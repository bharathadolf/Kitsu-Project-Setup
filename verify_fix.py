
import sys
import os

# Add current dir to path
sys.path.append(os.getcwd())

from PySide6.QtWidgets import QApplication
from project_ingester.ui.app import MainWindow

def test_startup():
    print("Initializing Application...")
    app = QApplication(sys.argv)
    
    # This triggers setup_ui -> apply_template -> add_node -> HybridNodeContainer.__init__
    # If the NameError persists, it will crash here.
    try:
        window = MainWindow()
        print("MainWindow created successfully.")
        print("Verification Passed: No NameError during initialization.")
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_startup()
