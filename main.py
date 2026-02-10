import sys
import os

# Ensure package is found
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from project_ingester.utils.compat import *
from project_ingester.ui.app import MainWindow

try:
    import hou
    IS_HOUDINI = True
except ImportError:
    IS_HOUDINI = False
    hou = None

def main():
    # Helper to check if running in Houdini
    in_houdini = False
    if IS_HOUDINI:
        # Extra check because sometimes hou module exists but not in Full GUI
        if hasattr(hou, "ui") and hou.ui.isUIAvailable():
            in_houdini = True

    if in_houdini:
        if hasattr(hou.session, 'project_ingester_window'):
            win = hou.session.project_ingester_window
            if win and win.isVisible():
                win.raise_()
                win.activateWindow()
                return

        parent = hou.ui.mainQtWindow()
        # Use Fusion style for consistency if possible, though Houdini controls style
        # app = QApplication.instance()
        # if app: app.setStyle("Fusion") 

        window = MainWindow(parent)
        window.resize(1400, 800) # Ensure it's large enough
        window.show()
        window.setWindowTitle("Project Ingester")
        hou.session.project_ingester_window = window
    else:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        # Use Fusion for consistent look (matches test environment)
        app.setStyle("Fusion")
            
        window = MainWindow()
        window.resize(1400, 800) # Ensure it's large enough
        window.show()
        
        if QT_VERSION == 6:
            sys.exit(app.exec())
        else:
            sys.exit(app.exec_())

if __name__ == "__main__":
    main()
