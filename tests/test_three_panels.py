
import sys
import os

# Ensure project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QDockWidget, QFrame, QLabel, Qt, QTimer, QT_VERSION, QTabWidget
)

# Import our new widget
from project_ingester.ui.widgets.project_hierarchy import ProjectHierarchyWidget

class PanelWidget(QFrame):
    def __init__(self, text, color, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"background-color: {color};")
        
        # Main layout
        self.layout = QVBoxLayout(self)
        
        # Center label
        self.center_label = QLabel(text)
        self.center_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.center_label)
        
        # Size label at the bottom
        self.size_label = QLabel()
        self.size_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self.size_label.setStyleSheet("color: black; font-weight: bold;")
        self.layout.addWidget(self.size_label)

    def resizeEvent(self, event):
        # Update the size label whenever the widget is resized
        size = event.size()
        self.size_label.setText(f"Size: {size.width()} x {size.height()}")
        super().resizeEvent(event)

class ThreePanelWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Three Panel Dockable Window")
        
        # Central widget (hidden/empty for this layout)
        central_widget = QWidget()
        central_widget.hide() 
        self.setCentralWidget(central_widget)
        
        # Enable dock nesting to allow complex layouts
        self.setDockNestingEnabled(True)

        # Panel 1
        self.dock1 = QDockWidget("Panel 1", self)
        self.dock1.setAllowedAreas(Qt.AllDockWidgetAreas)
        
        # Panel 1 Content: Tab Widget
        self.panel1_tabs = QTabWidget()
        self.dock1.setWidget(self.panel1_tabs)
        
        # Tab 1: Project Hierarchy
        self.project_hierarchy = ProjectHierarchyWidget()
        self.panel1_tabs.addTab(self.project_hierarchy, "Projects")
        
        # Tab 2: Placeholder
        self.tab2 = PanelWidget("Tab 2 Content", "#E0E0E0")
        self.panel1_tabs.addTab(self.tab2, "Tab 2")
        
        # Tab 3: Placeholder
        self.tab3 = PanelWidget("Tab 3 Content", "#D0D0D0")
        self.panel1_tabs.addTab(self.tab3, "Tab 3")
        
        self.addDockWidget(Qt.TopDockWidgetArea, self.dock1)

        # Panel 2
        self.dock2 = QDockWidget("Panel 2", self)
        self.dock2.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.panel2 = PanelWidget("Panel 2", "#C0C0C0")
        self.dock2.setWidget(self.panel2)
        
        self.splitDockWidget(self.dock1, self.dock2, Qt.Horizontal)

        # Panel 3
        self.dock3 = QDockWidget("Panel 3", self)
        self.dock3.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.panel3 = PanelWidget("Panel 3", "#A0A0A0")
        self.dock3.setWidget(self.panel3)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock3)

        # Apply initial layout after the event loop starts
        QTimer.singleShot(0, self.apply_initial_layout)

    def apply_initial_layout(self):
        # Requested Content Dimensions:
        # P1: 251 x 424
        # P2: 1021 x 424
        # P3: 1276 x 285
        
        # Total Window Content:
        # Width: 251 + 1021 = 1272
        # Height: 424 + 285 = 709
        
        # We need to account for separators and frame borders.
        # Let's approximate and then rely on strict constraints to distribute space.
        # Adding a bit of extra connection space for separators.
        win_w = 1272 + 20
        win_h = 709 + 40 
        self.resize(win_w, win_h)

        # Step 1: Force heights (Vertical Split) using constraints
        # Top area (dock1 & dock2) vs Bottom area (dock3)
        # We temporarily set min/max constraints to force the layout engine's hand.
        
        self.dock1.setMinimumHeight(424)
        self.dock2.setMinimumHeight(424)
        self.dock3.setMinimumHeight(285)
        
        # Also force widths for the horizontal split
        self.dock1.setMinimumWidth(251)
        self.dock1.setMaximumWidth(251) 
        
        # We process events to let the layout engine apply these constraints
        QApplication.processEvents()

        # Step 2: Release constraints to allow resizing
        # We perform this in a subsequent timer to ensure the first layout pass completes.
        QTimer.singleShot(100, self.release_constraints)

    def release_constraints(self):
        # Reset min/max to defaults (0 and QWIDGETSIZE_MAX)
        self.dock1.setMinimumSize(0, 0)
        self.dock1.setMaximumSize(16777215, 16777215)
        
        self.dock2.setMinimumSize(0, 0)
        self.dock2.setMaximumSize(16777215, 16777215)
        
        self.dock3.setMinimumSize(0, 0)
        self.dock3.setMaximumSize(16777215, 16777215)
        
        # One final nudge to the Horizontal split to be precise if the max width constraint didn't perfectly hold ratio
        # (Though max constraint usually does the job).
        self.resizeDocks([self.dock1, self.dock2], [251, 1021], Qt.Horizontal)

if __name__ == "__main__":
    app_instance = QApplication.instance()
    if not app_instance:
        app_instance = QApplication(sys.argv)
    
    window = ThreePanelWindow()
    window.show()
    
    try:
        if QT_VERSION == 6:
            sys.exit(app_instance.exec())
        else:
            sys.exit(app_instance.exec_())
    except SystemExit:
        pass
