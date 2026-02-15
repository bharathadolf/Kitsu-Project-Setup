import sys
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTreeWidget, QTreeWidgetItem, QMainWindow, QDockWidget
)
from PySide2.QtCore import Qt, Signal, QTimer

# --- MOCK CONSTANTS ---
TYPE_ROOT = 0
TYPE_PROJECT = 1
TYPE_SEQUENCE = 2
TYPE_SHOT = 3
TYPE_ASSET_TYPE = 4
TYPE_ASSET = 5

# --- COPIED BreadcrumbWidget ---
class BreadcrumbWidget(QWidget):
    """Minimalist Apple-inspired breadcrumb navigation widget with clickable segments"""
    
    # Entity type colors for differentiation
    ENTITY_COLORS = {
        TYPE_ROOT: "#888888",       # Gray
        TYPE_PROJECT: "#4da6ff",    # Blue
        TYPE_SEQUENCE: "#45b7d1",   # Cyan
        TYPE_SHOT: "#f9ca24",       # Yellow
        TYPE_ASSET_TYPE: "#ff6b6b", # Red
        TYPE_ASSET: "#95e1d3",      # Mint
    }
    
    def __init__(self, parent=None):
        super(BreadcrumbWidget, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Crumbs Container (Directly on layout now, no nav buttons)
        self.crumbs_widget = QWidget()
        self.crumbs_layout = QHBoxLayout(self.crumbs_widget)
        self.crumbs_layout.setContentsMargins(0, 0, 0, 0)
        self.crumbs_layout.setSpacing(0)
        
        self.layout.addWidget(self.crumbs_widget)
        self.layout.addStretch()
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        
        self.segments = []
        self.path_items = []  # Store tree items for navigation
        self.click_callback = None
        self.active_index_state = -1 # Store current active index
        self.setFixedHeight(24)
    
    def set_click_callback(self, callback):
        """Set callback function for breadcrumb segment click"""
        self.click_callback = callback
    
    def _on_segment_clicked(self, index):
        """Handle breadcrumb segment click for navigation"""
        print(f"DEBUG: Segment clicked at index {index}")
        if self.click_callback and index < len(self.path_items):
            self.click_callback(self.path_items[index])

    def update_active_index(self, active_index):
        """
        Efficiently update the styling of existing segments based on the new active index.
        Matches the logic of set_path but without destroying widgets.
        """
        self.active_index_state = active_index
        print(f"DEBUG: Updating active index to {active_index}")

        for i, segment in enumerate(self.segments):
            btn = segment['button']
            
            # Recalculate entity color (safely)
            entity_type = None
            if i < len(self.path_items):
                entity_type = self.path_items[i].data(0, Qt.UserRole + 1)
            
            entity_color = self.ENTITY_COLORS.get(entity_type, "#aaaaaa")
            
            # Styling Logic
            is_active = (i == active_index)
            is_ghost = (i > active_index)
            # Parent condition implicitly handled by 'else'
            
            style = ""
            if is_active:
                style = f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {entity_color};
                        border: none;
                        border-bottom: 2px solid {entity_color};
                        border-radius: 0px;
                        padding: 2px 4px;
                        font-size: 9px;
                        font-weight: 700;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    }}
                    QPushButton:hover {{
                        color: #ffffff;
                    }}
                """
            elif is_ghost:
                style = f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {entity_color};
                        opacity: 0.5;
                        border: none;
                        border-bottom: 1px dotted {entity_color};
                        border-radius: 0px;
                        padding: 2px 4px;
                        font-size: 9px;
                        font-weight: 300;
                        font-style: italic;
                    }}
                    QPushButton:hover {{
                        color: {entity_color};
                        opacity: 1.0;
                        border-bottom: 1px solid {entity_color};
                    }}
                """
            else: # Parent
                 style = f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {entity_color};
                        opacity: 0.8;
                        border: none;
                        border-bottom: 2px solid transparent;
                        border-radius: 0px;
                        padding: 2px 4px;
                        font-size: 9px;
                        font-weight: 400;
                    }}
                    QPushButton:hover {{
                        color: {entity_color};
                        opacity: 1.0;
                        border-bottom: 2px solid {entity_color};
                    }}
                """
            
            btn.setStyleSheet(style)
            # No need to update text or reconnect signals

    
    def set_path(self, path_parts, tree_items=None, active_index=-1):
        """Update breadcrumb with new path segments"""
        print(f"DEBUG: set_path called. Parts: {path_parts}, Active Index: {active_index}")
        
        # Clear existing segments from crumbs layout
        while self.crumbs_layout.count():
             item = self.crumbs_layout.takeAt(0)
             if item.widget():
                 item.widget().deleteLater()
        
        self.segments = []
        
        if not path_parts:
            return
        
        # Store tree items for navigation
        self.path_items = tree_items if tree_items else []
        
        if active_index == -1:
            active_index = len(path_parts) - 1
            
        self.active_index_state = active_index

        # Create new segments with entity type colors
        for i, part in enumerate(path_parts):
            # Create button for segment
            btn = QPushButton(part)
            btn.setFlat(True)
            btn.setCursor(Qt.PointingHandCursor)
            
            self.crumbs_layout.addWidget(btn)
            
            # Create separator (except for last item)
            if i < len(path_parts) - 1:
                separator = QLabel("⫸")
                separator.setStyleSheet("color: #444; font-size: 10px; font-weight: 300; padding: 0px 3px;")
                self.crumbs_layout.addWidget(separator)
            
            self.segments.append({
                'button': btn,
                'text': part
            })
            
            # Connect click handler with captured index
            btn.clicked.connect(lambda checked=False, idx=i: self._on_segment_clicked(idx))
            
        # Apply initial styling using the update method to avoid duplication
        self.update_active_index(active_index)

# --- MOCK Main Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Breadcrumb Test")
        self.resize(800, 600)
        
        # Central Widget (Tree)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Entities")
        self.setCentralWidget(self.tree)
        
        # Horizontal Dock
        self.h_dock = QDockWidget("Horizontal Dock", self)
        self.h_dock_contents = QWidget()
        self.h_layout = QVBoxLayout(self.h_dock_contents)
        self.h_dock.setWidget(self.h_dock_contents)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.h_dock)
        
        # Breadcrumb
        self.breadcrumb_widget = BreadcrumbWidget()
        self.h_layout.addWidget(self.breadcrumb_widget)
        self.breadcrumb_widget.set_click_callback(self.on_breadcrumb_navigate)
        
        # Log Label
        self.log_label = QLabel("Log will appear here")
        self.h_layout.addWidget(self.log_label)
        
        # Data
        self.deepest_path_items = []
        self.populate_tree()
        
        self.tree.itemClicked.connect(self.on_tree_item_clicked)
        
    def populate_tree(self):
        # Create hierarchy: Project -> Sequence -> Shot
        root = self.tree.invisibleRootItem()
        
        proj = QTreeWidgetItem(root)
        proj.setText(0, "MyProject")
        proj.setData(0, Qt.UserRole + 1, TYPE_PROJECT)
        
        seq = QTreeWidgetItem(proj)
        seq.setText(0, "Sequence_001")
        seq.setData(0, Qt.UserRole + 1, TYPE_SEQUENCE)
        
        shot = QTreeWidgetItem(seq)
        shot.setText(0, "Shot_010")
        shot.setData(0, Qt.UserRole + 1, TYPE_SHOT)
        
        self.tree.expandAll()
        
    def log_console(self, msg, level="info"):
        print(f"LOG [{level}]: {msg}")
        self.log_label.setText(msg)

    # --- THE LOGIC TO TEST ---
    def on_breadcrumb_navigate(self, tree_item):
        """Handle breadcrumb segment click - update context WITHOUT changing tree selection"""
        if not tree_item: 
            return
        
        # Find index in deepest path
        try:
            index = self.deepest_path_items.index(tree_item)
            entity_name = tree_item.text(0)
            self.log_console(f"Navigating to breadcrumb: {entity_name} (Index {index})", "info")
            QApplication.processEvents()
        except ValueError:
            self.log_console("Error: Breadcrumb item not found in current path", "error")
            return 
            
        # Update styling using the efficient method
        self.breadcrumb_widget.update_active_index(index)
        
        # Update Context (Horizontal Dock)
        self.log_console(f"Context Updated for: {tree_item.text(0)}")


    def on_tree_item_clicked(self, item, column):
        """Handle tree item click - BUILD breadcrumb structure only"""
        # Build path with tree items
        current_path_items = []
        curr = item
        while curr:
            current_path_items.insert(0, curr)
            curr = curr.parent()
        
        # Strict 1:1 Navigation (No Ghost Paths)
        # Always update deepest/current path to exactly what is selected
        self.deepest_path_items = list(current_path_items)
        active_index = len(current_path_items) - 1
             
        # Update Horizontal Dock with stylized breadcrumb (Visuals Only)
        path_names = [i.text(0) for i in self.deepest_path_items]
        self.breadcrumb_widget.set_path(path_names, self.deepest_path_items, active_index)
            
        # TRIGGER CONTEXT UPDATE for the selected item (last in path)
        self.log_console(f"Context Updated for: {item.text(0)}")


    def run_test_scenario(self):
        print("\n--- STARTING AUTOMATED TEST ---")
        
        # 1. Simulate selecting the Shot (Deepest)
        print("1. Selecting Shot (Deepest Item)...")
        # Find the items
        root = self.tree.invisibleRootItem()
        project_item = root.child(0)
        sequence_item = project_item.child(0)
        shot_item = sequence_item.child(0)
        
        self.on_tree_item_clicked(shot_item, 0)
        
        # 2. Find the Project button in breadcrumb
        project_btn = self.breadcrumb_widget.segments[0]['button']
        print(f"2. Clicking 'Project' Breadcrumb: {project_btn.text()}")
        
        # Simulate Click
        project_btn.click()
        
        # 3. Verify Result
        print("3. Verifying Results...")
        
        QApplication.processEvents() # Ensure styling updates

        # Check styles
        style_0 = self.breadcrumb_widget.segments[0]['button'].styleSheet()
        style_1 = self.breadcrumb_widget.segments[1]['button'].styleSheet()
        
        is_proj_active = "border-bottom: 2px solid" in style_0
        is_seq_ghost = "opacity: 0.5" in style_1
        
        print(f"   Project Active? {is_proj_active}")
        print(f"   Sequence Ghost? {is_seq_ghost}")

        # Check log
        log_text = self.log_label.text()
        print(f"   Log Text: {log_text}")
        
        if is_proj_active and is_seq_ghost and "Context Updated for: MyProject" in log_text:
            print("TEST PASSED: Breadcrumb updated correctly.") # Avoid emoji
        else:
            print("TEST FAILED: Breadcrumb did not update styling.")
            print(f"   Style 0: {style_0}")
            
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Run test after 1 second
    QTimer.singleShot(1000, window.run_test_scenario)
    
    window.show()
    sys.exit(app.exec_())
