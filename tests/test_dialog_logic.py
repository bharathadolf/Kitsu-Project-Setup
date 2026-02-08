
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
                    "root_path": "X:", # Added missing definition
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
                    "episode_code": "episode 01"
                }
            }
        },
        {
            "type": "asset_type",
            "name": "Characters",
            "params": {
                "name": "Characters"
            }
        },
        {
            "type": "asset",
            "name": "Hero",
            "params": {
                "name": "Hero",
                "code": "her",
                "data": {
                    "project_path": "X:/old",
                    "asset_type": "Characters",
                    "asset_type_path": "X:/old/assets/characters",
                    "asset_code": "hero",
                    "asset_path": "X:/old/assets/characters/hero"
                }
            }
        }
    ]
    
    dialog = GenerationSummaryDialog(plan, manager=MockManager())
    
    # 1.5 Fixup Hierarchy for Asset Type test (Manually parent asset under asset_type)
    root = dialog.tree.invisibleRootItem()
    
    # Indices change after reparenting, so grab them all first
    proj_item = root.child(0)
    ep_item = root.child(1)
    at_item = root.child(2)
    asset_item = root.child(3)
    
    # Reparent Asset under AT
    root.removeChild(asset_item)
    at_item.addChild(asset_item)
    
    # Reparent Episode under Project
    root.removeChild(ep_item)
    proj_item.addChild(ep_item)
    
    
    # 2. Simulate Renaming Project
    print("\n [TEST] Renaming Project 'OldProject' -> 'NewProject'")
    
    # Simulate Edit
    proj_item.setText(1, "NewProject")
    
    # Verification
    step = proj_item.data(0, Qt.UserRole)
    print(f" [CHECK] New Name: {step['name']}")
    print(f" [CHECK] New Code: {step['params']['code']}") 
    
    data = step['params'].get('data', {})
    print(f" [CHECK] Data.project_code: {data.get('project_code')}")
    print(f" [CHECK] Data.project_path: {data.get('project_path')}")
    
    if data.get('project_code') == "newpr": 
         print(" [PASS] Project Code updated.")
    else:
         print(f" [FAIL] Project Code: {data.get('project_code')}")
         
    # Check Child (Episode) Update
    # Use child count to be safe
    if proj_item.childCount() > 0:
        child_ep = proj_item.child(0)
        ep_data = child_ep.data(0, Qt.UserRole)['params'].get('data', {})
        print(f" [CHECK] Child Episode Project Path: {ep_data.get('project_path')}")
        
        if "newpr" in ep_data.get('project_path', ""):
             print(" [PASS] Child inherited new Project Path.")
        else:
             print(" [FAIL] Child did NOT inherit new Project Path.")
    else:
        print(" [FAIL] Episode child missing!")

    
    # 3. Simulate Renaming Episode
    print("\n [TEST] Renaming Episode 'Episode 01' -> 'Episode 99'")
    # Reuse ep_item from above (passed around) or fetch from hierarchy
    ep_item = proj_item.child(0)
    
    ep_item.setText(1, "Episode 99")
    
    ep_step = ep_item.data(0, Qt.UserRole)
    print(f" [CHECK] New Name: {ep_step['name']}")
    print(f" [CHECK] New Code (Param): {ep_step['params']['code']}") 
    
    ep_data = ep_step['params'].get('data', {})
    print(f" [CHECK] Data.episode_code: {ep_data.get('episode_code')}") 
    
    if ep_data.get('episode_code') == "episode 99":
         print(" [PASS] Data.episode_code updated to name.lower().")
    else:
         print(f" [FAIL] Data.episode_code: {ep_data.get('episode_code')}")
         
    # 4. Simulate Renaming Asset Type
    print("\n [TEST] Renaming Asset Type 'Characters' -> 'Props'")
    at_item.setText(1, "Props")
    
    # Check Child Asset
    child_asset_item = at_item.child(0)
    asset_step = child_asset_item.data(0, Qt.UserRole)
    asset_data = asset_step['params']['data']
    
    print(f" [CHECK] Child Asset Type Name: {asset_data.get('asset_type')}")
    print(f" [CHECK] Child Asset Type Path: {asset_data.get('asset_type_path')}")
    print(f" [CHECK] Child Asset Path: {asset_data.get('asset_path')}")
    
    if "props" in asset_data.get('asset_type_path', ""):
        print(" [PASS] Asset Type Path updated recursively.")
    else:
        print(" [FAIL] Asset Type Path NOT updated.")
        
    # 5. Check Pretty Printing
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
