import gazu

def get_or_create_sequence(project, name, episode=None):
    """
    Get or create a sequence. 
    Can be episode-bound or project-bound.
    """
    if episode:
        sequence = gazu.shot.get_sequence_by_name(project, name, episode)
        if not sequence:
            sequence = gazu.shot.new_sequence(project, name, episode=episode)
            print(f"Created Sequence: {name} (Episode: {episode['name']})")
        else:
            print(f"Found Sequence: {name}")
    else:
        sequence = gazu.shot.get_sequence_by_name(project, name)
        if not sequence:
            sequence = gazu.shot.new_sequence(project, name)
            print(f"Created Sequence: {name} (Global)")
        else:
            print(f"Found Sequence: {name}")

    # --- Data Injection Logic ---
    project_data = project.get('data', {})
    project_code = project_data.get('project_code', project['name'][:3].lower())
    project_path = project_data.get('project_path', "")

    sequence_code = name.lower()
    
    if episode:
        # Parent is Episode
        episode_data = episode.get('data', {})
        parent_code = episode_data.get('episode_code', episode['name'].lower())
        parent_path = episode_data.get('episode_path', f"{project_path}/{parent_code}")
        parent_type = "episode"
        sequence_path = f"{parent_path}/{sequence_code}"
    else:
        # Parent is Project
        parent_code = project_code
        parent_path = project_path
        parent_type = "project"
        # Assuming 'film' folder for project-level sequences as per 'film' type structure
        sequence_path = f"{parent_path}/film/{sequence_code}"

    data = {
        # Inherited & Identification
        "project_code": project_code,
        "project_path": project_path,
        
        "parent_code": parent_code,
        "parent_path": parent_path,
        "parent_type": parent_type,
        
        "sequence_code": sequence_code,
        "sequence_name": name,
        "sequence_path": sequence_path,

        # Tree Structure
        "sequence_tree": {
            "{shot}": {
                "{task_type}": {
                    "work": {},
                    "publish": {}
                }
            }
        }
    }
    
    # Update Entity
    current_data = sequence.get("data", {})
    if current_data is None: current_data = {}
    current_data.update(data)
    
    gazu.raw.update("sequences", sequence["id"], {"data": current_data})
    sequence["data"] = current_data
    
    return sequence
