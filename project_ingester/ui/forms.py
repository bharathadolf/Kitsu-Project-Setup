import os
import re
import random
import string
from datetime import datetime, timedelta
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
        if not self.toggle_button.text().startswith("▶") and not self.toggle_button.text().startswith("▼"):
            self.toggle_button.setText(f"▶ {text}")
        else:
            # Keep symbol
            sym = self.toggle_button.text()[:1]
            self.toggle_button.setText(f"{sym} {text}")

    def addRow(self, label, widget):
        self.content_layout.addRow(label, widget)

class EntityForm(QObject):
    """Base class for all entity forms."""
    def __init__(self, node_frame):
        super().__init__()
        self.node_frame = node_frame
        self.widgets = {}

    log_change = Signal(str, str)

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
            


    def update_data_param(self):
        """
        Constructs the 'data' dictionary from optional properties.
        """
        pass

    def on_prop_changed(self, key, value):
        old_val = self.node_frame.properties.get(key)
        self.node_frame.properties[key] = value
        
        # Log the change
        entity_name = self.node_frame.properties.get("name", self.node_frame.node_type)
        self.log_change.emit(f"Updated {entity_name} [{key}]: {old_val} -> {value}", "INFO")
        
        # User Req: "for other entities change the name field --> changes name parameter also should change description parameter..."
        if key == "name" and self.node_frame.node_type != "project":
            code = self.node_frame.properties.get("code", "")
            if code:
                new_desc = f"{value} and {code}"
                self.node_frame.properties["description"] = new_desc
                self.log_change.emit(f"Updated {entity_name} [description]: {new_desc}", "INFO")
                
                if hasattr(self, 'desc_edit') and self.desc_edit:
                    current_ui_desc = self.desc_edit.toPlainText()
                    if current_ui_desc != new_desc:
                         self.desc_edit.blockSignals(True)
                         self.desc_edit.setPlainText(new_desc)
                         self.desc_edit.blockSignals(False)
        
        # Trigger data update
        self.update_data_param()



def generate_project_code(project_name: str) -> str:
    """
    Generate a project code based on name length rules:
    - < 10 chars -> 3-letter uppercase code
    - >= 10 chars -> 5-letter uppercase code
    
    Uses intelligent acronym generation from significant words.
    """
    if not project_name: return ""
    
    # Clean and analyze the name
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', project_name).strip()
    name_length = len(clean_name.replace(" ", ""))  # Count letters only
    
    # Determine target length
    target_length = 3 if name_length < 10 else 5
    
    # Extract significant words
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
    words = [w for w in clean_name.split() if w.lower() not in stop_words and len(w) >= 2]
    
    # Strategy 1: Acronym from first letters
    if len(words) >= target_length:
        code = "".join(word[0].upper() for word in words[:target_length])
        return code.ljust(target_length, "X")[:target_length]
    
    # Strategy 2: Distribute letters
    if words:
        code_chars = []
        remaining = target_length
        for word in words:
            take = max(1, min(len(word), remaining // max(1, len(words) - len(code_chars))))
            code_chars.append(word[:take].upper())
            remaining -= take
            if remaining <= 0: break
        
        code = "".join(code_chars)
        if len(code) < target_length:
            code += "X" * (target_length - len(code))
        return code[:target_length]
    
    # Fallback
    return "".join(random.choices(string.ascii_uppercase, k=target_length))

class ProjectForm(EntityForm):
    def setup_ui(self, layout):
        super().setup_ui(layout)
        
        # --- Mandatory Fields ---
        
        # Root Path (Folder Selection)
        # Needs to be fed into 'data' custom param
        
        root_path_container = QWidget()
        rp_layout = QHBoxLayout(root_path_container)
        rp_layout.setContentsMargins(0,0,0,0)
        rp_layout.setSpacing(2)
        
        # Get existing value or default
        current_data = self.node_frame.properties.get("data")
        default_root = ""
        if isinstance(current_data, dict):
            default_root = current_data.get("root_path", "")
            
        self.root_path_edit = QLineEdit(default_root)
        self.root_path_edit.setPlaceholderText("Select Root Folder...")
        self.root_path_edit.textChanged.connect(self.on_root_path_changed)
        
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(30, 22)
        browse_btn.clicked.connect(self.browse_root_path)
        
        rp_layout.addWidget(self.root_path_edit)
        rp_layout.addWidget(browse_btn)
        
        layout.addRow("Root Path:", root_path_container)
        
        # Name
        name_input = QLineEdit(self.node_frame.properties.get("name", ""))
        name_input.textChanged.connect(lambda t: self.on_project_name_changed(t))
        layout.addRow("Name:", name_input)
        
        # Code (Editable, Auto-filled)
        self.code_input = QLineEdit(self.node_frame.properties.get("code", ""))
        self.code_input.textChanged.connect(lambda t: self.on_prop_changed("code", t))
        layout.addRow("Code:", self.code_input)

        # Production Type
        is_custom = self.node_frame.properties.get("is_custom_template", True)
        current_type = self.node_frame.properties.get("production_type", "short")
        
        if is_custom:
            # User request: "make the user to name the field instead of dropdown selection only in custom selection"
            self.type_input = QLineEdit(current_type)
            self.type_input.textChanged.connect(self.on_type_changed)
            layout.addRow("Type:", self.type_input)
            
            # For compatibility with potential other methods referencing type_combo, we set it to None or handle it
            self.type_combo = None 
        else:
            self.type_combo = QComboBox()
            
            # Map Config: (Display Name, Internal Value)
            # 1) Feature film -> movie
            # 2) Tv show -> tvshow
            # 3) Shots only -> short
            # 4) Assets only -> commercial
            # 5) Custom -> short (default or whatever)
            
            type_mapping = [
                ("Feature film", "featurefilm"), # Some systems use featurefilm, tree.py used movie? Check tree.py again. tree.py used 'movie'.
                ("Tv show", "tvshow"),
                ("Shots only", "short"),
                ("Assets only", "commercial"),
                ("Custom", "custom")
            ]
            
            # Corrections based on tree.py:
            # tree.py says: "Feature Film": "movie"
            # But earlier code used "featurefilm"?
            # Let's support both or standard. Gazu usually uses 'movie', 'tvshow', 'short'.
            # I will use the values that match tree.py logic for consistency.
            
            type_mapping = [
                ("Feature film", "movie"), 
                ("Tv show", "tvshow"), 
                ("Shots only", "shots only"), 
                ("Assets only", "assets only"),
                ("Custom", "custom") 
            ]

            for label, value in type_mapping:
                self.type_combo.addItem(label, value)
            
            # Select the correct item based on internal value
            index = -1
            for i in range(self.type_combo.count()):
                if self.type_combo.itemData(i) == current_type:
                    index = i
                    break
            
            # If not found (e.g. 'featurefilm' vs 'movie' mismatch), try text match or default
            if index == -1:
                # Add it as custom invisible or just show raw
                self.type_combo.addItem(current_type, current_type)
                index = self.type_combo.count() - 1
                
            self.type_combo.setCurrentIndex(index)
            self.type_combo.setEnabled(False) # Locked for templates
            self.type_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            layout.addRow("Type:", self.type_combo)

        # Production Style (Dropdown)
        self.style_combo = QComboBox()
        style_items = ["2d", "3d", "2d3d", "vfx", "stop-motion"]
        self.style_combo.addItems(style_items)
        
        current_style = self.node_frame.properties.get("production_style", "2d3d")
        if current_style not in style_items: self.style_combo.addItem(current_style)
        self.style_combo.setCurrentText(current_style)
        
        self.style_combo.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.style_combo.currentTextChanged.connect(self.on_style_changed)
        layout.addRow("Style:", self.style_combo)

        # Description (Auto-generated/Editable)
        # We won't use QLineEdit for description, maybe QTextEdit for consistency, 
        # but user said "Description: {type} using {style} project" which fits in one line often.
        # But let's use QTextEdit as before for better UX if it gets long.
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlainText(self.node_frame.properties.get("description", ""))
        self.desc_edit.setFixedHeight(60)
        self.desc_edit.textChanged.connect(lambda: self.on_prop_changed("description", self.desc_edit.toPlainText()))
        layout.addRow("Description:", self.desc_edit)
        
        # Initialize description if empty and we have data
        if not self.desc_edit.toPlainText().strip():
            self.update_description_auto()

        # --- Optional Fields (Collapsible with Checkboxes) ---
        
        # Master Checkbox
        self.master_cb = QCheckBox("Enable All Optional Properties")
        self.master_cb.setTristate(False)
        self.master_cb.toggled.connect(self.on_master_toggled)
        layout.addRow(self.master_cb)
        
        collapsible = CollapsibleBox("Optional Properties")
        layout.addRow(collapsible)
        
        self.optional_toggles = []
        
        # Helper to add toggleable row
        self.add_optional_row(collapsible, "FPS:", "fps", QSpinBox(), 24, lambda w, v: w.setValue(int(v)))
        self.add_optional_row(collapsible, "Ratio:", "ratio", QLineEdit(), "1.78")
        self.add_optional_row(collapsible, "Resolution:", "resolution", QLineEdit(), "1920x1080")
        
        self.add_optional_row(collapsible, "Has Avatar:", "has_avatar", QCheckBox(), False, lambda w, v: w.setChecked(bool(v)), lambda w: w.isChecked())

        collapsible.setText("Optional Properties")
        
        
    def add_optional_row(self, container, label_text, key, widget, default_val, setter=None, getter=None):
        """
        Adds a row with a checkbox to enable/disable the property.
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Checkbox
        use_key = f"use_{key}"
        is_enabled = self.node_frame.properties.get(use_key, False)
        
        checkbox = QCheckBox()
        checkbox.setChecked(is_enabled)
        checkbox.setFixedSize(20, 20)
        
        # Track for master toggle
        if not hasattr(self, 'optional_toggles'): self.optional_toggles = []
        self.optional_toggles.append(checkbox)
        
        # Widget Setup
        widget.setEnabled(is_enabled)
        widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        # Set Initial Value
        val = self.node_frame.properties.get(key, default_val)
        if setter:
            setter(widget, val)
        else:
            # Default setter for common widgets
            if isinstance(widget, QLineEdit): widget.setText(str(val))
            elif isinstance(widget, QSpinBox): widget.setValue(int(val))
            elif isinstance(widget, QCheckBox): widget.setChecked(bool(val))
            
        # Connections
        checkbox.toggled.connect(lambda c: self.on_optional_toggled(c, key, widget))
        
        if getter:
            # Custom getter (e.g. for DateEdit)
            if isinstance(widget, QtWidgets.QDateEdit):
                widget.dateChanged.connect(lambda: self.on_prop_changed(key, getter(widget)))
            elif isinstance(widget, QCheckBox):
                 widget.toggled.connect(lambda: self.on_prop_changed(key, getter(widget)))
        else:
            # Default connections
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda t: self.on_prop_changed(key, t))
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(lambda v: self.on_prop_changed(key, v))
            elif isinstance(widget, QCheckBox): # In case we used default for checkbox (Avatar)
                widget.toggled.connect(lambda c: self.on_prop_changed(key, c))

        row_layout.addWidget(checkbox)
        row_layout.addWidget(QLabel(label_text))
        row_layout.addWidget(widget)
        
        container.addRow(row_widget, None) # None because we packed label into the widget
        
    def on_optional_toggled(self, checked, key, widget):
        self.node_frame.properties[f"use_{key}"] = checked
        widget.setEnabled(checked)
        
    def on_master_toggled(self, checked):
        for cb in self.optional_toggles:
            cb.setChecked(checked)



    
    def on_project_name_changed(self, text):
        old_name = self.node_frame.properties.get("name")
        self.node_frame.properties["name"] = text
        self.log_change.emit(f"Updated Project [name]: {old_name} -> {text}", "INFO")
        
        # Auto-generate code using new logic
        code = generate_project_code(text)
        old_code = self.node_frame.properties.get("code")
        self.node_frame.properties["code"] = code
        
        if old_code != code:
             self.log_change.emit(f"Updated Project [code]: {old_code} -> {code}", "INFO")
        
        if hasattr(self, 'code_input') and self.code_input:
             self.code_input.setText(code)
        
        # Update Data Param because Code changed
        self.update_data_param()
        
    def on_type_changed(self, text):
        self.node_frame.properties["production_type"] = text
        self.update_description_auto()
        
    def on_style_changed(self, text):
        self.node_frame.properties["production_style"] = text
        self.update_description_auto()
        
    def update_description_auto(self):
        # "Feature film using 2d3d project"
        if hasattr(self, 'type_combo') and self.type_combo:
            p_type = self.type_combo.currentText()
        elif hasattr(self, 'type_input') and self.type_input:
            p_type = self.type_input.text()
        else:
            p_type = self.node_frame.properties.get("production_type", "")
            
        p_style = self.style_combo.currentText()
        desc = f"{p_type} using {p_style} project"
        self.desc_edit.setPlainText(desc)
        self.node_frame.properties["description"] = desc

    def browse_root_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Root Project Folder")
        if path:
            self.root_path_edit.setText(path)

    def on_root_path_changed(self, text):
        self.node_frame.properties["root_path"] = text
        # Update Data Param because Root Path changed
        self.update_data_param()

    def update_data_param(self):
        # Gather inputs
        root_path = self.root_path_edit.text()
        code = self.node_frame.properties.get("code", "")
        project_code = code.lower()
        
        # Safe construction of project_path
        project_path = ""
        if root_path and project_code:
            import os
            # Use forward slashes for consistency if needed, or os.path.join
            project_path = f"{root_path}/{project_code}".replace("\\", "/")
            
        # Construct data dict
        data_val = {
            "root_path": root_path,
            "project_code": project_code,
            "project_path": project_path
        }
        
        self.node_frame.properties["data"] = data_val
        # Also ensure 'file_tree' is present as requested (None for now or default)
        if "file_tree" not in self.node_frame.properties:
             self.node_frame.properties["file_tree"] = None # or None
             
        # self.node_frame.properties is a dict reference, so this updates it directly.

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
        fi_val = self.node_frame.properties.get("frame_in")
        if fi_val is None: fi_val = 1001
        frame_in.setValue(int(fi_val))
        frame_in.valueChanged.connect(lambda v: self.on_prop_changed("frame_in", v))
        collapsible.addRow("Frame In:", frame_in)
        
        frame_out = QSpinBox()
        frame_out.setRange(-999999, 999999)
        fo_val = self.node_frame.properties.get("frame_out")
        if fo_val is None: fo_val = 1100
        frame_out.setValue(int(fo_val))
        frame_out.valueChanged.connect(lambda v: self.on_prop_changed("frame_out", v))
        collapsible.addRow("Frame Out:", frame_out)
        
        nb_frames = QSpinBox()
        nb_frames.setRange(0, 999999)
        nb_val = self.node_frame.properties.get("nb_frames")
        if nb_val is None: nb_val = 100
        nb_frames.setValue(int(nb_val))
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
