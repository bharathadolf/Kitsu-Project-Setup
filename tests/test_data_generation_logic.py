
import sys
import os
import json

# Add project root path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.core.setup import ProjectManager
from project_ingester.ui.tree import HybridNodeContainer
from project_ingester.ui.forms import EntityForm # Just for imports if needed, but we mock widgets

# Mock Classes to simulate UI
class MockNodeFrame:
    def __init__(self, node_type, names, properties=None):
        self.node_type = node_type
        self.properties = properties or {}
        self.properties["name"] = names
        self.node_id = "mock_id"

class MockWidget:
    def __init__(self, node_type, name, properties=None):
        self.node_frame = MockNodeFrame(node_type, name, properties)

class MockTreeItem:
    def __init__(self, widget):
        self.widget = widget
        self.children = []
        self.parent_item = None
        
    def addChild(self, item):
        self.children.append(item)
        item.parent_item = self
        
    def childCount(self):
        return len(self.children)
        
    def child(self, i):
        return self.children[i]
        
    def parent(self):
        return self.parent_item

class MockTreeWidget:
    def itemWidget(self, item, column):
        return item.widget

def run_test():
    print(" [TEST] Starting Data Generation Logic Test...")
    
    # 1. Setup Mock Hierarchy
    # Project (TV)
    #   -> Episode 1
    #       -> Sequence 1
    #           -> Shot 1
    #   -> Assets
    #       -> Asset Type (Characters)
    #           -> Asset (Hero)
    
    # Root: Project
    proj_props = {
        "production_type": "tv", 
        "production_style": "2d3d", 
        "root_path": "X:/Projects",
        "description": "Test TV Project"
    }
    proj_widget = MockWidget("project", "TestProject", proj_props)
    root_item = MockTreeItem(proj_widget)
    
    # Child 1: Episode
    ep_widget = MockWidget("episode", "Episode 01")
    ep_item = MockTreeItem(ep_widget)
    root_item.addChild(ep_item)
    
    # Child 1.1: Sequence
    seq_widget = MockWidget("sequence", "SQ010")
    seq_item = MockTreeItem(seq_widget)
    ep_item.addChild(seq_item)
    
    # Child 1.1.1: Shot
    shot_props = {"frame_in": 1001, "frame_out": 1050, "nb_frames": 50}
    shot_widget = MockWidget("shot", "SH010", shot_props)
    shot_item = MockTreeItem(shot_widget)
    seq_item.addChild(shot_item)
    
    # Child 2: Asset Type
    at_widget = MockWidget("asset_type", "Characters")
    at_item = MockTreeItem(at_widget)
    root_item.addChild(at_item)
    
    # Child 2.1: Asset
    ast_widget = MockWidget("asset", "HeroChar")
    ast_item = MockTreeItem(ast_widget)
    at_item.addChild(ast_item)
    
    mock_tree = MockTreeWidget()
    
    manager = ProjectManager(log_callback=lambda m, l: print(f"[{l}] {m}"))
    
    print("\n [TEST] Building Plan with Hierarchy...")
    plan = manager.build_plan(root_item, mock_tree, hierarchy=True)
    
    print(f"\n [TEST] Plan Built. Steps: {len(plan)}")
    
    # Validation
    for step in plan:
        print(f"\n--- Checking {step['type'].upper()}: {step['name']} ---")
        params = step['params']
        data = params.get('data')
        
        if step['type'] == 'asset_type':
            if data is not None:
                print(" [FAILED] Asset Type should NOT have data parameter.")
            else:
                 print(" [PASS] Asset Type has no data parameter.")
            continue
            
        if not data:
            print(f" [FAILED] Missing 'data' parameter for {step['type']}")
            continue
            
        print(f" [INFO] Data Keys: {list(data.keys())}")
        
        # Check specific paths
        if step['type'] == 'project':
             if data.get('production_type') == 'tv': print(" [PASS] Production Type Correct")
             if 'project_tree' in data: print(" [PASS] Project Tree Present")
             
        elif step['type'] == 'episode':
             if data.get('parent_type') == 'project': print(" [PASS] Parent Type Correct")
             if 'episode_tree' in data: print(" [PASS] Episode Tree Present")
             if data.get('project_path') == "X:/Projects/testproject": print(f" [PASS] Inherited Project Path: {data.get('project_path')}")
             else: print(f" [FAIL] Project Path: {data.get('project_path')}")
             
        elif step['type'] == 'sequence':
             if data.get('parent_type') == 'episode': print(" [PASS] Parent Type Correct")
             if 'sequence_tree' in data: print(" [PASS] Sequence Tree Present")
        elif step['type'] == 'sequence':
             if data.get('parent_type') == 'episode': print(" [PASS] Parent Type Correct")
             if 'sequence_tree' in data: print(" [PASS] Sequence Tree Present")
             if data.get('sequence_code') == 'sq010': print(" [PASS] Sequence Code is name.lower(): sq010")
             else: print(f" [FAIL] Sequence Code: {data.get('sequence_code')}")
             
        elif step['type'] == 'shot':
             # code param is 'seq_sh01', but data['shot_code'] is 'sh010'
             if data.get('shot_code') == 'sh010': print(" [PASS] Shot Code is name.lower(): sh010")
             else: print(f" [FAIL] Data Shot Code: {data.get('shot_code')}")
             
        elif step['type'] == 'asset':
             if data.get('asset_type') == 'characters': print(" [PASS] Asset Type Context Correct")
             if 'asset_tree' in data: print(" [PASS] Asset Tree Present")
             if "assets/characters/herochar" in data.get('asset_path', ''): print(f" [PASS] Asset Path: {data.get('asset_path')}")
             else: print(f" [FAIL] Asset Path: {data.get('asset_path')}")

if __name__ == "__main__":
    run_test()
