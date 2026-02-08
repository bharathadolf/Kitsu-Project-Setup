import gazu
import json
from ..entities.project import get_or_create_project
from ..entities.episode import get_or_create_episode
from ..entities.sequence import get_or_create_sequence
from ..entities.shot import get_or_create_shot
from ..entities.asset import get_or_create_asset, get_or_create_asset_type
from ..entities.task import get_or_create_task, get_or_create_task_type
from ..kitsu_config import KITSU_HOST, KITSU_EMAIL, KITSU_PASSWORD
from ..utils import code_gen

from ..ui.dialogs import GenerationSummaryDialog
from ..utils.compat import QApplication

class ProjectManager:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback if log_callback else print
        self.connected = False

    def log(self, message, level="INFO"):
        self.log_callback(message, level)
        
    def log_section(self, title):
        self.log(f"========================================", "INFO")
        self.log(f" {title.upper()}", "INFO")
        self.log(f"========================================", "INFO")

    def connect(self):
        self.log(f"Connecting to Kitsu ({KITSU_HOST})...", "INFO")
        try:
            gazu.set_host(KITSU_HOST)
            gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
            self.log(f"✅ Connected to Kitsu", "SUCCESS")
            self.connected = True
            return True
        except Exception as e:
            self.log(f"❌ Connection Failed: {e}", "ERROR")
            return False

    def _get_node_widget(self, tree_widget, item):
        return tree_widget.itemWidget(item, 0)

    def process_node(self, item, tree_widget, hierarchy=True):
        """
        Orchestrator for the Generate Workflow:
        1. Connect
        2. Build Plan (Traverse & Resolve Params)
        3. Confirm (UI)
        4. Execute
        5. Verify
        """
        self.log("--- GENERATE INITIATED ---", "INFO")
        mode = "Hierarchy" if hierarchy else "Selected Only"
        self.log(f"Mode: {mode}", "INFO")

        if not self.connected:
            if not self.connect(): return
            
        # --- Step 1: Build Plan ---
        self.log("Analyzing structure...", "INFO")
        plan = self.build_plan(item, tree_widget, hierarchy)
        
        if not plan:
            self.log("No valid entities found to generate.", "WARNING")
            return

        # --- Step 2: Confirmation UI ---
        dialog = GenerationSummaryDialog(plan, manager=self)
        if dialog.exec_():
             pass
        else:
            self.log("Operation Cancelled or Completed via Dialog.", "WARNING")

    def fetch_entity_data(self, plan):
        """
        Queries Kitsu for the entities in the plan and updates step['fetched_data'].
        """
        self.log_section("🌍 Fetching Live Data")
        
        for step in plan:
            node_type = step['type']
            name = step['name']
            
            try:
                entity = None
                
                # Priority 1: Use ID from just-executed creation
                created = step.get('created_entity')
                existing_data = step.get('fetched_data')
                
                target_id = None
                if created:
                    target_id = created.get('id')
                    self.log(f"   [DEBUG] Found 'created_entity' for {name}. ID: {target_id}", "DEBUG")
                elif existing_data:
                    target_id = existing_data.get('id')
                
                if target_id:
                     self.log(f"   [DEBUG] Fetching {node_type} {name} via ID {target_id}...", "DEBUG")
                     if node_type == "project": entity = gazu.project.get_project(target_id)
                     elif node_type == "episode": entity = gazu.shot.get_episode(target_id)
                     elif node_type == "sequence": entity = gazu.shot.get_sequence(target_id)
                     elif node_type == "shot": entity = gazu.shot.get_shot(target_id)
                     elif node_type == "asset": entity = gazu.asset.get_asset(target_id)
                     elif node_type == "asset_type": entity = gazu.asset.get_asset_type(target_id)
                     elif node_type == "task": entity = gazu.task.get_task(target_id)
                     
                else:
                    self.log(f"   [DEBUG] No ID for {name}. Fallback to Name lookup.", "DEBUG")
                    # Fallback to Name-based lookup if ID missing
                    if node_type == "project":
                        entity = gazu.project.get_project_by_name(name)
                        
                    elif node_type == "episode":
                        project = self._find_project_in_plan(plan)
                        if project:
                            proj_entity = gazu.project.get_project_by_name(project['name'])
                            if proj_entity:
                                 entity = gazu.shot.get_episode_by_name(proj_entity, name)
                    
                    elif node_type == "sequence":
                         project_data = self._find_project_in_plan(plan)
                         if project_data:
                             proj_entity = gazu.project.get_project_by_name(project_data['name'])
                             if proj_entity:
                                 entity = gazu.shot.get_sequence_by_name(proj_entity, name)
    
                    elif node_type == "shot":
                         pass 
                
                if entity:
                     step['fetched_data'] = entity
                     self.log(f"   Refreshed: {name} (ID: {entity.get('id')})", "SUCCESS")
                else:
                     self.log(f"   Could not fetch data for: {name}", "WARNING")
                
            except Exception as e:
                self.log(f"Fetch Error {name}: {e}", "ERROR")

    def _find_project_in_plan(self, plan):
        for step in plan:
            if step['type'] == 'project':
                return step['params'] if 'params' in step else None
        return None

    def build_plan(self, item, tree_widget, hierarchy=True):
        """
        Traverses the UI tree (or selected item) to build a linear execution plan.
        Resolves parameters and generates CODES.
        """
        plan = []
        
        # 1. Initialize Context & Counters
        context = {
            "counters": {
                "episode": 0,
                "sequence": 0, 
                "shot": 0 # Resets per sequence
            },
            "existing": {
                "episodes": [],
                "sequences": [],
                "shots": [] 
            },
            "parent_code": None, # Code of the parent entity
            "parent_type": None
        }

        # 2. Try to Pre-fetch Existing Data (Best Effort)
        project_name = None
        widget = self._get_node_widget(tree_widget, item)
        if widget and widget.node_frame.node_type == "project":
            project_name = widget.node_frame.properties.get("name")
            
        if self.connected and project_name:
            try:
                proj = gazu.project.get_project_by_name(project_name)
                if proj:
                     self.log(f"Fetching existing codes for {project_name}...", "INFO")
                     eps = gazu.shot.all_episodes_for_project(proj)
                     context["existing"]["episodes"] = [e["code"] for e in eps if e.get("code")]
                     
                     seqs = gazu.shot.all_sequences_for_project(proj)
                     context["existing"]["sequences"] = [s["code"] for s in seqs if s.get("code")]
            except Exception as e:
                self.log(f"Failed to fetch context: {e}", "WARNING")

        # 3. Process Root
        step = self._prepare_step(item, tree_widget, "Context" if hierarchy else "Selected", context)
        if step:
            plan.append(step)
            # Update context for children if root resolved a code
            root_code = step['params'].get('code')
            root_type = step['type']
            
            # Pass new context to children
            child_context = context.copy()
            child_context['counters'] = context['counters'].copy() # shallow copy dict
            child_context['parent_code'] = root_code
            child_context['parent_type'] = root_type
            
            # Extract root data params (e.g. project_path)
            root_data = step['params'].get('data', {})
            if root_type == "project":
                child_context['project_path'] = root_data.get('project_path')
                child_context['project_code'] = root_data.get('project_code')
                child_context['production_type'] = root_data.get('production_type', 'short')
            
            if hierarchy:
                self._collect_children(item, tree_widget, plan, child_context)
        
        return plan

    def _collect_children(self, parent_item, tree_widget, plan, context):
        count = parent_item.childCount()
        for i in range(count):
            child = parent_item.child(i)
            
            # Prepare Step
            step = self._prepare_step(child, tree_widget, "Child", context)
            if step:
                plan.append(step)
                
                # Update Context for traversing DEEPER (Metadata for grandchild)
                branch_context = context.copy()
                branch_context['counters'] = context['counters'].copy() 
                
                current_type = step['type']
                current_code = step['params'].get('code')
                
                branch_context['parent_code'] = current_code
                branch_context['parent_type'] = current_type
                
                # Extract paths from the generated data to pass down
                data_params = step['params'].get('data', {})
                if current_type == "project":
                    branch_context['project_path'] = data_params.get('project_path')
                    branch_context['project_code'] = data_params.get('project_code')
                elif current_type == "episode":
                    branch_context['episode_path'] = data_params.get('episode_path')
                    branch_context['episode_code'] = data_params.get('episode_code')
                elif current_type == "sequence":
                    branch_context['sequence_path'] = data_params.get('sequence_path')
                    branch_context['sequence_code'] = data_params.get('sequence_code')
                elif current_type == "asset_type":
                     # Special logic to calculate Asset Type Path if not in data
                     proj_path = context.get('project_path', "")
                     at_name = step['name'].lower().replace(" ", "")
                     if proj_path:
                         branch_context['asset_type_path'] = f"{proj_path}/assets/{at_name}"
                     branch_context['asset_type_name'] = at_name
                
                # If we just entered a Sequence, reset shot counter in the branch context
                if current_type == "sequence":
                     branch_context['counters']['shot'] = 0
                
                self._collect_children(child, tree_widget, plan, branch_context)

    def _prepare_step(self, item, tree_widget, role, context):
        widget = self._get_node_widget(tree_widget, item)
        if not widget: return None
        
        node_type = widget.node_frame.node_type
        props = widget.node_frame.properties
        name = props.get("name", "Unknown")
        
        # Calculate Params (Injecting Context)
        params = self._resolve_params(node_type, props, context)
        
        return {
            "type": node_type,
            "name": name,
            "params": params,
            "role": role,
            "widget": widget
        }

    def _resolve_params(self, node_type, props, context):
        """
        Extracts params from UI props and Auto-Generates Codes -> AND Data Parameters.
        """
        name = props.get("name", "Unknown")
        existing_codes = context.get('existing', {})
        counters = context.get('counters', {})
        
        # Context Paths
        project_path = context.get('project_path', "")
        project_code = context.get('project_code', "")
        episode_path = context.get('episode_path', "")
        episode_code = context.get('episode_code', "")
        sequence_path = context.get('sequence_path', "")
        sequence_code = context.get('sequence_code', "")
        asset_type_path = context.get('asset_type_path', "")
        
        production_type = context.get('production_type', "short")
        parent_type = context.get('parent_type')
        
        # Initialize Base Params with Name
        params = {"name": name}
        
        # Log start
        self.log(f"Resolving params for {node_type}: {name}", "DEBUG")
        
        # --- AUTO-CODE GENERATION & DATA INJECTION ---
        code = None
        data = {}
        
        if node_type == "project":
            code = code_gen.generate_project_code(name)
            prod_type = props.get("production_type", "short")
            root_path = props.get("root_path", "E:/Termina")
            
            project_code_data = code.lower()
            proj_path_val = f"{root_path}/{project_code_data}".replace("\\", "/")
            
            proj_tree = self._get_project_tree_schema(prod_type)
            
            data = {
                "root_path": root_path,
                "project_code": project_code_data,
                "project_path": proj_path_val,
                "production_type": prod_type,
                "project_tree": proj_tree,
                "RV_MAP": {
                    project_code_data: proj_path_val
                }
            }
            
            params.update({
                "production_type": prod_type,
                "production_style": props.get("production_style", "2d3d"),
                "description": props.get("description"),
                "code": code,
                "data": data, # Inject Data
                "file_tree": props.get("file_tree")
            })
            
            for k in ["fps", "ratio", "resolution", "start_date", "end_date"]:
                if props.get(f"use_{k}"): params[k] = props.get(k)
                elif props.get(k): params[k] = props.get(k)
            
            return params
            
        elif node_type == "episode":
            count = counters["episode"]
            code = code_gen.generate_incremental_code("ep", existing_codes.get("episodes", []), count)
            counters["episode"] += 1 
            
            ep_code_data = name.lower()
            ep_path_val = f"{project_path}/{ep_code_data}".replace("\\", "/") if project_path else ""
            
            data = {
                "project_code": project_code,
                "project_path": project_path,
                "parent_type": "project",
                "episode_code": ep_code_data,
                "episode_name": name,
                "episode_path": ep_path_val,
                "episode_tree": {
                    "{sequence}": {
                        "{shot}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                },
                "RV_MAP": {
                    ep_code_data: ep_path_val
                }
            }
            
            return {
                "name": name, 
                "code": code, 
                "description": f"{name} and {code}",
                "project": "<Context.Project>",
                "data": data
            }
            
        elif node_type == "sequence":
            count = counters["sequence"]
            code = code_gen.generate_incremental_code("seq", existing_codes.get("sequences", []), count)
            counters["sequence"] += 1
            
            eff_parent_path = episode_path if episode_path else project_path
            eff_parent_type = "episode" if episode_path else "project"
            eff_parent_code = episode_code if episode_code else project_code
            
            seq_code_data = name.lower()
            
            if eff_parent_type == "project" and production_type == "film":
                 seq_path_val = f"{eff_parent_path}/film/{seq_code_data}".replace("\\", "/")
            else:
                 seq_path_val = f"{eff_parent_path}/{seq_code_data}".replace("\\", "/")
            
            data = {
                "project_code": project_code,
                "project_path": project_path,
                "parent_code": eff_parent_code,
                "parent_path": eff_parent_path,
                "parent_type": eff_parent_type,
                "sequence_code": seq_code_data,
                "sequence_name": name,
                "sequence_path": seq_path_val,
                "sequence_tree": {
                    "{shot}": {
                        "{task_type}": { "work": {}, "publish": {} }
                    }
                },
                "RV_MAP": {
                    seq_code_data: seq_path_val
                }
            }
            
            return {
                "name": name, 
                "code": code, 
                "description": f"{name} and {code}",
                "project": "<Context.Project>", 
                "episode": "<Context.Episode>",
                "data": data
            }
            
        elif node_type == "shot":
            if sequence_code:
                seq_code_ref = sequence_code
            else:
                seq_code_ref = "seqXX" 
                
            count = counters["shot"]
            code = code_gen.generate_shot_code(seq_code_ref, count + 1)
            counters["shot"] += 1
            
            shot_code_data = name.lower()
            shot_path_val = f"{sequence_path}/{shot_code_data}".replace("\\", "/") if sequence_path else ""
            
            data = {
                "project_code": project_code,
                "project_path": project_path,
                "sequence_code": seq_code_ref,
                "sequence_path": sequence_path,
                "parent_type": "sequence",
                "shot_code": shot_code_data,
                "shot_name": name,
                "shot_path": shot_path_val,
                "shot_tree": {
                    "{task_type}": { "work": {}, "publish": {} }
                },
                "RV_MAP": {
                    shot_code_data: shot_path_val
                }
            }
            
            return {
                "name": name,
                "code": code,
                "project": "<Context.Project>",
                "sequence": "<Context.Sequence>",
                "frame_in": props.get("frame_in"),
                "frame_out": props.get("frame_out"),
                "nb_frames": props.get("nb_frames"),
                "description": f"{name} and {code}",
                "tasks": ["Compositing"],
                "data": data
            }
            
        elif node_type == "asset_type":
             return {"name": name}
             
        elif node_type == "asset":
             at_name = context.get('asset_type_name', "asset")
             code = code_gen.generate_asset_code(at_name, name) 
             
             asset_code_data = name.lower()
             asset_path_val = f"{asset_type_path}/{asset_code_data}".replace("\\", "/") if asset_type_path else ""
             
             data = {
                "project_code": project_code,
                "project_path": project_path,
                "asset_type": at_name,
                "asset_type_path": asset_type_path,
                "parent_type": "asset_type",
                "asset_code": asset_code_data,
                "asset_name": name,
                "asset_path": asset_path_val,
                "asset_tree": {
                    "{task_type}": { "work": {}, "publish": {} }
                },
                "RV_MAP": {
                    asset_code_data: asset_path_val
                }
             }

             return {
                 "name": name,
                 "code": code,
                 "project": "<Context.Project>",
                 "asset_type": "<Context.AssetType>",
                 "description": f"{name} and {code}",
                 "data": data
             }
             
        return params

    def _get_project_tree_schema(self, prod_type):
        """Helper to return the project tree dict based on type."""
        base_shared = {
            "shared": { "lut": {}, "docs": {}, "reference": {} }
        }
        
        if prod_type == "film":
            tree = {
                "film": {
                    "{sequence}": {
                        "{shot}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                },
                "assets": {
                    "{asset_type}": {
                        "{asset_name}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                }
            }
        elif prod_type == "tv":
            tree = {
                "{episode}": {
                    "{sequence}": {
                        "{shot}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                },
                "assets": {
                    "{asset_type}": {
                        "{asset_name}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                }
            }
        elif prod_type == "shots_only":
            tree = {
                "shots": {
                    "{shot}": {
                        "{task_type}": { "work": {}, "publish": {} }
                    }
                }
            }
        elif prod_type == "assets_only":
            tree = {
                "assets": {
                    "{asset_type}": {
                        "{asset_name}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                }
            }
        else: # Custom or fallback
            tree = {
                "{episode}": {
                    "{sequence}": {
                        "{shot}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                },
                "film": {
                    "{sequence}": {
                        "{shot}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                },
                "assets": {
                    "{asset_type}": {
                        "{asset_name}": {
                            "{task_type}": { "work": {}, "publish": {} }
                        }
                    }
                }
            }
            
        tree.update(base_shared)
        return tree

    def sanity_check_project(self, name):
        """Pre-flight check to prevent failures."""
        if not self.connected:
            if not self.connect():
                return False, "Could not connect to Kitsu."
        
        try:
            existing = gazu.project.get_project_by_name(name)
            if existing:
                return False, f"Project '{name}' already exists in Kitsu."
        except Exception as e:
            return False, f"Gazu Error during check: {e}"
            
        return True, "Sanity Check Passed"

    def execute_plan(self, plan):
        self.log_section("🚀 Executing Plan")
        
        if not plan:
            self.log("Empty Plan", "WARNING")
            return
            
        project_step = plan[0]
        if project_step['type'] != 'project':
            self.log("Plan invalid: First item must be Project.", "ERROR")
            return
            
        # --- PHASE 1: PROJECT ---
        try:
            self.log(f"--- PHASE 1: PROJECT ---", "INFO")
            proj_name = project_step['name']
            proj_params = project_step['params']
            
            # 1. Create/Get
            self.log(f"Creating Project '{proj_name}'...", "INFO")
            project = gazu.project.get_project_by_name(proj_name)
            if not project:
                project = gazu.project.new_project(
                    name=proj_name,
                    production_type=proj_params.get('production_type', 'short'),
                    production_style=proj_params.get('production_style', 'vfx')
                )
            
            # 2. Update Code/Desc
            self.log("Updating Project Code & Description...", "INFO")
            updated = False
            if proj_params.get('code'):
                project['code'] = proj_params['code']
                updated = True
            if proj_params.get('description'):
                project['description'] = proj_params['description']
                updated = True
            if updated:
                gazu.project.update_project(project)
                
            # 3. Meta Data
            if proj_params.get('data'):
                self.log("Injecting Project Data...", "INFO")
                gazu.project.update_project_data(project, data=proj_params['data'])
                # Update local ref
                project['data'] = proj_params['data']

            # 4. Link Asset/Task Types
            self.log("Linking Asset Types & Task Types...", "INFO")
            defaults_ats = ["Character", "Prop", "Environment"]
            defaults_tts = ["Modeling", "Rigging", "Lookdev", "Lighting", "Compositing"]
            
            final_ats = []
            for name in defaults_ats:
                at = gazu.asset.get_asset_type_by_name(name)
                if not at: at = gazu.asset.new_asset_type(name)
                final_ats.append(at)
            
            final_tts = []
            for name in defaults_tts:
                tt = gazu.task.get_task_type_by_name(name)
                if not tt: tt = gazu.task.new_task_type(name)
                final_tts.append(tt)
            
            project["asset_types"] = final_ats
            project["task_types"] = final_tts
            gazu.project.update_project(project)
            
            self.log(f"✅ Project '{proj_name}' Configured.", "SUCCESS")
            
            project_step['created_entity'] = project
            if len(plan) == 1: return 
            
        except Exception as e:
            self.log(f"❌ Project Creation Failed: {e}", "ERROR")
            raise e 

        # --- PHASE 2: HIERARCHY ---
        self.log(f"--- PHASE 2: HIERARCHY ---", "INFO")
        
        entity_cache = { ("project", proj_name): project }
        success_count = 0
        
        for step in plan[1:]:
            try:
                node_type = step['type']
                name = step['name']
                params = step['params']
                
                self.log(f"Processing {node_type}: {name}...", "INFO")
                created_entity = None
                
                if node_type == "episode":
                    # Mandatory: Project, Name
                    ep_name_val = params.get('code', name).upper()
                    if not ep_name_val: ep_name_val = name
                    
                    created_entity = gazu.shot.new_episode(
                        project=project,
                        name=ep_name_val
                    )
                    
                    if params.get('code') or params.get('description'):
                        if params.get('code'): created_entity['code'] = params.get('code')
                        if params.get('description'): created_entity['description'] = params.get('description')
                        gazu.shot.update_episode(created_entity)
                    
                    if params.get('data'):
                         gazu.shot.update_episode_data(created_entity, data=params['data'])
                         created_entity['data'] = params['data']
                         
                    entity_cache[("episode", name)] = created_entity
                    
                elif node_type == "sequence":
                    # Find Parent Episode (Scan backwards in plan)
                    idx = plan.index(step)
                    parent_ep_obj = None
                    if project.get('production_type') == 'tv_show':
                        for i in range(idx-1, -1, -1):
                            if plan[i]['type'] == 'episode':
                                parent_ep_obj = plan[i].get('created_entity')
                                break
                    
                    created_entity = gazu.shot.new_sequence(
                        project=project,
                        name=name,
                        episode=parent_ep_obj
                    )
                    
                    if params.get('code') or params.get('description'):
                        if params.get('code'): created_entity['code'] = params.get('code')
                        if params.get('description'): created_entity['description'] = params.get('description')
                        gazu.shot.update_sequence(created_entity)
                    
                    if params.get('data'):
                        gazu.shot.update_sequence_data(created_entity, data=params['data'])
                        
                    entity_cache[("sequence", name)] = created_entity

                elif node_type == "shot":
                    # Find Parent Sequence (Scan backwards)
                    idx = plan.index(step)
                    parent_seq_obj = None
                    for i in range(idx-1, -1, -1):
                        if plan[i]['type'] == 'sequence':
                            parent_seq_obj = plan[i].get('created_entity')
                            break
                    
                    if parent_seq_obj:
                        created_entity = gazu.shot.new_shot(
                            project=project,
                            sequence=parent_seq_obj,
                            name=name,
                            frame_in=params.get("frame_in"),
                            frame_out=params.get("frame_out"),
                            nb_frames=params.get("nb_frames")
                        )
                        
                        if params.get('code') or params.get('description'):
                            if params.get('code'): created_entity['code'] = params.get('code')
                            if params.get('description'): created_entity['description'] = params.get('description')
                            gazu.shot.update_shot(created_entity)
                        
                        if params.get('data'):
                             gazu.shot.update_shot_data(created_entity, data=params['data'])
                    else:
                        self.log(f"⚠️ Skipping Shot '{name}': No Parent Sequence.", "WARNING")

                elif node_type == "asset_type":
                     at = gazu.asset.get_asset_type_by_name(name)
                     if not at: at = gazu.asset.new_asset_type(name)
                     entity_cache[("asset_type", name)] = at
                     created_entity = at
                     
                elif node_type == "asset":
                     at_name = params.get('data', {}).get('asset_type')
                     at_obj = None
                     if at_name:
                         at_obj = entity_cache.get(("asset_type", at_name))
                         if not at_obj: list(filter(lambda x: x['type'] == 'asset_type' and x['name'] == at_name, plan))
                         # Fallback to fetch
                         if not at_obj: at_obj = gazu.asset.get_asset_type_by_name(at_name)
                     
                     if not at_obj:
                         idx = plan.index(step)
                         for i in range(idx-1, -1, -1):
                             if plan[i]['type'] == 'asset_type':
                                 at_obj = plan[i].get('created_entity')
                                 break
                     
                     if at_obj:
                         created_entity = gazu.asset.new_asset(
                             project=project,
                             asset_type=at_obj,
                             name=name 
                         )
                         
                         if params.get('code') or params.get('description'):
                            if params.get('code'): created_entity['code'] = params.get('code')
                            if params.get('description'): created_entity['description'] = params.get('description')
                            gazu.asset.update_asset(created_entity)

                         if params.get('data'):
                             gazu.asset.update_asset_data(created_entity, data=params['data'])
                             created_entity['data'] = params['data']
                             
                         entity_cache[("asset", name)] = created_entity

                     else:
                          self.log(f"⚠️ Skipping Asset '{name}': No Asset Type.", "WARNING")
                
                if created_entity:
                     step['created_entity'] = created_entity
                     self.log(f"   Created {node_type}: {name}", "SUCCESS")
                     success_count += 1
                     
            except Exception as e:
                self.log(f"Failed {node_type} {name}: {e}", "ERROR")

        self.log_section("🏁 Execution Finished")
        self.log(f"Processed {len(plan)} items. Success: {success_count}.", "INFO")
        
        if proj_name:
            self.verify_project_data(proj_name)
            return True
        return False

    def verify_project_data(self, project_name):
        self.log_section("🔍 Post-Creation Verification")
        try:
            project = gazu.project.get_project_by_name(project_name)
            if not project:
                self.log(f"❌ CRITICAL: Could not find project '{project_name}' in Kitsu!", "ERROR")
                return

            self.log(f"✅ PROJECT FOUND: {project['name']} (ID: {project['id']})", "SUCCESS")
            self.log(f"   Type: {project.get('production_type')} | Style: {project.get('production_style')}", "INFO")
            
            data_fields = ['resolution', 'fps', 'ratio', 'start_date', 'end_date']
            data_summary = {k: project.get(k) or project.get('data', {}).get(k) for k in data_fields}
            self.log(f"   Parameters: {json.dumps(data_summary)}", "INFO")

            sequences = gazu.shot.all_sequences_for_project(project)
            self.log(f"\n📂 SEQUENCES FOUND: {len(sequences)}", "INFO")
            
            for seq in sequences:
                self.log(f"   ► Sequence: {seq.get('name')}", "INFO")
                shots = gazu.shot.all_shots_for_sequence(seq)
                if shots:
                    self.log(f"     └── Shots ({len(shots)}):", "INFO")
                    for shot in shots:
                        fr_in = shot.get('data', {}).get('frame_in', '-')
                        fr_out = shot.get('data', {}).get('frame_out', '-')
                        self.log(f"         • {shot.get('name')} [Frames: {fr_in}-{fr_out}]", "INFO")
        
        except Exception as e:
            self.log(f"❌ Verification Failed: {e}", "ERROR")
