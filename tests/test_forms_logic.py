
import sys
import os

# Add project root path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import QApplication, QWidget, QFormLayout
from project_ingester.ui.forms import ProjectForm

# Mock NodeFrame
class MockNodeFrame:
    def __init__(self):
        self.node_type = "project"
        self.properties = {"name": "TestProject", "is_custom_template": True}
        self.node_id = "1"

def run_test():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    print(" [TEST] Starting ProjectForm Logic Test...")
    
    node_frame = MockNodeFrame()
    form = ProjectForm(node_frame)
    
    # Create a container widget to hold layout
    container = QWidget()
    layout = QFormLayout(container)
    form.setup_ui(layout)
    
    print(" [TEST] Simulating Root Path Change...")
    # Find root path edit
    # In setup_ui, self.root_path_edit is created
    form.root_path_edit.setText("Z:/NewRoot")
    
    # Check properties
    root_path_prop = node_frame.properties.get("root_path")
    data_prop = node_frame.properties.get("data", {})
    
    print(f" [CHECK] Properties['root_path']: {root_path_prop}")
    print(f" [CHECK] Properties['data']['root_path']: {data_prop.get('root_path')}")
    
    if root_path_prop == "Z:/NewRoot":
        print(" [PASS] root_path property updated correctly.")
    else:
        print(" [FAIL] root_path property NOT updated.")

    if data_prop.get('root_path') == "Z:/NewRoot":
        print(" [PASS] data.root_path updated correctly.")
    else:
        print(" [FAIL] data.root_path NOT updated.")

if __name__ == "__main__":
    run_test()
