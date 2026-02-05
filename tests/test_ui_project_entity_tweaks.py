import sys
import os

# Add project root to sys.path so we can import 'project_ingester'
# Assumes this file is in <project_root>/tests/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import *
from project_ingester.ui.app import MainWindow

def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    # Use Fusion for consistent look during test
    app.setStyle("Fusion")
        
    window = MainWindow()
    window.resize(1400, 800) # Ensure it's large enough
    window.show()
    
    # --- Test Logic: Auto-select Project Node ---
    print("[TEST] Attempting to auto-select Project node...")
    
    # Access the tree widget
    # structure: window -> project_panel -> tree
    if hasattr(window, 'project_panel') and hasattr(window.project_panel, 'tree'):
        tree = window.project_panel.tree
        
        # Get the root item (Project)
        root_item = tree.topLevelItem(0)
        
        if root_item:
            # Get the custom widget inside the item (HybridNodeContainer)
            container = tree.itemWidget(root_item, 0)
            
            if container and hasattr(container, 'node_frame'):
                print(f"[TEST] Found Root Node: {container.node_frame.properties.get('name')}")
                
                # Use the project_panel's selection method to ensure signals fire
                window.project_panel.select_node(container.node_frame)
                print("[TEST] Project Node Selected.")
            else:
                print("[TEST] ERROR: Could not find node_frame in root item widget.")
        else:
            print("[TEST] ERROR: No root item found in tree.")
    else:
        print("[TEST] ERROR: Could not access project_panel or tree.")

    # --- End Test Logic ---

    # --- Debug Timer ---
    def print_props():
        if hasattr(window, 'project_panel'):
            tree = window.project_panel.tree
            root_item = tree.topLevelItem(0)
            if root_item:
                container = tree.itemWidget(root_item, 0)
                if container:
                    props = container.node_frame.properties
                    print(f"[DEBUG] Validating Data: {props.get('data')}")

    timer = QtCore.QTimer()
    timer.timeout.connect(print_props)
    # timer.start(5000) # Disabled to reduce spam as per user feedback

    if QT_VERSION == 6:
        sys.exit(app.exec())
    else:
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
