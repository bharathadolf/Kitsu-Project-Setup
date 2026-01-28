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
            # Ensure context update updates tab title? 
            # For now, just initial name.
            tab_widget.addTab(page, title)

    def _populate_form(self, container_layout, node_frame):
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        form_layout.setContentsMargins(5, 5, 5, 5)
        form_layout.setSpacing(5)
        
        # Instantiate correct form
        form_class = FORM_MAP.get(node_frame.node_type, EntityForm)
        form_instance = form_class(node_frame)
        form_instance.setup_ui(form_layout)
        
        # Divider for Custom Attributes
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("background-color: #3e3e3e;")
        form_layout.addRow(sep)
        
        custom_header = QLabel("Custom Attributes")
        custom_header.setStyleSheet("color: #4fc3f7; font-weight: bold; margin-top: 5px;")
        form_layout.addRow(custom_header)
        
        # Custom Attributes Logic
        self._populate_custom_attributes(form_layout, node_frame)
        
        container_layout.addWidget(form_widget)
        container_layout.addStretch()

    def _populate_custom_attributes(self, form_layout, node_frame):
        custom_props = node_frame.properties.get("custom", {})
        for key, data in custom_props.items():
            val = data.get("value")
            dtype = data.get("type", "text")
            
            field_container = QWidget()
            field_layout = QHBoxLayout(field_container)
            field_layout.setContentsMargins(0,0,0,0)
            field_layout.setSpacing(5)
            
            inp_widget = None
            if dtype == "text":
                inp_widget = QLineEdit(str(val))
                inp_widget.textChanged.connect(lambda t, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, t))
            elif dtype == "number":
                inp_widget = QtWidgets.QSpinBox()
                inp_widget.setRange(-999999, 999999)
                try: inp_widget.setValue(int(val))
                except: inp_widget.setValue(0)
                inp_widget.valueChanged.connect(lambda v, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, v))
                inp_widget.setStyleSheet("background-color: #333; color: #fff; border: 1px solid #555;")
            elif dtype == "bool":
                inp_widget = QtWidgets.QCheckBox()
                inp_widget.setChecked(bool(val))
                inp_widget.toggled.connect(lambda c, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, c))
            elif dtype == "date":
                inp_widget = QtWidgets.QDateEdit()
                inp_widget.setCalendarPopup(True)
                inp_widget.setDisplayFormat("yyyy-MM-dd")
                try:
                    qdate = QtCore.QDate.fromString(val, "yyyy-MM-dd")
                    if not qdate.isValid(): qdate = QtCore.QDate.currentDate()
                    inp_widget.setDate(qdate)
                except: inp_widget.setDate(QtCore.QDate.currentDate())
                inp_widget.dateChanged.connect(lambda d, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, d.toString("yyyy-MM-dd")))
            elif dtype == "dropdown":
                inp_widget = QtWidgets.QComboBox()
                options = data.get("options", [])
                inp_widget.addItems(options)
                idx = inp_widget.findText(str(val))
                if idx >= 0: inp_widget.setCurrentIndex(idx)
                inp_widget.currentTextChanged.connect(lambda t, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, t))
            elif dtype == "color":
                inp_widget = QPushButton()
                inp_widget.setFixedSize(50, 20)
                c_val = str(val) if val else "#ffffff"
                inp_widget.setStyleSheet(f"background-color: {c_val}; border: 1px solid #555;")
                inp_widget.clicked.connect(lambda checked=False, k=key, nf=node_frame: self.pick_color(nf, k))
            elif dtype == "path" or dtype == "file_path" or dtype == "folder_path":
                container = QWidget()
                h_lay = QHBoxLayout(container)
                h_lay.setContentsMargins(0,0,0,0)
                h_lay.setSpacing(2)
                path_edit = QLineEdit(str(val))
                path_edit.setReadOnly(False)
                path_edit.textChanged.connect(lambda t, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, t))
                browse = QPushButton("...")
                browse.setFixedSize(20, 20)
                
                mode = "folder" if dtype == "folder_path" else "file"
                # Legacy "path" was file
                if dtype == "path": mode = "file"
                
                browse.clicked.connect(lambda checked=False, pe=path_edit, m=mode: self.browse_path(pe, m))
                h_lay.addWidget(path_edit)
                h_lay.addWidget(browse)
                inp_widget = container
            elif dtype == "richtext":
                 inp_widget = QtWidgets.QTextEdit()
                 inp_widget.setPlainText(str(val))
                 inp_widget.setFixedHeight(60)
                 inp_widget.setStyleSheet("font-size: 10px; font-family: Segoe UI;")
                 inp_widget.textChanged.connect(lambda k=key, nf=node_frame, w=inp_widget: self.on_custom_prop_changed(nf, k, w.toPlainText()))

            if inp_widget:
                field_layout.addWidget(inp_widget)
            
            del_btn = QPushButton("x")
            del_btn.setFixedSize(20, 20)
            del_btn.setStyleSheet("background-color: #c62828; color: white; border: none; border-radius: 3px; font-weight: bold;")
            del_btn.clicked.connect(lambda checked=False, k=key, nf=node_frame: self.remove_custom_attribute(nf, k))
            field_layout.addWidget(del_btn)
            
            form_layout.addRow(f"{key}:", field_container)

        add_attr_btn = QPushButton("+ Add Attribute")
        add_attr_btn.setStyleSheet("background-color: #2e7d32; color: white; border: none; padding: 5px;")
        add_attr_btn.clicked.connect(lambda: self.add_custom_attribute(node_frame))
        form_layout.addRow(add_attr_btn)

    def on_custom_prop_changed(self, node_frame, key, value):
        if "custom" in node_frame.properties and key in node_frame.properties["custom"]:
            node_frame.properties["custom"][key]["value"] = value
            self.log_message.emit(f"Custom Property '{key}' changed to '{value}'", "INFO")

    def add_custom_attribute(self, node_frame):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Custom Attribute")
        dialog.setModal(True)
        dialog.resize(300, 150)
        dialog.setStyleSheet(self.styleSheet())
        layout = QtWidgets.QFormLayout(dialog)
        name_edit = QLineEdit()
        type_combo = QtWidgets.QComboBox()
        # Added "Folder Path"
        type_combo.addItems(["Text", "Number", "Yes/No", "Date", "Dropdown", "Color", "File Path", "Folder Path", "Multi-line Text"])
        option_edit = QLineEdit()
        option_edit.setPlaceholderText("Option 1, Option 2, Option 3")
        option_edit.setEnabled(False)
        type_combo.currentTextChanged.connect(lambda t: option_edit.setEnabled(t == "Dropdown"))
        layout.addRow("Attribute Name:", name_edit)
        layout.addRow("Data Type:", type_combo)
        layout.addRow("Options (Dropdown only):", option_edit)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            attr_name = name_edit.text().strip()
            if not attr_name:
                QtWidgets.QMessageBox.warning(self, "Invalid Name", "Attribute name cannot be empty.")
                return
            if "custom" not in node_frame.properties:
                node_frame.properties["custom"] = {}
            if attr_name in node_frame.properties["custom"]:
                QtWidgets.QMessageBox.warning(self, "Duplicate", "Attribute already exists.")
                return
            
            # Map UI type to internal type
            type_map = {
                "Text": "text", "Number": "number", "Yes/No": "bool",
                "Date": "date", "Dropdown": "dropdown", "Color": "color",
                "File Path": "file_path", "Folder Path": "folder_path", 
                "Multi-line Text": "richtext"
            }
            selected_type = type_map[type_combo.currentText()]
            default_val = ""
            options = []
            if selected_type == "number": default_val = 0
            elif selected_type == "bool": default_val = False
            elif selected_type == "date": default_val = datetime.now().strftime("%Y-%m-%d")
            elif selected_type == "color": default_val = "#ffffff"
            elif selected_type == "dropdown":
                raw_opts = option_edit.text()
                options = [o.strip() for o in raw_opts.split(",") if o.strip()]
                if not options: options = ["Option 1"]
                default_val = options[0]
            prop_data = {"type": selected_type, "value": default_val}
            if selected_type == "dropdown": prop_data["options"] = options
            node_frame.properties["custom"][attr_name] = prop_data
            self.log_message.emit(f"Added custom attribute: {attr_name} ({selected_type})", "SUCCESS")
            
            # Refresh
            self.load_nodes([node_frame])

    def pick_color(self, node_frame, key):
        initial_color = QtGui.QColor(node_frame.properties["custom"][key].get("value", "#ffffff"))
        color = QtWidgets.QColorDialog.getColor(initial_color, self, "Pick Color")
        if color.isValid():
            hex_color = color.name()
            self.on_custom_prop_changed(node_frame, key, hex_color)
            self.load_nodes([node_frame])

    def browse_path(self, line_edit, mode="file"):
        path = ""
        if mode == "folder":
            path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File")
            
        if path: line_edit.setText(path)

    def remove_custom_attribute(self, node_frame, key):
        if "custom" in node_frame.properties and key in node_frame.properties["custom"]:
            del node_frame.properties["custom"][key]
            self.log_message.emit(f"Removed custom attribute: {key}", "WARNING")
            self.load_nodes([node_frame])
