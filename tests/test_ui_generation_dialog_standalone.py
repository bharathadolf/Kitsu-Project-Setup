import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import *
from project_ingester.ui.dialogs import GenerationSummaryDialog

class MockManager:
    def __init__(self):
        pass
        
    def execute_plan(self, plan):
        print("[MOCK] Executing Plan...")
        import time
        # Simulate work
        for step in plan:
            print(f"[MOCK] Processing {step['name']}...")
            # Simulate fetch results
            step['fetched_data'] = step['params'].copy()
            step['fetched_data'].update({
                "id": "mock-id-12345", 
                "created_at": "2023-01-01T12:00:00",
                "updated_at": "2023-01-01T12:00:00",
                "project_id": "mock-proj-id-999" # System param
            })
            
        print("[MOCK] Execution Complete. Data populated.")
        
class MockWidget:
    def __init__(self, item):
        self.item = item

def create_dummy_plan(tree):
    """
    Creates a plan with a hierarchy:
    Project
      └── Episode 1
            └── Sequence 1
                  └── Shot 1
    """
    # 1. Create Source Tree Items
    root_item = QTreeWidgetItem(tree)
    root_item.setText(0, "Project")
    
    ep_item = QTreeWidgetItem(root_item)
    ep_item.setText(0, "Episode 1")
    
    seq_item = QTreeWidgetItem(ep_item)
    seq_item.setText(0, "Sequence 1")
    
    shot_item = QTreeWidgetItem(seq_item)
    shot_item.setText(0, "Shot 1")
    
    mock_proj_widget = MockWidget(root_item)
    mock_ep_widget = MockWidget(ep_item)
    mock_seq_widget = MockWidget(seq_item)
    mock_shot_widget = MockWidget(shot_item)
    
    # 2. Create Steps
    # Note: setup.py usually puts ancestors first.
    
    plan = []
    
    # Project
    plan.append({
        "type": "project",
        "name": "MyProject",
        "params": {
             "name": "MyProject",
             "production_style": "3d",
             "project_id": "SHOULD_NOT_BE_HERE_BUT_LETS_TEST" 
        },
        "widget": mock_proj_widget,
        "role": "Context"
    })
    
    # Episode
    plan.append({
        "type": "episode",
        "name": "Ep01",
        "params": {"name": "Ep01", "project_id": "ignore"},
        "widget": mock_ep_widget,
        "role": "Child"
    })
    
    # Sequence
    plan.append({
        "type": "sequence",
        "name": "Seq01",
        "params": {"name": "Seq01", "project_id": "ignore"},
        "widget": mock_seq_widget,
        "role": "Child"
    })
    
    # Shot
    plan.append({
        "type": "shot",
        "name": "sh010",
        "params": {
            "name": "sh010",
            "project_id": "123456",  # This should be GREY (System)
            "frame_in": 1001,        # Core/Update
            "description": "Test Shot"
        },
        "widget": mock_shot_widget,
        "role": "Child"
    })
    
    return plan

def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # Need a dummy source tree for parent constraints to work in mocked items
    source_tree = QTreeWidget()
    
    print("[TEST] Building Mock Plan...")
    plan = create_dummy_plan(source_tree)
    
    print("[TEST] Launching Dialog with Mock Manager...")
    manager = MockManager()
    dialog = GenerationSummaryDialog(plan, manager=manager)
    
    # Show dialog
    dialog.exec_()
    
    print("[TEST] Dialog Closed.")

if __name__ == "__main__":
    main()
