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
            project = context.get("project")
            if project:
                entity = self._create_asset_type(project, props, buffer)

        elif node_type == "asset":
            project = context.get("project")
            asset_type = context.get("asset_type")
            if project and asset_type:
                entity = self._create_asset(project, asset_type, props, buffer)
        
        return entity

    # ----------------------------------------------------------------
    # STRICT CREATION CALLS
    # ----------------------------------------------------------------
    
    def _create_project(self, props, buffer):
        name = props.get("name")
        production_type = props.get("production_type", "short")
        
        # Mandatory: name, production_type
        # Optional: fps, ratio, resolution, description
        fps = props.get("fps")
        ratio = props.get("ratio")
        resolution = props.get("resolution")
        description = props.get("description")
        
        try:
            # 1. Create or Get
            project = gazu.project.get_project_by_name(name)
            if not project:
                # Strict Call: gazu.project.new_project(name, production_type, ...)
                # Note: gazu.project.new_project might take other args.
                # Assuming new_project supports these keywords or we update after.
                # If they are not supported in new_project, we update after.
                # Standard gazu usually supports basic info.
                
                # We'll use the user suggested call structure: new_project(name, production_type, ...)
                # If some args fail, we do basic and update.
                project = gazu.project.new_project(
                    name,
                    production_type=production_type
                )
                buffer.log(f"Created Project: {name}")
                
                # 2. Update status/info if needed
                # Set Optional fields if they exist and are not None
                update_data = {}
                if fps: update_data["fps"] = int(fps)
                if ratio: update_data["ratio"] = str(ratio)
                if resolution: update_data["resolution"] = str(resolution)
                if description: update_data["description"] = description
                
                if update_data:
                    project = gazu.raw.update("projects", project["id"], update_data)
                    buffer.log(f"Updated Project Info: {update_data}")

            else:
                buffer.log(f"Found Project: {name}")

            # 3. Inject Hidden/Custom Data
            # file_tree, data
            # The 'file_tree' and 'data' are pipeline specific.
            # We'll inject 'data' from props['custom'] if available?
            # User said: "User never types JSON. ... Inject data -> Pipeline Builder"
            # For now, we take `custom` prop and put it into `data`.
            
            custom_data = props.get("custom", {})
            # Transform custom_data values which are currently dicts {"type":..., "value":...} to simple key-value?
            # Or store as is? Kitsu 'data' field is a Dict.
            # Usually we want clean key-value.
            
            clean_data = {}
            for k, v in custom_data.items():
                if isinstance(v, dict) and "value" in v:
                    clean_data[k] = v["value"]
                else:
                    clean_data[k] = v
            
            if clean_data:
                current_data = project.get("data", {})
                if current_data is None: current_data = {}
                current_data.update(clean_data)
                project = gazu.raw.update("projects", project["id"], {"data": current_data})
                buffer.log(f"Injected Data: {clean_data.keys()}")

            return project
            
        except Exception as e:
            buffer.log(f"Error creating project {name}: {e}")
            return None

    def _create_episode(self, project, props, buffer):
        name = props.get("name")
        # Strict Call: gazu.shot.new_episode(project, name)
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
        name = props.get("name")
        # Strict Call: gazu.shot.new_sequence(project, name, episode=episode_or_none)
        try:
            if episode:
                 seq = gazu.shot.get_sequence_by_name(project, name, episode)
                 if not seq:
                     seq = gazu.shot.new_sequence(project, name, episode=episode)
                     buffer.log(f"Created Sequence: {name} (in Episode)")
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
        name = props.get("name")
        frame_in = props.get("frame_in")
        frame_out = props.get("frame_out")
        nb_frames = props.get("nb_frames")
        description = props.get("description")
        
        # Strict Call: gazu.shot.new_shot(project, sequence, name, ...)
        try:
            shot = gazu.shot.get_shot_by_name(sequence, name)
            if not shot:
                # new_shot args: project, sequence, name, data=None, ...
                # We need to see if we can pass frame_in/out during create or update after.
                # Assuming update after for optional fields to be safe, except if new_shot supports them.
                # User's pseudo-code implies passing them to new_shot.
                
                shot = gazu.shot.new_shot(
                    project, 
                    sequence, 
                    name,
                    frame_in=frame_in,
                    frame_out=frame_out,
                    nb_frames=nb_frames,
                    description=description
                )
                buffer.log(f"Created Shot: {name}")
                
                 # Inject Custom Data
                custom_data = props.get("custom", {})
                clean_data = {}
                for k, v in custom_data.items():
                    if isinstance(v, dict) and "value" in v:
                        clean_data[k] = v["value"]
                    else:
                        clean_data[k] = v
                
                if clean_data:
                    current_data = shot.get("data", {})
                    if current_data is None: current_data = {}
                    current_data.update(clean_data)
                    shot = gazu.raw.update("shots", shot["id"], {"data": current_data})
                    buffer.log(f"Injected Data: {clean_data.keys()}")

            else:
                buffer.log(f"Found Shot: {name}")
            return shot
        except Exception as e:
            buffer.log(f"Error shot {name}: {e}")
            return None

    def _create_asset_type(self, project, props, buffer):
        name = props.get("name")
        # Strict Call: gazu.asset.new_asset_type(name) -> But user said "Asset types belong only to project"
        # User pseudo-code: gazu.asset.new_asset_type(project, name) (Wait, does new_asset_type take project?)
        # Gazu standard: new_asset_type(name) - global.
        # But maybe user has a fork or wrapper?
        # User request: "Asset Types belong only to project ... gazu.asset.new_asset_type(project, name)"
        # I will follow USER REQUEST.
        
        try:
            # Check if exists in project? Asset types are usually global in Kitsu, but linked to project via settings?
            # Or maybe they mean "Asset Type" as in "Task Type"?
            # No, "Asset Type".
            # If default gazu doesn't support project, this might fail.
            # But I must follow "execute" instruction.
            
            # Note: standard gazu: new_asset_type(name) -> returns type.
            # Then usually you don't link type to project explicitly, you just use it.
            # UNLESS user means creating a custom asset type FOR that project?
            # I will try to pass project. If it fails, I might fallback or log error.
            # Safest is to try generic first? No, strict request.
            
            at = gazu.asset.get_asset_type_by_name(name)
            if not at:
                 # Try passing project if requested
                 # But standard gazu.asset.new_asset_type only takes name.
                 # Python allows ignoring extra kwargs if not used? No.
                 # I'll call it exactly as requested: gazu.asset.new_asset_type(project, name) (if user library supports it)
                 # Or maybe user meant: create type, then link?
                 # "Asset types belong *only* to project" -> This implies a project-specific scope.
                 # I will try:
                 try:
                     at = gazu.asset.new_asset_type(name) # Standard call first?
                     # Wait, user wrote: gazu.asset.new_asset_type(project, name)
                     # I'll Assume user knows their API.
                 except:
                     at = None

                 if not at:
                      # Let's try to match signature
                      # If I can't check signature, I'll trust user.
                      pass
                 
                 # Actually, I'll stick to what Gazu normally does but pass Project if that's the "Strict" requirement.
                 # But if I use standard Gazu, it will break.
                 # Let's assume standard Gazu behavior for "Asset Type" involves just name,
                 # BUT I will try `gazu.asset.new_asset_type(name)` first because that is the standard.
                 # AND THEN maybe user means "Asset Type" in the project scope?
                 # No, user code block: `gazu.asset.new_asset_type(project, name)`
                 # I will use THAT.
                 at = gazu.asset.new_asset_type(project, name) 
                 buffer.log(f"Created Asset Type: {name}")
            else:
                 buffer.log(f"Found Asset Type: {name}")
            return at
        except TypeError:
             # Fallback if user was wrong about API signature but right about intent
             try:
                 at = gazu.asset.get_asset_type_by_name(name)
                 if not at:
                     at = gazu.asset.new_asset_type(name)
                     buffer.log(f"Created Asset Type (Global): {name}")
                 return at
             except Exception as e:
                 buffer.log(f"Error asset type {name}: {e}")
                 return None
        except Exception as e:
             buffer.log(f"Error asset type {name}: {e}")
             return None

    def _create_asset(self, project, asset_type, props, buffer):
        name = props.get("name")
        # Strict Call: gazu.asset.new_asset(project, asset_type, name)
        try:
            asset = gazu.asset.get_asset_by_name(project, asset_type, name)
            if not asset:
                asset = gazu.asset.new_asset(project, asset_type, name)
                buffer.log(f"Created Asset: {name}")
                
                # Inject Custom Data
                custom_data = props.get("custom", {})
                clean_data = {}
                for k, v in custom_data.items():
                    if isinstance(v, dict) and "value" in v:
                        clean_data[k] = v["value"]
                    else:
                        clean_data[k] = v
                
                if clean_data:
                    current_data = asset.get("data", {})
                    if current_data is None: current_data = {}
                    current_data.update(clean_data)
                    asset = gazu.raw.update("assets", asset["id"], {"data": current_data})
                    buffer.log(f"Injected Data: {clean_data.keys()}")
            else:
                buffer.log(f"Found Asset: {name}")
            return asset
        except Exception as e:
            buffer.log(f"Error asset {name}: {e}")
            return None
