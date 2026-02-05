import gazu
from .task import get_or_create_task, get_or_create_task_type

def get_or_create_shot(project, sequence, name, frame_in=None, frame_out=None, nb_frames=None, description="", custom_data=None, tasks=None):
    """
    Get or create a shot.
    Also handles default task creation.
    """
    shot = gazu.shot.get_shot_by_name(sequence, name)
    
    if not shot:
        # Create
        kwargs = {}
        if frame_in is not None: kwargs['frame_in'] = frame_in
        if frame_out is not None: kwargs['frame_out'] = frame_out
        if nb_frames is not None: kwargs['nb_frames'] = nb_frames
        if description: kwargs['description'] = description
        
        shot = gazu.shot.new_shot(project, sequence, name, **kwargs)
        print(f"Created Shot: {name}")

        # Inject Custom Data (Merging into our main data logic below or keeping separate?)
        # We will merge it.
    else:
        print(f"Found Shot: {name}")

    # --- Data Injection Logic ---
    project_data = project.get('data', {})
    project_code = project_data.get('project_code', project['name'][:3].lower())
    project_path = project_data.get('project_path', "")
    
    sequence_data = sequence.get('data', {})
    sequence_code = sequence_data.get('sequence_code', sequence['name'].lower())
    sequence_path = sequence_data.get('sequence_path', f"{project_path}/{sequence_code}")

    shot_code = name.lower()
    shot_path = f"{sequence_path}/{shot_code}"

    data = {
        # Inherited & Identification
        "project_code": project_code,
        "project_path": project_path,
        
        "sequence_code": sequence_code,
        "sequence_path": sequence_path,
        "parent_type": "sequence",
        
        "shot_code": shot_code,
        "shot_name": name,
        "shot_path": shot_path,

        # Tree Structure
        "shot_tree": {
            "{task_type}": {
                "work": {},
                "publish": {}
            }
        }
    }

    # Update Data
    current_data = shot.get("data", {})
    if current_data is None: current_data = {}
    current_data.update(data)

    # If custom_data was passed, merge it as well
    if custom_data:
        clean_data = {}
        for k, v in custom_data.items():
            if isinstance(v, dict) and "value" in v:
                clean_data[k] = v["value"]
            else:
                clean_data[k] = v
        current_data.update(clean_data)

    gazu.raw.update("shots", shot["id"], {"data": current_data})
    shot["data"] = current_data
    
    if tasks:
        # tasks is a list of task type names, e.g. ["Compositing", "Animation"]
        for task_name in tasks:
            task_type = get_or_create_task_type(task_name)
            if task_type:
                get_or_create_task(shot, task_type)

    return shot
