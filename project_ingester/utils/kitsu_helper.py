import os
import glob
from pprint import pformat
import json

try:
    import gazu
except ImportError:
    gazu = None

from ..kitsu_config import KITSU_HOST, KITSU_EMAIL, KITSU_PASSWORD

# Helper to capture log like output
class LogBuffer:
    def __init__(self):
        self.logs = []
    
    def log(self, message):
        self.logs.append(message)
    
    def section(self, title):
        self.logs.append("\n" + title)
        self.logs.append("-" * len(title))
    
    def field(self, label, value):
        self.logs.append(f"{label:<20}: {value} ({type(value).__name__})")

    def get_output(self):
        return "\n".join(self.logs)

class KitsuGenerator:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback if log_callback else print
        self.connected = False
        
    def _log(self, msg, level="INFO"):
        # We can implement level handling or just pass string
        # For this tool, we'll try to mimic the user's requested output style within the generator
        # But we also need to emit signals to the UI console.
        self.log_callback(msg, level)

    def connect(self):
        if not gazu:
            self._log("Gazu module not found. Cannot connect to Kitsu.", "ERROR")
            return False
        
        try:
            gazu.set_host(KITSU_HOST)
            gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
            self._log(f"✅ Login successful to {KITSU_HOST}", "SUCCESS")
            self.connected = True
            return True
        except Exception as e:
            self._log(f"Failed to login to Kitsu: {e}", "ERROR")
            return False

    def process_node(self, item, tree_widget, hierarchy=True):
        if not self.connected:
            if not self.connect():
                return
        
        # Resolve context by walking up the tree
        path_items = []
        curr = item
        while curr:
            path_items.insert(0, curr)
            curr = curr.parent()
        
        context = {} 
        
        for i, ancestor_item in enumerate(path_items):
            # We treat every ancestor as something to be verified/created in order
            
            node_widget = tree_widget.itemWidget(ancestor_item, 0)
            if not node_widget: continue
            
            props = node_widget.node_frame.properties
            node_type = node_widget.node_frame.node_type
            
            buffer = LogBuffer()
            entity = self._ensure_entity(node_type, props, context, buffer)
            
            if buffer.logs:
                self._log(buffer.get_output(), "INFO")

            if not entity:
                self._log(f"Failed to resolve/create {node_type}: {props.get('name')}", "ERROR")
                return
            
            # Store ID in context
            if node_type == "project":
                context["project"] = entity
                context["project_id"] = entity["id"]
            elif node_type == "episode":
                context["episode"] = entity
                context["episode_id"] = entity["id"]
            elif node_type == "sequence":
                context["sequence"] = entity
                context["sequence_id"] = entity["id"]
            elif node_type == "shot":
                context["shot"] = entity
                context["shot_id"] = entity["id"]
            elif node_type == "asset_type":
                context["asset_type"] = entity
                context["asset_type_id"] = entity["id"]
            
        
        # If hierarchy=True, we process children recursively
        if hierarchy:
            self._process_children(item, tree_widget, context)
            
        self._log("✅ Done", "SUCCESS")

    def _process_children(self, parent_item, tree_widget, context):
        count = parent_item.childCount()
        for i in range(count):
            child_item = parent_item.child(i)
            buffer = LogBuffer()
            
            node_widget = tree_widget.itemWidget(child_item, 0)
            if not node_widget: continue
            
            props = node_widget.node_frame.properties
            node_type = node_widget.node_frame.node_type
            
            entity = self._ensure_entity(node_type, props, context, buffer)
            
            if buffer.logs:
                self._log(buffer.get_output(), "INFO")
            
            if entity:
                # Create new context for this branch
                child_context = context.copy()
                if node_type == "episode":
                    child_context["episode"] = entity
                    child_context["episode_id"] = entity["id"]
                elif node_type == "sequence":
                    child_context["sequence"] = entity
                    child_context["sequence_id"] = entity["id"]
                elif node_type == "asset_type":
                    child_context["asset_type"] = entity
                    child_context["asset_type_id"] = entity["id"]
                
                # Recurse
                self._process_children(child_item, tree_widget, child_context)
            else:
                self._log(f"Failed child {node_type}", "ERROR")


    def _ensure_entity(self, node_type, props, context, buffer):
        entity = None
        
        if node_type == "project":
            entity = self._create_project(props, buffer)
            
        elif node_type == "episode":
            project = context.get("project")
            if project:
                entity = self._create_episode(project, props, buffer)
                
        elif node_type == "sequence":
            project = context.get("project")
            episode = context.get("episode") # Can be None
            if project:
                entity = self._create_sequence(project, episode, props, buffer)

        elif node_type == "shot":
            project = context.get("project")
            sequence = context.get("sequence")
            if project and sequence:
                entity = self._create_shot(project, sequence, props, buffer)

        elif node_type == "asset_type":
            # Asset type is usually global but we can get/create
            entity = self._create_asset_type(props, buffer)

        elif node_type == "asset":
            project = context.get("project")
            asset_type = context.get("asset_type")
            if project and asset_type:
                entity = self._create_asset(project, asset_type, props, buffer)
        
        return entity

    # ----------------------------------------------------------------
    # SPECIFIC CREATORS
    # ----------------------------------------------------------------
    
    def _create_project(self, props, buffer):
        name = props.get("name")
        prod_type = props.get("production_type", "short")
        # style is not standard in props unless custom stored?
        # User script has PRODUCTION_STYLE.
        # In tree.py properties: production_style is NOT default, but user script adds it to data.
        # But wait, tree.py project defaults: production_type, status, start_date, etc.
        # It doesn't have 'production_style' by default in line 25-33 of tree.py unless added.
        # But the USER SCRIPT output shows "Production Style : vfx".
        # So I will assume it might be in props or I should check.
        # checking tree.py again...
        # It is NOT in the default dict.
        # However, the user script says `pipeline_data` has it.
        # I'll check `props` for it, fallback to 'vfx' or '3d'.
        
        style = props.get("production_style", "vfx") # Defaulting
        
        # 1. Create Project
        # gazu.project.new_project provides name, resolution, fps, etc.
        # Arguments: name, production_type=None, ratio=None, resolution=None, fps=None, ...
        # Check if project exists first to be safe or just call new_project (idempotent?)
        # User script just calls new_project.
        
        try:
            # Check if exists to avoid error if gazu throws on duplicate
            project = gazu.project.get_project_by_name(name)
            if not project:
                project = gazu.project.new_project(name, production_type=prod_type)
                # gazu new_project args might differ by version, but name is first.
                # User used: name=PROJECT_NAME, production_type=PRODUCTION_TYPE, production_style=PRODUCTION_STYLE
                # Wait, does gazu accept production_style in new_project? 
                # User script:
                # project = gazu.project.new_project(
                #     name=PROJECT_NAME,
                #     production_type=PRODUCTION_TYPE,
                #     production_style=PRODUCTION_STYLE,
                # )
                # So I should pass it.
            else:
                 # Update validation?
                 pass

            if not project:
                 # Use kwargs from script
                 project = gazu.project.new_project(
                     name=name,
                     production_type=prod_type,
                     production_style=style
                 )
            
            buffer.section("Project Creation")
            buffer.field("Name", project["name"])
            buffer.field("ID", project["id"])

            # 2. Update Code
            code = props.get("code", "")
            if code:
                project = gazu.raw.update("projects", project["id"], {"code": code})
                buffer.field("Kitsu Code", project["code"])

            # 3. Attach Pipeline Data
            pipeline_data = project.get("data", {})
            if pipeline_data is None: pipeline_data = {} # Safety
            
            pipeline_info = {
                "project_code": code,
                "nas_path": props.get("root_path", ""),
                "production_type": prod_type,
                "production_style": style
            }
            pipeline_data["pipeline"] = pipeline_info
            
            project = gazu.raw.update("projects", project["id"], {"data": pipeline_data})
            buffer.field("Pipeline Data", project.get("data"))
            
            # 4. Basic Info
            buffer.section("Basic Project Info")
            buffer.field("Name", project.get("name"))
            buffer.field("ID", project.get("id"))
            buffer.field("Code", project.get("code"))
            buffer.field("Type", project.get("type"))
            buffer.field("Production Type", project.get("production_type"))
            buffer.field("Production Style", project.get("production_style"))
            
            return project
            
        except Exception as e:
            buffer.log(f"Error creating project {name}: {e}")
            return None

    def _create_episode(self, project, props, buffer):
        name = props.get("episode_name", props.get("name"))
        try:
            episode = gazu.shot.get_episode_by_name(project, name)
            if not episode:
                episode = gazu.shot.new_episode(project, name)
                buffer.log(f"Created Episode: {name}")
            else:
                buffer.log(f"Found Episode: {name}")
            return episode
        except Exception as e:
            buffer.log(f"Error episode {name}: {e}")
            return None

    def _create_sequence(self, project, episode, props, buffer):
        # Sequence name in tree.py is sequence_code usually? 
        # tree.py: "sequence_code": f"SEQ_...", "sequence_name": "New Sequence"
        # Gazu usually uses the name.
        name = props.get("sequence_code", props.get("name")) 
        try:
            # If episode is valid, seq should be linked to episode?
            # Gazu: gazu.shot.new_sequence(project, name, episode=None)
            if episode:
                 seq = gazu.shot.get_sequence_by_name(project, name, episode)
                 if not seq:
                     seq = gazu.shot.new_sequence(project, name, episode=episode)
                     buffer.log(f"Created Sequence: {name} in {episode['name']}")
                 else:
                     buffer.log(f"Found Sequence: {name}")
            else:
                 seq = gazu.shot.get_sequence_by_name(project, name)
                 if not seq:
                     seq = gazu.shot.new_sequence(project, name)
                     buffer.log(f"Created Sequence: {name}")
                 else:
                     buffer.log(f"Found Sequence: {name}")
            return seq
        except Exception as e:
            buffer.log(f"Error sequence {name}: {e}")
            return None

    def _create_shot(self, project, sequence, props, buffer):
        name = props.get("shot_code", props.get("name"))
        try:
            shot = gazu.shot.get_shot_by_name(sequence, name)
            if not shot:
                shot = gazu.shot.new_shot(project, sequence, name)
                buffer.log(f"Created Shot: {name}")
            else:
                buffer.log(f"Found Shot: {name}")
            return shot
        except Exception as e:
            buffer.log(f"Error shot {name}: {e}")
            return None

    def _create_asset_type(self, props, buffer):
        name = props.get("name") # e.g. "Characters"
        try:
            # Check if asset type exists
            at = gazu.asset.get_asset_type_by_name(name)
            if not at:
                at = gazu.asset.new_asset_type(name)
                buffer.log(f"Created Asset Type: {name}")
            else:
                buffer.log(f"Found Asset Type: {name}")
            return at
        except Exception as e:
             buffer.log(f"Error asset type {name}: {e}")
             return None

    def _create_asset(self, project, asset_type, props, buffer):
        name = props.get("asset_name", props.get("name"))
        try:
            asset = gazu.asset.get_asset_by_name(project, asset_type, name)
            if not asset:
                asset = gazu.asset.new_asset(project, asset_type, name)
                buffer.log(f"Created Asset: {name}")
            else:
                buffer.log(f"Found Asset: {name}")
            return asset
        except Exception as e:
            buffer.log(f"Error asset {name}: {e}")
            return None
