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


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.console = None
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.current_theme = DARK_THEME
        self.setup_ui()
        self.apply_theme(self.current_theme)
        
    def setup_ui(self):
        self.setWindowTitle("Project Ingester")
        self.setGeometry(100, 100, 1019, 669)
        
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
        self.splitter.setSizes([307, 321, 371])
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
        connect_action = QAction("Connect", self)
        connect_action.triggered.connect(self.connect_kitsu)
        view_menu.addAction(connect_action)

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

    def connect_kitsu(self):
        if gazu is None:
            self.console.log("Gazu library not found. Please install 'gazu'.", "ERROR")
            self.status_light.setStyleSheet("background-color: #FF4444; border-radius: 10px; border: 2px solid #333;")
            self.status_light.setToolTip("Status: Error (Gazu Missing)")
            return

        self.console.log(f"Connecting to Kitsu at {KITSU_HOST}...", "INFO")
        try:
            gazu.set_host(KITSU_HOST)
            gazu.log_in(KITSU_EMAIL, KITSU_PASSWORD)
            
            self.console.log("✅ Login successful", "SUCCESS")
            # Green Light
            self.status_light.setStyleSheet("background-color: #00FF00; border-radius: 10px; border: 2px solid #333; box-shadow: 0 0 5px #00FF00;")
            self.status_light.setToolTip("Status: Connected to Kitsu")
            
        except Exception as e:
            self.console.log(f"❌ Connection failed: {str(e)}", "ERROR")
            self.status_light.setStyleSheet("background-color: #FF0000; border-radius: 10px; border: 2px solid #333;")
            self.status_light.setToolTip(f"Status: Connection Failed ({str(e)})")
