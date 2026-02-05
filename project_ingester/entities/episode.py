import gazu

def get_or_create_episode(project, name):
    """
    Get or create an episode within a project.
    """
    episode = gazu.shot.get_episode_by_name(project, name)
    if not episode:
        episode = gazu.shot.new_episode(project, name)
        print(f"Created Episode: {name}")
    else:
        print(f"Found Episode: {name}")
        
    # --- Data Injection Logic ---
    project_data = project.get('data', {})
    # Fallback if project data isn't fully populated yet
    project_code = project_data.get('project_code', project['name'][:3].lower())
    project_path = project_data.get('project_path', "")
    
    episode_code = name.lower()
    # If project_path is empty, we might not be able to fully construct episode_path correctly 
    # but we follow the logic provided.
    episode_path = f"{project_path}/{episode_code}" if project_path else f"{episode_code}"

    data = {
        # Inherited & Identification
        "project_code": project_code,
        "project_path": project_path,
        "parent_type": "project",
        
        "episode_code": episode_code,
        "episode_name": name,
        "episode_path": episode_path,

        # Tree Structure
        "episode_tree": {
            "{sequence}": {
                "{shot}": {
                    "{task_type}": {
                        "work": {},
                        "publish": {}
                    }
                }
            }
        }
    }
    
    # Update Entity
    current_data = episode.get("data", {})
    if current_data is None: current_data = {}
    current_data.update(data)
    
    gazu.raw.update("episodes", episode["id"], {"data": current_data})
    
    # Refresh object
    episode["data"] = current_data
    
    return episode
