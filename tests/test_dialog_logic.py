
import sys
import os
import json

# Add project root path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import QApplication, QDialog, Qt
from project_ingester.ui.dialogs import GenerationSummaryDialog

# Mock ProjectManager
class MockManager:
    pass

def run_test():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    print(" [TEST] Starting Dialog Logic Test...")
    
    # 1. Create a Dummy Plan
    plan = [
        {
            "type": "project",
            "name": "OldProject",
            "params": {
                "name": "OldProject",
                "code": "old",
                "description": "OldProject and old",
                "data": {
                    "project_code": "old",
                    "project_path": "X:/old"
                }
            }
        },
        {
            "type": "episode",
            "name": "Episode 01",
            "params": {
                "name": "Episode 01",
                "code": "ep01",
                "description": "Episode 01 and ep01",
                "data": {
                    "episode_name": "Episode 01",
                    "episode_code": "ep01"
                }
            }
        }
    ]
    
    dialog = GenerationSummaryDialog(plan, manager=MockManager())
    
    # 2. Simulate Renaming Project
    print("\n [TEST] Renaming Project 'OldProject' -> 'NewProject'")
    
    # Find Project Item (Row 0)
    root = dialog.tree.invisibleRootItem()
    proj_item = root.child(0)
    
    # Simulate Edit
    proj_item.setText(1, "NewProject")
    # Manually trigger on_item_changed logic since setText emits signal? 
    # QTreeWidget.itemChanged emits when data changes. Verify if setText triggers it.
    # Usually yes, if connected.
    
    # Verification
    step = proj_item.data(0, Qt.UserRole)
    print(f" [CHECK] New Name: {step['name']}")
    print(f" [CHECK] New Code: {step['params']['code']}")
    print(f" [CHECK] New Description: {step['params']['description']}")
    
    data = step['params'].get('data', {})
    print(f" [CHECK] Data.project_code: {data.get('project_code')}")
    print(f" [CHECK] Data.project_path: {data.get('project_path')}")
    
    if step['params']['code'] == "newproject": # auto-gen code is lowercase name usually (or first 3 chars depending on logic)
         # code_gen.generate_project_code usually returns slugified or first 3 chars. 
         # We need to see what it actually returns.
         pass
         
    # 3. Simulate Renaming Episode
    print("\n [TEST] Renaming Episode 'Episode 01' -> 'Episode 99'")
    ep_item = root.child(1) # Assuming flat list/root for testing populate_tree logic
    # Wait, populate_tree reconstructs hierarchy. Episode might be child of Project if hierarchy exists?
    # But our plan list is flat. `populate_tree` code tries to map parents.
    # In this logic, Episode has no 'widget' attached so it won't find parent mapped. 
    # So both will be at root. Correct.
    
    ep_item.setText(1, "Episode 99")
    
    ep_step = ep_item.data(0, Qt.UserRole)
    print(f" [CHECK] New Name: {ep_step['name']}")
    print(f" [CHECK] New Code: {ep_step['params']['code']}") # Should NOT change
    
    ep_data = ep_step['params'].get('data', {})
    print(f" [CHECK] Data.episode_name: {ep_data.get('episode_name')}")
    
    # 4. Check Pretty Printing
    print("\n [TEST] Checking HTML Output for Project...")
    dialog.on_item_clicked(proj_item, 0)
    html = dialog.details.toHtml()
    if "<pre" in html:
        print(" [PASS] HTML contains <pre> tag for pretty printing.")
    else:
        print(" [FAIL] HTML missing <pre> tag. Output snippet:")
        print(html[:200])

if __name__ == "__main__":
    run_test()
