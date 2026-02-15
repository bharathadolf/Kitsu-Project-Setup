from ..utils.compat import *
from ..data.rules import RULE_MAP
from .tree import VisualTree, ProjectStructureWidget
from .properties import PropertiesWidget
from .console import ConsoleWidget

# We need to implement ProjectStructureWidget inside tree.py or here?
# In original code it was separate. Let's assume it was migrated to tree.py or add it here if missing.
# Checking tree.py content... I might have missed ProjectStructureWidget in tree.py.
# Wait, I see VisualTree in tree.py, but ProjectStructureWidget wrapper logic needs to be there too.
# I will add ProjectStructureWidget to tree.py via append/edit if I forgot it, 
# OR I can define it here if it's small, but better in tree.py.
# Let's check what I wrote to tree.py.
# I wrote NodeFrame, HybridNodeContainer, VisualTree. 
# I MISSED ProjectStructureWidget! I must add it to tree.py first.

# UPDATE: I'll write a separate file or append to tree.py. 
# Appending to tree.py is cleaner as they are coupled. 
# But for now, let's create app.py assuming it exists, and I will fix tree.py in next step.

from .themes import DARK_THEME, get_next_theme
from ..kitsu_config import gazu, KITSU_HOST, KITSU_EMAIL, KITSU_PASSWORD
from ..core.loader import ProjectLoader
from .dialogs import EntityViewerDialog


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.console = None
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.current_theme = DARK_THEME
        self.setup_ui()
        self.loader = ProjectLoader(log_callback=self.console.log)
        self.apply_theme(self.current_theme)
        
    def setup_ui(self):
        self.setWindowTitle("Project Ingester")
        self.setGeometry(100, 100, 908, 534)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.project_panel = ProjectStructureWidget()
        self.properties_panel = PropertiesWidget()
        
        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(0)
        
        self.console_header = QLabel("Console Log")
        self.console_header.setAlignment(Qt.AlignCenter)
        console_layout.addWidget(self.console_header)
        
        self.console = ConsoleWidget()
        console_layout.addWidget(self.console)
        
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        clear_btn = QPushButton("Clear Console")
        clear_btn.clicked.connect(self.clear_console)
        
        controls_layout.addWidget(clear_btn)
        controls_layout.addStretch()
        console_layout.addWidget(controls_widget)
        
        self.splitter.addWidget(self.project_panel)
        self.splitter.addWidget(self.properties_panel)
        self.splitter.addWidget(console_container)
        self.splitter.setSizes([286, 270, 334])
        self.splitter.setChildrenCollapsible(True)
        self.splitter.splitterMoved.connect(self.update_panel_sizes)
        main_layout.addWidget(self.splitter)
        
        self.create_menu_bar()
        self.status_bar = QtWidgets.QStatusBar()
        self.status_bar.showMessage(f"PySide{QT_VERSION} - Ready")
        self.setStatusBar(self.status_bar)

        # Kitsu Status Light
        self.status_light = QLabel()
        self.status_light.setFixedSize(20, 20)
        self.status_light.setStyleSheet("background-color: #555555; border-radius: 10px; border: 2px solid #333;")
        self.status_light.setToolTip("Kitsu Connection Status: Not Connected")
        self.status_bar.addWidget(self.status_light)
        # Add some spacing
        spacer = QWidget()
        spacer.setFixedWidth(10)
        self.status_bar.addWidget(spacer)

        # Toggle Button
        self.theme_btn = QPushButton(f"Theme: {self.current_theme.name}")
        self.theme_btn.setFlat(True)
        self.theme_btn.setStyleSheet("text-align: left; padding-left: 10px; font-weight: bold;")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.status_bar.addWidget(self.theme_btn)

        # Add panel size label to status bar
        self.panel_size_label = QLabel("")
        self.panel_size_label.setStyleSheet("padding-right: 15px;")
        self.status_bar.addPermanentWidget(self.panel_size_label)

        # Add size label to status bar
        self.size_label = QLabel(f"{self.width()} x {self.height()}")
        self.size_label.setStyleSheet("padding-right: 10px;")
        self.status_bar.addPermanentWidget(self.size_label)
        
        self.update_panel_sizes()
        
        self.console.log("Application started successfully", "SUCCESS")
        self.apply_template("Custom")
        self.project_panel.node_selected.connect(self.properties_panel.load_nodes)
        self.project_panel.viewer_requested.connect(self.on_viewer_requested)
        
        self.project_panel.log_message.connect(self.console.log)
        self.properties_panel.log_message.connect(self.console.log)

    def toggle_theme(self):
        new_theme = get_next_theme(self.current_theme.name)
        self.apply_theme(new_theme)
        
    def apply_theme(self, theme):
        self.current_theme = theme
        self.setStyleSheet(theme.main_window_style)
        self.console_header.setStyleSheet(theme.get_header_style('#4caf50'))
        self.theme_btn.setText(f"Theme: {theme.name}")
        
        # Propagate to panels
        if hasattr(self.project_panel, 'set_theme'):
            self.project_panel.set_theme(theme)
        
        if hasattr(self.properties_panel, 'set_theme'):
            self.properties_panel.set_theme(theme)

    def apply_template(self, template_name):
        self.project_panel.apply_template(template_name)
        
    def create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = menubar.addMenu("View")
        template_menu = view_menu.addMenu("Template")
        for rule_name in RULE_MAP.keys():
            action = QAction(rule_name, self)
            action.triggered.connect(lambda checked=False, r=rule_name: self.apply_template(r))
            template_menu.addAction(action)

        view_menu.addSeparator()
        
        # Load Project Submenu
        self.load_project_menu = view_menu.addMenu("Load Project")
        self.load_project_menu.aboutToShow.connect(self.populate_projects_menu)

        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.connect_kitsu)
        view_menu.addAction(connect_action)

        # File Menu Extensions
        build_folder_action = QAction("Build from Folders...", self)
        build_folder_action.triggered.connect(self.open_folder_builder)
        file_menu.addAction(build_folder_action)

    def clear_console(self):
        self.console.clear()
        self.console.log("Console cleared", "INFO")

    def update_panel_sizes(self, pos=None, index=None):
        sizes = self.splitter.sizes()
        self.panel_size_label.setText(f"Panels: {sizes}")

    def resizeEvent(self, event):
        if hasattr(self, 'size_label'):
            self.size_label.setText(f"{self.width()} x {self.height()}")
        if hasattr(self, 'panel_size_label'):
            self.update_panel_sizes()
        super().resizeEvent(event)

    def closeEvent(self, event):
        # Houdini cleanup logic can be handled in main.py entry point or here
        event.accept()

    def showEvent(self, event):
        self.update_panel_sizes()
        super().showEvent(event)

    def connect_kitsu(self, *args):
        if gazu is None:
            self.console.log("Gazu library not found. Please install 'gazu'.", "ERROR")
            self.status_light.setStyleSheet("background-color: #FF4444; border-radius: 10px; border: 2px solid #333;")
            self.status_light.setToolTip("Status: Error (Gazu Missing)")
            return

        # Use loader's robust connect method which includes retry/UI dialog
        if self.loader.connect():
            # Green Light
            self.status_light.setStyleSheet("background-color: #00FF00; border-radius: 10px; border: 2px solid #55FF55;")
            self.status_light.setToolTip("Status: Connected to Kitsu")
        else:
            # Red Light
            # If user cancelled, we just stay disconnected. Status light reflects "Failed" or determines by loader logic?
            # Actually if connect() returns False because of user cancel, we probably shouldn't show RED if it was just "Not Connected".
            # But the user might want feedback. Let's keep it red for now or maybe yellow if cancelled?
            # loader.connect() returns False if failed OR cancelled.
            self.status_light.setStyleSheet("background-color: #FF0000; border-radius: 10px; border: 2px solid #333;")
            self.status_light.setToolTip("Status: Connection Failed or Cancelled")

    def populate_projects_menu(self):
        self.load_project_menu.clear()
        
        # Try to connect if not already
        if not self.loader.connect():
             action = QAction("Connect to Kitsu first", self)
             action.setEnabled(False)
             self.load_project_menu.addAction(action)
             return
             
        projects = self.loader.get_all_projects()
        if not projects:
             action = QAction("No projects found", self)
             action.setEnabled(False)
             self.load_project_menu.addAction(action)
             return

        for p in projects:
             action = QAction(p['name'], self)
             # Use default argument binding to capture loop variable
             action.triggered.connect(lambda checked=False, pid=p['id']: self.load_project_action(pid))
             self.load_project_menu.addAction(action)

    def load_project_action(self, project_id):
        self.console.log(f"Starting load for project ID: {project_id}...", "INFO")
        data = self.loader.load_full_project(project_id)
        if data:
             self.rebuild_tree_from_data(data)

    def rebuild_tree_from_data(self, data):
        self.project_panel.tree.clear()
        
        # 1. Update Watermark
        prod_type = data.get('production_type', 'TV Show') # Default
        self.project_panel.tree.watermark_text = prod_type
        self.project_panel.tree.viewport().update()
        
        # 2. Update Status
        p_name = data.get('properties', {}).get('name', 'Unknown')
        self.project_panel.status_label.setText(f"Project Loaded: {p_name}")
        
        # Root is project
        root_item = self.project_panel.add_node(None, "project", is_root=True)
        self._apply_properties_to_node(root_item, data, is_loaded=True)
        self.project_panel.tree.expandItem(root_item)
        
        self._recursive_build(root_item, data.get("children", []), is_loaded=True)
        self.console.log("Tree reconstruction complete.", "SUCCESS")

    def _recursive_build(self, parent_item, children_data, is_loaded=False):
        for child_data in children_data:
            node_type = child_data['type']
            new_item = self.project_panel.add_node(parent_item, node_type)
            self._apply_properties_to_node(new_item, child_data, is_loaded=is_loaded)
            
            # Recursion
            self._recursive_build(new_item, child_data.get("children", []), is_loaded=is_loaded)

    def _apply_properties_to_node(self, item, data, is_loaded=False):
        widget = self.project_panel.tree.itemWidget(item, 0)
        if widget and widget.node_frame:
             props = data.get("properties", {})
             
             # Set Loaded Flag
             widget.node_frame.is_loaded = is_loaded
             
             # Log all properties as requested
             name = props.get("name", "Unknown")
             type_ = data.get("type", "Unknown")
             
             self.console.log(f"Loading {type_}: {name}", "DEBUG")
             widget.node_frame.properties.update(props)
             
             # Also update visual name
             widget.node_frame.name_edit.setText(name)
             
             # Log parameters logic
             log_lines = []
             for k, v in props.items():
                  log_lines.append(f"  {k}: {v}")
             
             if log_lines:
                 self.console.log("\n".join(log_lines), "DEBUG")

    def on_viewer_requested(self, params, node_type):
        dialog = EntityViewerDialog(params, node_type, self)
        dialog.exec()

    def open_folder_builder(self):
        from .dialogs_builder import FolderBuilderDialog
        dialog = FolderBuilderDialog(self)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.console.log(f"Building tree from folder: {data.get('path')}", "INFO")
                # Apply the template chosen in dialog to ensure rules match
                # The dialog doesn't return template name directly in result_data usually, 
                # but we can infer it or pass it. 
                # Let's assume result_data is just the tree. 
                # Ideally we should switch the main window template to match.
                
                # For now, just populate.
                self.project_panel.populate_from_structure(data)
                self.console.log("Tree populated from folders.", "SUCCESS")

