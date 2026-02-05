import gazu
from .task import get_or_create_task, get_or_create_task_type

def get_or_create_asset_type(name, project=None):
    """
    Get or create an asset type.
    Note: Standard Kitsu defines AssetType as global.
    However, if user requested project-bound creation, we try to support it
    or fallback to global. Usually one just needs the type ID.
    User request was: gazu.asset.new_asset_type(project, name) which implies specific logic.
    We will try to implement that signature support if possible.
    """
    # Strict compliance to user request / codebase analysis
    # Try global lookup first
    at = gazu.asset.get_asset_type_by_name(name)
    if not at:
        try:
            # Try user's requested signature
            if project:
                # Assuming hypothetical API extension or strict user requirement
                # If this fails (standard gazu), we catch and fallback
                at = gazu.asset.new_asset_type(name) # Standard Gazu doesn't take project, but let's assume global.
                # If user INSISTS on project bound:
                # at = gazu.asset.new_asset_type(project, name) # This would fail in standard Gazu 0.8.x
                # We will stick to standard valid Gazu unless error proven.
                # But wait, previous code analysis showed I should respect user code block.
                # User code block: `get_or_create_asset_type(name)` -> `gazu.asset.new_asset_type(name)`
                # The user's provided SCRIPT in the prompt used `gazu.asset.new_asset_type(name)` (Global).
                # SO I WILL USE GLOBAL.
                pass
            else:
                at = gazu.asset.new_asset_type(name)
            print(f"Created Asset Type: {name}")
        except Exception as e:
            print(f"Error creating Asset Type {name}: {e}")
            return None
    return at

def get_or_create_asset(project, asset_type, name, description="", custom_data=None, tasks=None):
    """
    Get or create an asset.
    """
    asset = gazu.asset.get_asset_by_name(project, asset_type, name)
    if not asset:
        asset = gazu.asset.new_asset(project, asset_type, name, description=description)
        print(f"Created Asset: {name}")
        
        # Inject Custom Data (Merged below)
    else:
        print(f"Found Asset: {name}")
        
    # --- Data Injection Logic ---
    project_data = project.get('data', {})
    project_code = project_data.get('project_code', project['name'][:3].lower())
    project_path = project_data.get('project_path', "")

    asset_type_name = asset_type['name']
    # Assuming 'assets' folder is where assets live.
    asset_type_path = f"{project_path}/assets/{asset_type_name.lower()}"
    
    asset_code = name.lower()
    asset_path = f"{asset_type_path}/{asset_code}"

    data = {
        # Inherited & Identification
        "project_code": project_code,
        "project_path": project_path,
        
        "asset_type": asset_type_name,
        "asset_type_path": asset_type_path,
        "parent_type": "asset_type",
        
        "asset_code": asset_code,
        "asset_name": name,
        "asset_path": asset_path,

        # Tree Structure
        "asset_tree": {
            "{task_type}": {
                "work": {},
                "publish": {}
            }
        }
    }
    
    # Update Entity
    current_data = asset.get("data", {})
    if current_data is None: current_data = {}
    current_data.update(data)
    
    if custom_data:
        clean_data = {}
        for k, v in custom_data.items():
            if isinstance(v, dict) and "value" in v:
                clean_data[k] = v["value"]
            else:
                clean_data[k] = v
        current_data.update(clean_data)

    gazu.raw.update("assets", asset["id"], {"data": current_data})
    asset["data"] = current_data

        
    if tasks:
        for task_name in tasks:
            task_type = get_or_create_task_type(task_name)
            if task_type:
                get_or_create_task(asset, task_type)

    return asset
