import os
from ..data.rules import RULE_MAP

class FolderMapper:
    def __init__(self):
        pass

    def scan_structure(self, template_name, mappings):
        """
        Scans folders based on the mappings provided by FolderBuilderDialog.
        
        Args:
            template_name (str): Selected project template (e.g. "TV Show")
            mappings (dict): Key=EntityType, Value=FolderPath (e.g. {'project': 'C:/Proj', 'episode': 'C:/Proj/Eps'})
            
        Returns:
            dict: Nested structure ready for tree population.
        """
        
        # 1. Project Root
        project_path = mappings.get('project')
        if not project_path or not os.path.exists(project_path):
            return None
            
        project_name = os.path.basename(project_path)
        
        structure = {
            "type": "project",
            "name": project_name,
            "path": project_path,
            "children": []
        }
        
        # 2. Derive Hierarchy from Template
        rules = RULE_MAP.get(template_name, {})
        project_children_types = rules.get('project', {}).get('children', [])
        
        # 3. Recursively Build
        # We need to pass the parent path to connect the dots if user didn't map every single level explicitly.
        # But per requirements, user maps "Entity Levels" to "Folders".
        
        # Let's handle the direct children of Project first
        for child_type in project_children_types:
            self._process_level(structure, child_type, mappings, rules)
            
        return structure

    def _process_level(self, parent_node, entity_type, mappings, rules):
        """
        Populate parent_node['children'] with nodes of entity_type.
        """
        # 1. Check if user explicitly mapped this entity type
        mapped_path = mappings.get(entity_type.lower())
        
        candidates = []
        
        if mapped_path and os.path.exists(mapped_path):
            # User said "Episodes are in X"
            # So every folder in X is an Episode
            try:
                # We scan the mapped folder for subfolders
                if os.path.isdir(mapped_path):
                    for entry in os.scandir(mapped_path):
                        if entry.is_dir():
                            candidates.append({
                                "name": entry.name,
                                "path": entry.path
                            })
            except Exception as e:
                print(f"Error scanning {mapped_path}: {e}")
                
        # 2. If no explicit mapping, can we infer it?
        # Only if the parent has a path we can look into?
        # For now, let's rely on explicit mappings for high levels, 
        # OR if the parent path is known, we can maybe look for a folder named "{entity_type}s"?
        # But requirement says "User maps folder names".
        
        # Strategy: If mapped, use it. If not, skip? 
        # Or maybe the mapped path IS the parent folder.
        
        if not candidates:
            return

        # 3. Create Nodes
        entity_rules = rules.get(entity_type, {})
        allowed_children = entity_rules.get("children", [])
        
        for cand in candidates:
            new_node = {
                "type": entity_type,
                "name": cand['name'],
                "path": cand['path'], # Store for potentially finding children
                "children": []
            }
            parent_node['children'].append(new_node)
            
            # Recurse for grandchildren
            # But wait, mappings are global "Entity Type -> Folder".
            # If I mapped "Sequence" -> "D:/Seqs", that implies ALL sequences are flat in there? 
            # unlikely for a tree.
            # Usually structure is nested: Project/Ep01/Sq01...
            
            # HYBRID APPROACH:
            # If "Sequence" is mapped globally, does it mean "Look for a folder named Sequence inside the parent"?
            # OR "Use the 'Sequence' mapping path provided by user"?
            # If the user maps "Sequence" -> "C:/MyProject/Sequences", then maybe all sequences are there.
            # BUT if the user maps "Episode" -> "C:/MyProject/Episodes", we found "Ep01".
            # Inside "Ep01", we expect to find Sequences.
            
            # AUTOMATIC DISCOVERY:
            # Once we are inside a scanned entity (e.g. Ep01 path), we should look for children folders there.
            # unless told otherwise.
            
            if allowed_children:
                for child_type in allowed_children:
                     self._scan_children_recursive(new_node, child_type, rules)

    def _scan_children_recursive(self, parent_node, child_type, rules):
        parent_path = parent_node.get('path')
        if not parent_path or not os.path.isdir(parent_path):
            return

        # We assume children folders are directly inside parent folder
        # e.g. Ep01/Sq01, Ep01/Sq02
        
        # Check if there is an intermediate folder? e.g. Ep01/Sequences/Sq01?
        # Some pipelines have standard folder names like "sequences" or "shots".
        # For now, simplest approach: All subfolders are candidates.
        
        entity_rules = rules.get(child_type, {})
        grand_children_types = entity_rules.get("children", [])
        
        try:
             # Heuristic: Filter out common non-entity folders?
            ignore = {".git", ".vs", "reference", "docs", "lut", "plates", "dailies"}
            
            for entry in os.scandir(parent_path):
                if entry.is_dir() and entry.name.lower() not in ignore:
                    # Create Node
                    new_node = {
                        "type": child_type,
                        "name": entry.name,
                        "path": entry.path,
                        "children": []
                    }
                    parent_node['children'].append(new_node)
                    
                    # Recurse
                    for grand_child in grand_children_types:
                        self._scan_children_recursive(new_node, grand_child, rules)
                        
        except Exception:
            pass
