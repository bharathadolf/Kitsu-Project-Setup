import gazu

def get_or_create_task_type(name):
    """
    Get or create a task type (globally).
    """
    task_type = gazu.task.get_task_type_by_name(name)
    if not task_type:
        task_type = gazu.task.new_task_type(name)
        print(f"Created Task Type: {name}")
    return task_type

def get_or_create_task(entity, task_type):
    """
    Get or create a task on an entity (Shot or Asset).
    """
    # Check if task exists on entity
    # gazu.task.get_task_by_entity(entity, task_type) # valid?
    # Standard Gazu: gazu.task.get_task(entity, task_type) or iterate
    # User script used: any(t.get("task_type_id") == ... in all_tasks_for_shot)
    
    # We need a generic way for any entity (Shot or Asset)
    # gazu.task.all_tasks_for_entity(entity) doesn't exist? 
    # gazu.task.all_tasks_for_shot / gazu.task.all_tasks_for_asset
    
    tasks = []
    # Identify entity type by checking keys or 'type' field if available, 
    # but Gazu dicts don't always have 'type'.
    # We can try both or assume context.
    # However, to be robust:
    
    entity_id = entity["id"]
    # We can fetch tasks by entity_id? 
    # gazu.task.all_tasks_for_entity(entity) IS available in newer Gazu versions.
    # If not, we fallback.
    
    try:
        tasks = gazu.task.all_tasks_for_entity(entity)
    except AttributeError:
        # Fallback to duck typing
        if "shot_id" in entity or "sequence_id" in entity: # Shot properties?
             # Shot usually has sequence_id?
             # Or just try `all_tasks_for_shot`
             try: tasks = gazu.task.all_tasks_for_shot(entity)
             except: pass
        
        if not tasks:
            try: tasks = gazu.task.all_tasks_for_asset(entity)
            except: pass

    # Check existence
    existing = False
    for t in tasks:
        if t["task_type_id"] == task_type["id"]:
            existing = True
            break
            
    if not existing:
        task = gazu.task.new_task(entity, task_type)
        print(f"    Task Created: {task_type['name']} on {entity.get('name', 'Entity')}")
        return task
    else:
        print(f"    Task Exists: {task_type['name']} on {entity.get('name', 'Entity')}")
        return None
