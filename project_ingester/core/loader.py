import gazu
from ..kitsu_config import KITSU_HOST, KITSU_EMAIL, KITSU_PASSWORD

class ProjectLoader:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback if log_callback else print
        self.connected = False

    def log(self, message, level="INFO"):
        self.log_callback(message, level)

    def connect(self):
        if self.connected:
            return True
        
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

    def get_all_projects(self):
        if not self.connect():
            return []
        try:
            return gazu.project.all_projects()
        except Exception as e:
            self.log(f"Failed to fetch projects: {e}", "ERROR")
            return []

    def load_full_project(self, project_id):
        if not self.connect():
            return None

        try:
            project = gazu.project.get_project(project_id)
            if not project:
                self.log(f"Project with ID {project_id} not found.", "ERROR")
                return None

            self.log(f"Loading project: {project['name']}...", "INFO")
            
            # Determine structure type based on production_style/type
            # Fallback to 'short' if not specified
            prod_type = project.get('production_type', 'short')
            
            # Structure we will build
            # { "type": "project", "properties": {...}, "children": [...] }
            
            root_data = {
                "type": "project",
                "properties": self._extract_properties(project, "project"),
                "children": []
            }
            
            # Fetch Episodes if TV Show
            is_tv = prod_type in ['tv_show', 'tv']
            
            if is_tv:
                self.log("Fetching Episodes...", "INFO")
                episodes = gazu.shot.all_episodes_for_project(project)
                for ep in episodes:
                    ep_node = {
                        "type": "episode",
                        "properties": self._extract_properties(ep, "episode"),
                        "children": []
                    }
                    
                    self.log(f"  Fetching Sequences for {ep['name']}...", "INFO")
                    sequences = gazu.shot.all_sequences_for_episode(ep)
                    for seq in sequences:
                        seq_node = self._process_sequence(project, seq)
                        ep_node["children"].append(seq_node)
                        
                    root_data["children"].append(ep_node)
            else:
                # Film / Short
                self.log("Fetching Sequences...", "INFO")
                sequences = gazu.shot.all_sequences_for_project(project)
                for seq in sequences:
                    seq_node = self._process_sequence(project, seq)
                    root_data["children"].append(seq_node)

            # Fetch Assets
            self.log("Fetching Assets...", "INFO")
            # Organize assets by Asset Type
            asset_types = gazu.asset.all_asset_types_for_project(project)
            if not asset_types:
                 # Fallback if specific project types not set, get global
                 asset_types = gazu.asset.all_asset_types()
            
            for at in asset_types:
                assets = gazu.asset.all_assets_for_project_and_type(project, at)
                if not assets:
                    continue
                    
                at_node = {
                    "type": "asset_type",
                    "properties": {"name": at['name']}, # Asset types usually just have name
                    "children": []
                }
                
                for asset in assets:
                    asset_node = {
                        "type": "asset",
                        "properties": self._extract_properties(asset, "asset"),
                        "children": [] # Assets might have tasks, but tree stops here usually?
                    }
                    at_node["children"].append(asset_node)
                    
                root_data["children"].append(at_node)

            self.log("✅ Project structure loaded successfully.", "SUCCESS")
            return root_data

        except Exception as e:
            self.log(f"❌ Error loading project: {e}", "ERROR")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            return None

    def _process_sequence(self, project, sequence):
        seq_node = {
            "type": "sequence",
            "properties": self._extract_properties(sequence, "sequence"),
            "children": []
        }
        
        shots = gazu.shot.all_shots_for_sequence(sequence)
        for shot in shots:
            shot_node = {
                "type": "shot",
                "properties": self._extract_properties(shot, "shot"),
                "children": []
            }
            seq_node["children"].append(shot_node)
            
        return seq_node

    def _extract_properties(self, entity, entity_type):
        """
        Extracts relevant properties to populate the NodeFrame.properties + extras.
        Also flattens 'data' if present for easier viewing.
        """
        props = {}
        
        # Standard fields
        props["name"] = entity.get("name", "Unknown")
        props["description"] = entity.get("description", "")
        props["id"] = entity.get("id")
        props["created_at"] = entity.get("created_at")
        props["updated_at"] = entity.get("updated_at")
        
        # Entity specific
        if entity_type == "project":
            props["code"] = entity.get("code")
            props["production_type"] = entity.get("production_type")
            props["fps"] = entity.get("fps")
            props["ratio"] = entity.get("ratio")
            props["resolution"] = entity.get("resolution")
            props["start_date"] = entity.get("start_date")
            props["end_date"] = entity.get("end_date")
            
        elif entity_type == "sequence":
            props["code"] = entity.get("code", "")
            
        elif entity_type == "shot":
            props["code"] = entity.get("code", "")
            props["frame_in"] = entity.get("frame_in")
            props["frame_out"] = entity.get("frame_out")
            props["nb_frames"] = entity.get("nb_frames")
            
        elif entity_type == "asset":
            # Assets don't strictly have 'code' in generic Kitsu, usually just name
            pass

        # Inject 'data' dictionary as flattened keys or keep as is
        # The prompt says: "their properties for every entity in the properties panel and every parameter of every entity will be logged"
        # We will keep 'data' as is in properties to be shown in the UI form if needed, 
        # or just mix them in. NodeFrame generally expects 'data' key for extra stuff.
        if entity.get("data"):
            props["data"] = entity.get("data")
            
        # Add all other keys from entity just in case, for logging purposes
        # But filter out heavy stuff if any
        for k, v in entity.items():
            if k not in props and k != "data":
                 props[k] = v
                 
        return props
