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
    if IS_HOUDINI:
        if hasattr(hou.session, 'project_ingester_window'):
            win = hou.session.project_ingester_window
            if win and win.isVisible():
                win.raise_()
                win.activateWindow()
                return

        parent = hou.ui.mainQtWindow()
        window = MainWindow(parent)
        window.show()
        window.setWindowTitle("ProjectIngesterApp")
        hou.session.project_ingester_window = window
    else:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        window = MainWindow()
        window.show()
        
        if QT_VERSION == 6:
            sys.exit(app.exec())
        else:
            sys.exit(app.exec_())

if __name__ == "__main__":
    main()
