import sys
import os

# Put package on path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project_ingester.utils.compat import *
from project_ingester.ui.dialogs_builder import FolderBuilderDialog

# Mock RULE_MAP if needed, or rely on actual
# We will just run the dialog

def main():
    app = QApplication(sys.argv)
    
    dialog = FolderBuilderDialog()
    if dialog.exec_():
        print("Result Data:")
        import json
        print(json.dumps(dialog.result_data, indent=2))
    else:
        print("Dialog Cancelled")
        
    sys.exit()

if __name__ == "__main__":
    main()
