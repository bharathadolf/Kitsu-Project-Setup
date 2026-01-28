from datetime import datetime
from ..utils.compat import *
from ..config import *

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super(CollapsibleBox, self).__init__(parent)
        self.toggle_button = QPushButton(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.setStyleSheet("text-align: left; font-weight: bold; background-color: #444; border: none; padding: 5px;")
        self.toggle_button.toggled.connect(self.on_toggled)
        
        self.content_area = QWidget()
        self.content_area.setVisible(False)
        self.content_layout = QFormLayout(self.content_area)
        self.content_layout.setContentsMargins(10, 5, 5, 5)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)
        
    def on_toggled(self, checked):
        self.toggle_button.setText(f"{'▼' if checked else '▶'} {self.toggle_button.text()[2:]}")
        self.content_area.setVisible(checked)
        
    def setText(self, text):
        self.toggle_button.setText(f"▶ {text}")

    def addRow(self, label, widget):
        self.content_layout.addRow(label, widget)

class EntityForm(QObject):
    """Base class for all entity forms."""
    def __init__(self, node_frame):
        super().__init__()
        self.node_frame = node_frame
        self.widgets = {}

    def setup_ui(self, layout):
        """Populates the layout with form fields."""
        self.layout = layout
        pass

    def add_row(self, label, widget):
        if isinstance(self.layout, QFormLayout):
            self.layout.addRow(label, widget)
        else:
            row = QWidget()
            h = QHBoxLayout(row)
            h.setContentsMargins(0,0,0,0)
            h.addWidget(QLabel(label))
            h.addWidget(widget)
            self.layout.addWidget(row)

    def on_prop_changed(self, key, value):
        self.node_frame.properties[key] = value

class ProjectForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # --- Mandatory Fields ---
        
        # Name
        name_input = QLineEdit(self.node_frame.properties.get("name", ""))
        name_input.textChanged.connect(lambda t: self.on_project_name_changed(t))
        layout.addRow("Name:", name_input)
        
        # Production Type
        # Check if derived from template (locked)
        is_custom = self.node_frame.properties.get("is_custom_template", True)
        
        type_combo = QComboBox()
        type_combo.addItems(["short", "featurefilm", "tvshow"])
        current_type = self.node_frame.properties.get("production_type", "short")
        if current_type not in ["short", "featurefilm", "tvshow"]: current_type = "short"
        type_combo.setCurrentText(current_type)
        
        if not is_custom:
            type_combo.setEnabled(False) 
            # Or use setReadOnly logic if QComboBox supports it (frame only), usually setEnabled(False) is clear it's locked.
        
        type_combo.currentTextChanged.connect(lambda t: self.on_prop_changed("production_type", t))
        layout.addRow("Type:", type_combo)

        # --- Optional Fields (Collapsible) ---
        
        collapsible = CollapsibleBox("Optional Properties")
        layout.addRow(collapsible)
        
        # FPS
        fps_spin = QSpinBox()
        fps_spin.setRange(1, 240)
        fps_spin.setValue(int(self.node_frame.properties.get("fps", 24)))
        fps_spin.valueChanged.connect(lambda v: self.on_prop_changed("fps", v))
        collapsible.addRow("FPS:", fps_spin)
        
        # Ratio
        ratio_edit = QLineEdit(str(self.node_frame.properties.get("ratio", "1.78")))
        ratio_edit.textChanged.connect(lambda t: self.on_prop_changed("ratio", t))
        collapsible.addRow("Ratio:", ratio_edit)
        
        # Resolution
        res_edit = QLineEdit(str(self.node_frame.properties.get("resolution", "1920x1080")))
        res_edit.textChanged.connect(lambda t: self.on_prop_changed("resolution", t))
        collapsible.addRow("Resolution:", res_edit)
        
        # Description
        desc_edit = QTextEdit()
        desc_edit.setPlainText(self.node_frame.properties.get("description", ""))
        desc_edit.setFixedHeight(60)
        desc_edit.textChanged.connect(lambda: self.on_prop_changed("description", desc_edit.toPlainText()))
        collapsible.addRow("Description:", desc_edit)
        
        # Has Avatar
        avatar_cb = QCheckBox()
        avatar_cb.setChecked(bool(self.node_frame.properties.get("has_avatar", False)))
        avatar_cb.toggled.connect(lambda c: self.on_prop_changed("has_avatar", c))
        collapsible.addRow("Has Avatar:", avatar_cb)

        # Force initial text set
        collapsible.setText("Optional Properties")
        
    def on_project_name_changed(self, text):
        self.node_frame.properties["name"] = text
        # Auto-generate code
        stripped = text.replace(" ", "").upper()
        code = stripped[:3] if len(stripped) >= 3 else stripped
        self.node_frame.properties["code"] = code

class EpisodeForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # Mandatory: Name
        name_input = QLineEdit(self.node_frame.properties.get("name", "Episode 1"))
        name_input.textChanged.connect(lambda t: self.on_prop_changed("name", t))
        layout.addRow("Name:", name_input)

class SequenceForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # Mandatory: Name
        name_input = QLineEdit(self.node_frame.properties.get("name", "SEQ_01"))
        name_input.textChanged.connect(lambda t: self.on_prop_changed("name", t))
        layout.addRow("Name:", name_input)

class ShotForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # Mandatory: Name
        name_input = QLineEdit(self.node_frame.properties.get("name", "SH_010"))
        name_input.textChanged.connect(lambda t: self.on_prop_changed("name", t))
        layout.addRow("Name:", name_input)
        
        # Optional
        collapsible = CollapsibleBox("Optional Properties")
        layout.addRow(collapsible)
        
        frame_in = QSpinBox()
        frame_in.setRange(-999999, 999999)
        frame_in.setValue(int(self.node_frame.properties.get("frame_in", 1001)))
        frame_in.valueChanged.connect(lambda v: self.on_prop_changed("frame_in", v))
        collapsible.addRow("Frame In:", frame_in)
        
        frame_out = QSpinBox()
        frame_out.setRange(-999999, 999999)
        frame_out.setValue(int(self.node_frame.properties.get("frame_out", 1100)))
        frame_out.valueChanged.connect(lambda v: self.on_prop_changed("frame_out", v))
        collapsible.addRow("Frame Out:", frame_out)
        
        nb_frames = QSpinBox()
        nb_frames.setRange(0, 999999)
        nb_frames.setValue(int(self.node_frame.properties.get("nb_frames", 100)))
        nb_frames.valueChanged.connect(lambda v: self.on_prop_changed("nb_frames", v))
        collapsible.addRow("Nb Frames:", nb_frames)
        
        desc_edit = QTextEdit()
        desc_edit.setPlainText(self.node_frame.properties.get("description", ""))
        desc_edit.setFixedHeight(60)
        desc_edit.textChanged.connect(lambda: self.on_prop_changed("description", desc_edit.toPlainText()))
        collapsible.addRow("Description:", desc_edit)
        
        collapsible.setText("Optional Properties")

class AssetTypeForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # Mandatory: Name
        name_input = QLineEdit(self.node_frame.properties.get("name", "Characters"))
        name_input.textChanged.connect(lambda t: self.on_prop_changed("name", t))
        layout.addRow("Name:", name_input)

class AssetForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # Mandatory: Name
        name_input = QLineEdit(self.node_frame.properties.get("name", "New Asset"))
        name_input.textChanged.connect(lambda t: self.on_prop_changed("name", t))
        layout.addRow("Name:", name_input)

FORM_MAP = {
    "project": ProjectForm,
    "episode": EpisodeForm,
    "sequence": SequenceForm,
    "shot": ShotForm,
    "asset_type": AssetTypeForm,
    "asset": AssetForm
}
