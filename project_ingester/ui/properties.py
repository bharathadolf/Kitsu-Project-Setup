from datetime import datetime
from ..utils.compat import *
from ..config import *
from .forms import FORM_MAP, EntityForm

class PropertiesWidget(QWidget):
    log_message = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__()
        self.current_node_frame = None
        self.current_form = None # Keep reference to prevent GC if needed, though layout holds widgets
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.header = QLabel("Properties Panel")
        self.header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.header)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0,0,0,0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.content_widget)
        
        layout.addWidget(self.scroll)

        # Initial empty widget
        self.setStyleSheet("") # Will be set by set_theme
        
    def set_theme(self, theme):
        self.header.setStyleSheet(theme.get_header_style('#68217a'))
        self.setStyleSheet(theme.property_panel_style)
        
    def load_nodes(self, node_frames):
        if not isinstance(node_frames, list):
             node_frames = [node_frames] if node_frames else []
        
        # Clear previous content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not node_frames:
            return

        # Always use tabs as per user request
        tab_widget = QtWidgets.QTabWidget()
        self.content_layout.addWidget(tab_widget)
        
        for node_frame in node_frames:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            self._populate_form(page_layout, node_frame)
            
            title = node_frame.properties.get("name", node_frame.node_type)
            
            # Use functional static tab names as approved
            TAB_TITLES = {
                "project": "Project Settings",
                "episode": "Episode Attributes",
                "sequence": "Sequence Config",
                "shot": "Shot Metadata",
                "asset_type": "Type Definition",
                "asset": "Asset Details"
            }
            title = TAB_TITLES.get(node_frame.node_type, title)
            
            tab_widget.addTab(page, title)

    def _populate_form(self, container_layout, node_frame):
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(5, 5, 5, 5)
        form_layout.setSpacing(5)
        
        # Instantiate correct form
        form_class = FORM_MAP.get(node_frame.node_type, EntityForm)
        form_instance = form_class(node_frame)
        form_instance.log_change.connect(self.log_message.emit)
        form_instance.setup_ui(form_layout)
        
        container_layout.addWidget(form_widget)
        container_layout.addStretch()

    def browse_path(self, line_edit, mode="file"):
         # Keeping this helper might be useful for other forms if referenced, 
         # but if it was only for custom attributes, we can remove it.
         # The new forms.py has its own browsing logic.
         # So we can remove this if sure.
         pass
         
    # All other custom attribute methods removed.
