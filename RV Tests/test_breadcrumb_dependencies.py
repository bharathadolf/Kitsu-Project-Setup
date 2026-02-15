import sys
from PySide2.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTreeWidget, QTreeWidgetItem, QMainWindow, QDockWidget, QListWidget
)
from PySide2.QtCore import Qt, Signal, QTimer

# --- MOCK CONSTANTS ---
TYPE_ROOT = 0
TYPE_PROJECT = 1
TYPE_SEQUENCE = 2
TYPE_SHOT = 3
TYPE_ASSET_TYPE = 4
TYPE_ASSET = 5

# --- COPIED BreadcrumbWidget (Mocking the latest version) ---
class BreadcrumbWidget(QWidget):
    ENTITY_COLORS = {
        TYPE_ROOT: "#888888", TYPE_PROJECT: "#4da6ff", TYPE_SEQUENCE: "#45b7d1",
        TYPE_SHOT: "#f9ca24", TYPE_ASSET_TYPE: "#ff6b6b", TYPE_ASSET: "#95e1d3",
    }
    
    def __init__(self, parent=None):
        super(BreadcrumbWidget, self).__init__(parent)
        self.layout = QHBoxLayout(self)
        self.crumbs_widget = QWidget()
        self.crumbs_layout = QHBoxLayout(self.crumbs_widget)
        self.layout.addWidget(self.crumbs_widget)
        self.segments = []
        self.path_items = []
        self.active_index_state = -1

    def update_active_index(self, active_index):
        self.active_index_state = active_index
        print(f"DEBUG: Breadcrumb visuals updated. Active Index: {active_index}")
        # (Styling logic omitted for brevity in this specific dependency test)

    def _on_segment_clicked(self, index):
        # In the real class, this calls the callback
        if hasattr(self, 'click_callback') and self.click_callback:
            # We need to find the item. In the real class it uses self.path_items
            if index < len(self.path_items):
                item = self.path_items[index]
                self.click_callback(item)

    def set_path(self, path_parts, tree_items=None, active_index=-1):
        # Clear
        self.segments = []
        self.path_items = tree_items if tree_items else []
        
        # Rebuild (Simplified for test)
        for i, part in enumerate(path_parts):
            btn = QPushButton(part)
            # Simulating the connect
            # We need to manually bind the click for the mock test to work nicely
            btn.clicked.connect(lambda checked=False, idx=i: self._on_segment_clicked(idx))
            self.segments.append({'button': btn, 'text': part})

# --- CONTROLLER CLASS ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.deepest_path_items = []
        
        # UI Setup
        self.cw = QWidget()
        self.setCentralWidget(self.cw)
        self.layout = QVBoxLayout(self.cw)
        
        # Breadcrumb
        self.breadcrumb_widget = BreadcrumbWidget()
        self.breadcrumb_widget.click_callback = self.on_breadcrumb_navigate
        self.layout.addWidget(QLabel("Breadcrumb:"))
        self.layout.addWidget(self.breadcrumb_widget)
        
        # Status/Log
        self.log_label = QLabel("Log: Ready")
        self.layout.addWidget(self.log_label)
        
        # Mock List Widget (Dependent Operation)
        self.list_widget = QListWidget()
        self.layout.addWidget(QLabel("Dependent List (Sequences):"))
        self.layout.addWidget(self.list_widget)

    def log_console(self, msg, level="info"):
        print(f"LOG: {msg}")
        self.log_label.setText(msg)

    # --- THE CORE LOGIC TO TEST ---
    def set_breadcrumb_active_index(self, index):
        """
        Single Source of Truth: Update Highlighter -> Trigger Dependent Operations
        """
        print(f"\n--- set_breadcrumb_active_index({index}) called ---")
        if index < 0 or index >= len(self.deepest_path_items):
            return

        # 1. Update Highlighter Visuals
        self.breadcrumb_widget.update_active_index(index)
        QApplication.processEvents() 

        # 2. Trigger Dependencies (Context Update)
        active_item = self.deepest_path_items[index]
        self.update_horizontal_dock_context(active_item)
        
        # Log 
        self.log_console(f"Highlighter moved to: {active_item.text(0)} (Index {index})")

    def update_horizontal_dock_context(self, item):
        """Mock dependent operation"""
        entity_name = item.text(0)
        print(f"DEPENDENCY TRIGGERED: Updating List for context '{entity_name}'")
        
        self.list_widget.clear()
        self.list_widget.addItem(f"Sequences for {entity_name}...")
        self.list_widget.addItem("Seq_A")
        self.list_widget.addItem("Seq_B")

    def on_breadcrumb_navigate(self, tree_item):
        if not tree_item: return
        try:
            index = self.deepest_path_items.index(tree_item)
        except ValueError:
            return 
        
        # Use Centralized Method
        self.set_breadcrumb_active_index(index)

    def on_tree_item_clicked(self, item):
        # Build path
        current_path_items = []
        curr = item
        while curr:
            current_path_items.insert(0, curr)
            curr = curr.parent()
        
        self.deepest_path_items = list(current_path_items)
        active_index = len(current_path_items) - 1
             
        path_names = [i.text(0) for i in self.deepest_path_items]
        self.breadcrumb_widget.set_path(path_names, self.deepest_path_items, active_index)
        
        # TRIGGER CONTEXT UPDATE via Highlighter
        self.set_breadcrumb_active_index(active_index)

    # --- TEST RUNNER ---
    def run_test(self):
        print("=== TEST START: Verifying Dependency Chain ===")
        
        # Setup Mock Data
        root = QTreeWidgetItem()
        root.setText(0, "ROOT")
        
        proj = QTreeWidgetItem(root)
        proj.setText(0, "Project_X")
        proj.setData(0, Qt.UserRole + 1, TYPE_PROJECT)
        
        seq = QTreeWidgetItem(proj)
        seq.setText(0, "Sequence_Y")
        seq.setData(0, Qt.UserRole + 1, TYPE_SEQUENCE)
        
        shot = QTreeWidgetItem(seq)
        shot.setText(0, "Shot_Z")
        shot.setData(0, Qt.UserRole + 1, TYPE_SHOT)
        
        # 1. TEST TREE SELECTION
        print("\n[Action] User selects 'Shot_Z' in Tree.")
        self.on_tree_item_clicked(shot)
        
        # Check assertions
        if "Sequences for Shot_Z..." in [self.list_widget.item(i).text() for i in range(self.list_widget.count())]:
             print("CHECK 1 PASSED: Tree selection triggered context for Shot_Z")
        else:
             print("CHECK 1 FAILED: Context not updated for Shot_Z")

        # 2. TEST BREADCRUMB NAVIGATION
        print("\n[Action] User clicks 'Project_X' in Breadcrumb.")
        # Find index 0 item (Project)
        # Note: self.breadcrumb_widget.segments contains our buttons needed to simulate click
        btn = self.breadcrumb_widget.segments[1]['button'] # ROOT is 0, Proj is 1? No, logic above:
        # on_tree_item_clicked builds items: [ROOT, Proj, Seq, Shot]
        
        # Let's print the segments to be sure
        print(f"Segments: {[s['text'] for s in self.breadcrumb_widget.segments]}")
        
        # Click Project_X (Index 1)
        btn = self.breadcrumb_widget.segments[1]['button']
        btn.click()
        
        # Check assertions
        # 1. Active Index should be 1
        is_index_correct = (self.breadcrumb_widget.active_index_state == 1)
        # 2. List widget should show Project sequences
        list_content = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        is_context_correct = "Sequences for Project_X..." in list_content
        # 3. Log should update
        is_log_correct = "Highlighter moved to: Project_X" in self.log_label.text()

        print(f"CHECK 2A (Highlighter Index): {'PASSED' if is_index_correct else 'FAILED'}")
        print(f"CHECK 2B (Context Update):    {'PASSED' if is_context_correct else 'FAILED'}")
        print(f"CHECK 2C (Log Message):       {'PASSED' if is_log_correct else 'FAILED'}")
        
        if is_index_correct and is_context_correct and is_log_correct:
            print("\n[OK] MAIN TEST PASSED: Operations are driven by Breadcrumb Item.")
        else:
            print("\n[FAIL] MAIN TEST FAILED.")

        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    QTimer.singleShot(500, window.run_test)
    app.exec_()
