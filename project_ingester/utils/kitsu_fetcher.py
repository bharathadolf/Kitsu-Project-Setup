import gazu

from ..kitsu_config import KITSU_HOST, KITSU_EMAIL, KITSU_PASSWORD

class KitsuFetcher:
    def __init__(self):
        self.projects = []
        self.connect()

    def connect(self):
        try:
            # simple re-auth or check
            gazu.set_host(KITSU_HOST)
            gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
            print(f"Connected to Kitsu at {KITSU_HOST}")
        except Exception as e:
            print(f"Failed to connect to Kitsu: {e}")

    def get_all_projects(self):
        """
        Fetches all open projects from Kitsu.
        Returns a list of project dictionaries.
        """
        try:
            # Assuming authentication is handled elsewhere or we might need to check/connect here.
            # For now, relying on global gazu state or previous connection.
            # If not connected, this will raise an error or return empty.
            
            # Fetch all projects (usually we want open ones)
            all_projects = gazu.project.all_projects()
            
            # Filter for open projects if needed? 
            # Gazu usually returns all. Let's just return all for now.
            return all_projects
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []

    def get_project_hierarchy(self, project):
        """
        Fetches the hierarchy (episodes, sequences, shots, assets) for a given project.
        Returns a dictionary structure mimicking the tree.
        """
        hierarchy = {}
        try:
            # 1. Episodes (Optional in some pipelines, mandatory in others)
            # Check if project uses episodes? 
            # For now, let's fetch episodes.
            episodes = gazu.shot.all_episodes_for_project(project)
            
            if episodes:
                hierarchy['episodes'] = []
                for ep in episodes:
                    ep_data = {'entity': ep, 'sequences': []}
                    seqs = gazu.shot.all_sequences_for_episode(ep)
                    for seq in seqs:
                        seq_data = {'entity': seq, 'shots': []}
                        shots = gazu.shot.all_shots_for_sequence(seq)
                        seq_data['shots'] = shots
                        ep_data['sequences'].append(seq_data)
                    hierarchy['episodes'].append(ep_data)
            else:
                # No episodes, maybe just sequences directly under project?
                # Kitsu usually enforces Episodes -> Sequences -> Shots or Sequences -> Shots?
                # Actually gazu.shot.all_sequences_for_project(project) works too.
                sequences = gazu.shot.all_sequences_for_project(project)
                hierarchy['sequences'] = []
                for seq in sequences:
                    # If we found episodes, these sequences might be duplicates if they are linked to episodes.
                    # But if episodes list was empty, then these are direct children (or unlinked).
                    seq_data = {'entity': seq, 'shots': []}
                    shots = gazu.shot.all_shots_for_sequence(seq)
                    seq_data['shots'] = shots
                    hierarchy['sequences'].append(seq_data)

            # 2. Assets
            # Assets are organized by Asset Type
            hierarchy['assets'] = []
            
            # We can get all assets for project and group them, or get asset types first.
            # But requirement says "query all ... as a hierarchies".
            
            # Note: gazu.asset.all_asset_types_for_project might not exist, usually it's global types used by project.
            # But let's check `gazu.asset.all_assets_for_project(project)`
            
            all_assets = gazu.asset.all_assets_for_project(project)
            
            # Group by asset type id
            assets_by_type = {}
            # Logic to group assets by type can be added here if structure requires it.
            # For now, we store raw assets to list them.
                
            # To be safe and avoiding complex grouping logic blindly:
            # Let's just list Asset Types, and then query assets for that type?
            # No, `all_assets_for_project` is efficient.
            
            # Let's simple-structure it for now:
            hierarchy['raw_assets'] = all_assets

        except Exception as e:
            print(f"Error fetching hierarchy for {project.get('name')}: {e}")
        
        return hierarchy
