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
        # Must run on main thread. Assuming we are on main thread (which PySide usually is).
        # Include 'manager=self' so the dialog can trigger execution and query
        dialog = GenerationSummaryDialog(plan, manager=self)
        if dialog.exec_():
             # If user clicked "Generate" standard button (Accept), we execute here.
             # If they clicked "Generate & Query", the dialog likely handled execution internally
             # and then we might not need to do anything here, or we re-run?
             # Standard "Generate" works as before (Dialog returns Accepted).
             # "Generate & Query" might keep dialog open, or close it after. 
             # Let's assume standard behavior is preserved for "Generate", 
             # and "Generate & Query" does its own thing inside dialog but suppresses default accept until done?
             # For now, let's keep this as fallback if not handled inside.
             # But wait, if "Generate & Query" executed it, we shouldn't execute again.
             # We will check if plan was executed. 
             # Actually, simpler: Standard "Generate" closes dialog -> returns here -> execute.
             # "Generate & Query" -> calls manager -> updates UI -> User eventually clicks "Close" (Cancel) or we close.
             # If "Query" runs, we probably want to return Cancel or special code so we don't re-run.
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
            
            # Use 'params' name as the authoritative source (it might have been edited in UI)
            # The execution step would have used the edited name.
            
            try:
                entity = None
                
                if node_type == "project":
                    entity = gazu.project.get_project_by_name(name)
                    
                elif node_type == "episode":
                    # Need project context (which should be in params if we updated it during exec, 
                    # but context is separate. 
                    # Simpler is to use the context from execution if we stored it?
                    # The plan steps are independent dicts. 
                    # Execution logic maintains a 'context' dict.
                    # We need that context here to query efficiently, OR just search globally/by project if possible.
                    
                    # Episodes are unique by project.
                    # We can try to find the project from plan? Recursion?
                    # Let's assume project name is available in params or we search.
                    
                    # For now, let's try a best effort search or find parent project in plan.
                    project = self._find_project_in_plan(plan)
                    if project:
                        proj_entity = gazu.project.get_project_by_name(project['name'])
                        if proj_entity:
                             entity = gazu.shot.get_episode_by_name(proj_entity, name)
                
                elif node_type == "sequence":
                     project = self._find_project_in_plan(plan)
                     if project:
                         proj_entity = gazu.project.get_project_by_name(project['name'])
                         if proj_entity:
                             # Try to get sequence directly from project
                             entity = gazu.shot.get_sequence_by_name(proj_entity, name)

                elif node_type == "shot":
                     # To find a shot, we technically need project + sequence.
                     # But gazu.shot.get_shot_by_name might allow searching or we iterate.
                     # Actually, gazu usually needs sequence.
                     pass 
                     # This implementation might be tricky without fuller context preservation.
                     # ALTERNATIVE: During 'execute_plan', we can SAVE the result entity into the plan!
                     # That is much smarter. Update execute_plan to save entity to step.
            
            except Exception as e:
                self.log(f"Fetch Error {name}: {e}", "ERROR")

    def _find_project_in_plan(self, plan):
        for step in plan:
            if step['type'] == 'project':
                return step
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
                "shots": [] # Tricky to cache all, maybe fetch per sequence? 
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
                # This blocks UI, but necessary for accurate codes
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
        Extracts params from UI props and Auto-Generates Codes.
        """
        name = props.get("name", "Unknown")
        existing_codes = context.get('existing', {})
        counters = context.get('counters', {})
        parent_code = context.get('parent_code')
        parent_type = context.get('parent_type')
        
        # Initialize Base Params with Name
        params = {"name": name}
        
        # --- AUTO-CODE GENERATION ---
        code = None
        
        if node_type == "project":
            code = code_gen.generate_project_code(name)
            params.update({
                "production_type": props.get("production_type", "short"),
                "production_style": props.get("production_style", "2d3d"),
                "description": props.get("description"),
                "code": code, # Injected Code
                "data": props.get("data"),
                "file_tree": props.get("file_tree")
            })
            # Optional Params
            if props.get("use_fps"): params["fps"] = props.get("fps")
            if props.get("use_ratio"): params["ratio"] = props.get("ratio")
            if props.get("use_resolution"): params["resolution"] = props.get("resolution")
            if props.get("use_start_date"): params["start_date"] = props.get("start_date")
            if props.get("use_end_date"): params["end_date"] = props.get("end_date")
            
            return params
            
        elif node_type == "episode":
            # ep{n:02}
            count = counters["episode"]
            code = code_gen.generate_incremental_code("ep", existing_codes.get("episodes", []), count)
            counters["episode"] += 1 # Increment global counter
            return {
                "name": name, 
                "code": code, 
                "description": f"{name} and {code}",
                "project": "<Context.Project>"
            }
            
        elif node_type == "sequence":
            # seq{n:02}
            count = counters["sequence"]
            code = code_gen.generate_incremental_code("seq", existing_codes.get("sequences", []), count)
            counters["sequence"] += 1
            return {
                "name": name, 
                "code": code, 
                "description": f"{name} and {code}",
                "project": "<Context.Project>", 
                "episode": "<Context.Episode>"
            }
            
        elif node_type == "shot":
            # {seq_code}_sh{n:02}
            # Need sequence code. If parent is Sequence, use parent_code.
            if parent_type == "sequence" and parent_code:
                seq_code = parent_code
            else:
                seq_code = "seqXX" # Fallback if hierarchy issue
                
            count = counters["shot"]
            code = code_gen.generate_shot_code(seq_code, count + 1) # shots start at 1
            counters["shot"] += 1
            
            return {
                "name": name,
                "code": code,
                "project": "<Context.Project>",
                "sequence": "<Context.Sequence>",
                "frame_in": props.get("frame_in"),
                "frame_out": props.get("frame_out"),
                "nb_frames": props.get("nb_frames"),
                "description": f"{name} and {code}",
                "tasks": ["Compositing"]
            }
            
        elif node_type == "asset_type":
             return {"name": name}
             
        elif node_type == "asset":
             # {asset_type}_{asset_name}
             # need asset type name.
             asset_type_name = "asset"
             # Try to find parent asset_type name if possible, or use fallback
             if parent_type == "asset_type":
                 pass 
             
             # Placeholder until context fixed or explicit type
             code = code_gen.generate_asset_code("character", name) 
             
             return {
                 "name": name,
                 "code": code,
                 "project": "<Context.Project>",
                 "asset_type": "<Context.AssetType>",
                 "description": f"{name} and {code}"
             }
             
        return params

    def execute_plan(self, plan):
        self.log_section("🚀 Executing Plan")
        context = {} 
        success_count = 0
        created_project_name = None
        
        for step in plan:
            node_type = step['type']
            name = step['name']
            ui_params = step['params']
            
            try:
                entity = None
                
                if node_type == "project":
                    self.log(f"Processing Project: {name}...", "INFO")
                    # Step 1: Create/Get with MANDATORY params
                    entity = gazu.project.get_project_by_name(name)
                    if not entity:
                        entity = gazu.project.new_project(
                            name=name,
                            production_type=step['params'].get('production_type', 'short'),
                            production_style=step['params'].get('production_style', '2d3d')
                        )
                    created_project_name = name
                    
                    # Step 2: Inject Optional Params (Code, Description)
                    code_val = step['params'].get('code')
                    desc_val = step['params'].get('description')
                    
                    if code_val:
                        self.log(f"adding value to code parameter in the {node_type} entity", "INFO")
                        entity['code'] = code_val
                        # Need to update entity dict locally if we want gazu to use it? 
                        # Actually gazu.project.update_project takes the dict and sends it.
                        # But we should also ensure the dict we have HAS the new value before sending?
                        # Yes: project["code"] = ... then update_project(project)
                    
                    if desc_val:
                         self.log(f"adding value to description parameter in the {node_type} entity", "INFO")
                         entity['description'] = desc_val
                    
                    if code_val or desc_val:
                         gazu.project.update_project(entity)
                    
                    # Step 3: Inject Data (Metadata)
                    data_val = step['params'].get('data')
                    if data_val:
                         self.log(f"adding data to 'data' parameter in the {node_type} entity", "INFO")
                         gazu.project.update_project_data(entity, data=data_val)
                         # Update local entity Ref
                         entity['data'] = data_val


                elif node_type == "episode":
                    proj = context.get("project")
                    if proj: 
                        # Step 1: Create
                        entity = gazu.shot.get_episode_by_name(proj, name)
                        if not entity:
                            entity = gazu.shot.new_episode(project=proj, name=name)
                        
                        # Step 2: Code/Desc
                        code_val = step['params'].get('code')
                        desc_val = step['params'].get('description')
                        
                        updated = False
                        if code_val: 
                            self.log(f"adding value to code parameter in the {node_type} entity", "INFO")
                            entity['code'] = code_val; updated = True
                        if desc_val:
                            self.log(f"adding value to description parameter in the {node_type} entity", "INFO")
                            entity['description'] = desc_val; updated = True
                            
                        if updated:
                            # gazu.shot.update_episode(episode)
                            gazu.shot.update_episode(entity)
                            
                        # Step 3: Data
                        data_val = step['params'].get('data')
                        if data_val:
                            self.log(f"adding data to 'data' parameter in the {node_type} entity", "INFO")
                            gazu.shot.update_episode_data(entity, data=data_val)
                            entity['data'] = data_val
                            
                    else: self.log(f"⚠️ Skipping Episode '{name}': Missing Project context.", "ERROR")

                elif node_type == "sequence":
                    proj = context.get("project")
                    ep = context.get("episode") # Can be none if preset doesn't use episodes
                    if proj: 
                        entity = gazu.shot.get_sequence_by_name(proj, name)
                        if not entity:
                             # new_sequence may require episode?
                             # gazu.shot.new_sequence(project, name, episode=None)
                             entity = gazu.shot.new_sequence(project=proj, name=name, episode=ep)
                        
                        # Update Code/Desc
                        updated = False
                        if step['params'].get('code'): 
                             self.log(f"adding value to code parameter in the {node_type} entity", "INFO")
                             entity['code'] = step['params']['code']; updated=True
                        if step['params'].get('description'):
                             self.log(f"adding value to description parameter in the {node_type} entity", "INFO")
                             entity['description'] = step['params']['description']; updated=True
                        
                        if updated: gazu.shot.update_sequence(entity)
                        
                        # Update Data
                        if step['params'].get('data'):
                             self.log(f"adding data to 'data' parameter in the {node_type} entity", "INFO")
                             gazu.shot.update_sequence_data(entity, data=step['params']['data'])
                             entity['data'] = step['params']['data']
                             
                    else: self.log(f"⚠️ Skipping Sequence '{name}': Missing Project.", "ERROR")
                
                elif node_type == "shot":
                     proj = context.get("project")
                     seq = context.get("sequence")
                     if proj and seq:
                          # Check existence? gazu.shot.get_shot_by_name(sequence, name)?
                          # Usually we might not check for shots as they are many. Assume Create/Get.
                          # But get_or_create_shot checked.
                          # Let's try creation directly, catch if exists? Gazu usually errors or returns.
                          # new_shot(project, sequence, name, frame_in=None, frame_out=None)
                          
                          # We try to get it first?
                          # existing_shots = gazu.shot.all_shots_for_sequence(seq) ... slow?
                          # Let's trust new_shot usually returns validation error if exists or we handle it.
                          # Better: try new_shot.
                          try:
                              params_in = {
                                  "project": proj,
                                  "sequence": seq,
                                  "name": name,
                                  "frame_in": step['params'].get("frame_in"),
                                  "frame_out": step['params'].get("frame_out"),
                                  "nb_frames": step['params'].get("nb_frames")
                              }
                              entity = gazu.shot.new_shot(**params_in)
                          except Exception:
                              # Assume exists?
                              # Try fetch?
                              pass 
                          
                          if not entity:
                               # Fallback fetch?
                               # Actually gazu.shot.get_shot_by_name uses sequence.
                               entity = gazu.shot.get_shot_by_name(seq, name)
                               
                          if entity:
                              # Update Code/Desc
                              updated = False
                              if step['params'].get('code'): 
                                  self.log(f"adding value to code parameter in the {node_type} entity", "INFO")
                                  entity['code'] = step['params']['code']; updated=True
                              if step['params'].get('description'):
                                  self.log(f"adding value to description parameter in the {node_type} entity", "INFO")
                                  entity['description'] = step['params']['description']; updated=True
                              
                              if updated: gazu.shot.update_shot(entity)
                              
                              # Update Data
                              tasks_val = step['params'].get('tasks') # Special for shot?
                              # Data
                              data_val = step['params'].get('data') or {}
                              # Merge tasks? User script didn't mention tasks in data update, but 'data' dict.
                              if data_val:
                                  self.log(f"adding data to 'data' parameter in the {node_type} entity", "INFO")
                                  gazu.shot.update_shot_data(entity, data=data_val)
                                  entity['data'] = data_val

                elif node_type == "asset_type":
                    entity = get_or_create_asset_type(name) # Keep this simple
                    
                elif node_type == "asset":
                    proj = context.get("project")
                    at = context.get("asset_type") # Asset type entity
                    if proj and at:
                        # gazu.asset.new_asset(project, asset_type, name)
                        # Check exist?
                        # entity = gazu.asset.get_asset_by_name(project, name) -> needs keys?
                        # gazu.asset.get_asset_by_name(project, name)
                        entity = gazu.asset.get_asset_by_name(proj, name)
                        if not entity:
                            entity = gazu.asset.new_asset(project=proj, asset_type=at, name=name)
                        
                        # Update Code/Desc
                        updated = False
                        if step['params'].get('code'): 
                             self.log(f"adding value to code parameter in the {node_type} entity", "INFO")
                             entity['code'] = step['params']['code']; updated=True
                        if step['params'].get('description'):
                             self.log(f"adding value to description parameter in the {node_type} entity", "INFO")
                             entity['description'] = step['params']['description']; updated=True
                        
                        if updated: gazu.asset.update_asset(entity)
                        
                        # Update Data
                        if step['params'].get('data'):
                             self.log(f"adding data to 'data' parameter in the {node_type} entity", "INFO")
                             gazu.asset.update_asset_data(entity, data=step['params']['data'])
                             entity['data'] = step['params']['data']

                if entity:
                    self.log(f"   ✓ Processed: {node_type.capitalize()} -> {name}", "SUCCESS")
                    # Store the live entity data back into the plan for the UI to use
                    step['fetched_data'] = entity
                    
                    if node_type == "project": context["project"] = entity
                    elif node_type == "episode": context["episode"] = entity
                    elif node_type == "sequence": context["sequence"] = entity
                    elif node_type == "shot": context["shot"] = entity
                    elif node_type == "asset_type": context["asset_type"] = entity
                    elif node_type == "asset": context["asset"] = entity
                    success_count += 1
                else:
                    self.log(f"   ❌ Failed: {name}", "ERROR")

            except Exception as e:
                self.log(f"❌ Error processing {name}: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "DEBUG")

        self.log_section("🏁 Execution Finished")
        self.log(f"Processed {len(plan)} items. Success: {success_count}.", "INFO")
        
        # --- Post-Verification ---
        if created_project_name:
            self.verify_project_data(created_project_name)
            return True
        else:
            return False

    def verify_project_data(self, project_name):
        self.log_section("🔍 Post-Creation Verification")
        try:
            import pprint
            
            # 1. Fetch Project
            project = gazu.project.get_project_by_name(project_name)
            if not project:
                self.log(f"❌ CRITICAL: Could not find project '{project_name}' in Kitsu!", "ERROR")
                return

            self.log(f"✅ PROJECT FOUND: {project['name']} (ID: {project['id']})", "SUCCESS")
            self.log(f"   Type: {project.get('production_type')} | Style: {project.get('production_style')}", "INFO")
            
            # Log selected interesting fields
            data_fields = ['resolution', 'fps', 'ratio', 'start_date', 'end_date']
            data_summary = {k: project.get(k) or project.get('data', {}).get(k) for k in data_fields}
            self.log(f"   Parameters: {json.dumps(data_summary)}", "INFO")

            # 2. Fetch Sequences
            sequences = gazu.shot.all_sequences_for_project(project)
            self.log(f"\n📂 SEQUENCES FOUND: {len(sequences)}", "INFO")
            
            for seq in sequences:
                self.log(f"   ► Sequence: {seq.get('name')}", "INFO")
                
                # 3. Fetch Shots
                shots = gazu.shot.all_shots_for_sequence(seq)
                if shots:
                    self.log(f"     └── Shots ({len(shots)}):", "INFO")
                    for shot in shots:
                        # Format nice shot info
                        fr_in = shot.get('data', {}).get('frame_in', '-')
                        fr_out = shot.get('data', {}).get('frame_out', '-')
                        self.log(f"         • {shot.get('name')} [Frames: {fr_in}-{fr_out}]", "INFO")
        
        except Exception as e:
            self.log(f"❌ Verification Failed: {e}", "ERROR")
