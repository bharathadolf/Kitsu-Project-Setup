from datetime import datetime
from ..utils.compat import *
from ..config import *

class PropertiesWidget(QWidget):
    log_message = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_node_frame = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.header = QLabel("Properties Panel")
        self.header.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.header)
        
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # Initial empty widget
        self.setStyleSheet("") # Will be set by set_theme
        
    def set_theme(self, theme):
        self.header.setStyleSheet(theme.get_header_style('#68217a'))
        self.setStyleSheet(theme.property_panel_style)
        
    def load_nodes(self, node_frames):
        if not isinstance(node_frames, list):
             node_frames = [node_frames] if node_frames else []
        self.tab_widget.clear()
        for node_frame in node_frames:
             self.add_node_tab(node_frame)
             
    def add_node_tab(self, node_frame):
        display_name = node_frame.node_type.capitalize()
        if node_frame.node_id:
             display_name += f"#{node_frame.node_id}"
        
        current_name = node_frame.properties.get("name", "")
        
        tab = QWidget()
        tab.setObjectName("PropertiesContent")
        form_layout = QtWidgets.QFormLayout(tab)
        form_layout.setContentsMargins(5, 5, 5, 5)
        form_layout.setSpacing(5)

        name_input = QLineEdit()
        name_input.setText(current_name)
        
        code_input = None 
        if node_frame.node_type == "project":
            code_input = QLineEdit()
            code_input.setText(node_frame.properties.get("code", ""))
            code_input.setFixedWidth(50) 
            code_input.textChanged.connect(lambda t, nf=node_frame: self.on_code_changed(t, nf))
        
        name_input.textChanged.connect(lambda t, nf=node_frame, ni=name_input, ci=code_input: self.on_name_changed(t, nf, ni, ci))
        name_input.editingFinished.connect(lambda: self.log_change(f"Name changed to: {name_input.text()}"))

        if node_frame.node_type == "project":
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            row_layout.addWidget(QLabel("Entity Name:"))
            row_layout.addWidget(name_input)
            row_layout.addWidget(QLabel("Code:"))
            row_layout.addWidget(code_input)
            form_layout.addRow(row_widget)
            
            type_combo = QtWidgets.QComboBox()
            type_combo.addItems(["movie", "tvshow", "short", "commercial"])
            current_type = node_frame.properties.get("production_type", "short")
            idx = type_combo.findText(current_type)
            if idx >= 0: type_combo.setCurrentIndex(idx)
            type_combo.currentTextChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "production_type", t))
            form_layout.addRow("Production Type:", type_combo)

            start_date_edit = QtWidgets.QDateEdit()
            start_date_edit.setCalendarPopup(True)
            start_date_edit.setDisplayFormat("yyyy-MM-dd")
            s_date_str = node_frame.properties.get("start_date", datetime.now().strftime("%Y-%m-%d"))
            start_date_edit.setDate(QtCore.QDate.fromString(s_date_str, "yyyy-MM-dd"))
            start_date_edit.dateChanged.connect(lambda d, nf=node_frame: self.on_date_changed(nf, "start_date", d))
            form_layout.addRow("Start Date:", start_date_edit)

            path_widget = QWidget()
            path_layout = QHBoxLayout(path_widget)
            path_layout.setContentsMargins(0,0,0,0)
            path_layout.setSpacing(2)
            root_path_input = QLineEdit()
            root_path_input.setText(node_frame.properties.get("root_path", ""))
            root_path_input.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "root_path", t))
            browse_btn = QPushButton("...")
            browse_btn.setFixedWidth(20)
            browse_btn.clicked.connect(lambda: self.browse_folder(root_path_input))
            path_layout.addWidget(root_path_input)
            path_layout.addWidget(browse_btn)
            form_layout.addRow("Show path:", path_widget)

            task_options = ["layout", "anim", "fx", "lighting", "comp"]
            task_widget = self.create_compact_multi_select("Task Template", task_options, node_frame.properties.get("task_template", []), lambda sel, nf=node_frame: self.on_multi_select_changed(nf, "task_template", sel), allow_custom=True)
            form_layout.addRow("Task Template:", task_widget)

            asset_options = ["characters", "props", "env"]
            asset_widget = self.create_compact_multi_select("Asset Types", asset_options,node_frame.properties.get("asset_types", []), lambda sel, nf=node_frame: self.on_multi_select_changed(nf, "asset_types", sel), allow_custom=True)
            form_layout.addRow("Asset Types:", asset_widget)
            
        elif node_frame.node_type == "episode":
            # EPISODE FIELDS
            # episode_name (text), episode_order (spinbox)
            
            ep_name_edit = QLineEdit(str(node_frame.properties.get("episode_name", "")))
            ep_name_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "episode_name", t))
            form_layout.addRow("Episode Name:", ep_name_edit)
            
            ep_order_spin = QtWidgets.QSpinBox()
            ep_order_spin.setRange(1, 999)
            ep_order_spin.setValue(int(node_frame.properties.get("episode_order", 1)))
            ep_order_spin.valueChanged.connect(lambda v, nf=node_frame: self.on_prop_changed(nf, "episode_order", v))
            ep_order_spin.setStyleSheet("background-color: #333; color: #fff;")
            form_layout.addRow("Episode Order:", ep_order_spin)

        elif node_frame.node_type == "sequence":
            # SEQUENCE FIELDS
            # sequence_code (text), sequence_name (text)
            
            seq_code_edit = QLineEdit(str(node_frame.properties.get("sequence_code", "")))
            seq_code_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "sequence_code", t))
            form_layout.addRow("Seq Code:", seq_code_edit)
            
            seq_name_edit = QLineEdit(str(node_frame.properties.get("sequence_name", "")))
            seq_name_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "sequence_name", t))
            form_layout.addRow("Seq Name:", seq_name_edit)
            
        elif node_frame.node_type == "shot":
            # SHOT FIELDS
            # shot_code (text), output_format (dropdown), rv_context_group (text), delivery_tag (dropdown)
            
            shot_code_edit = QLineEdit(str(node_frame.properties.get("shot_code", "")))
            shot_code_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "shot_code", t))
            form_layout.addRow("Shot Code:", shot_code_edit)
            
            out_fmt_widget = self.create_dropdown("output_format", OUTPUT_FORMATS, node_frame)
            form_layout.addRow("Output Format:", out_fmt_widget)
            
            rv_ctx_edit = QLineEdit(str(node_frame.properties.get("rv_context_group", "")))
            rv_ctx_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "rv_context_group", t))
            form_layout.addRow("RV Context:", rv_ctx_edit)
            
            del_tag_widget = self.create_dropdown("delivery_tag", DELIVERY_TAGS, node_frame)
            form_layout.addRow("Delivery Tag:", del_tag_widget)

        elif node_frame.node_type == "asset_type":
            # ASSET TYPE FIELDS
            # asset_type_code, asset_root_path, publish_ruleset, versioning_mode
            
            at_code_edit = QLineEdit(str(node_frame.properties.get("asset_type_code", "")))
            at_code_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "asset_type_code", t))
            form_layout.addRow("Code:", at_code_edit)
            
            # Asset root path
            path_widget = QWidget()
            path_layout = QHBoxLayout(path_widget)
            path_layout.setContentsMargins(0,0,0,0)
            path_layout.setSpacing(2)
            root_path_input = QLineEdit()
            root_path_input.setText(node_frame.properties.get("asset_root_path", ""))
            root_path_input.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "asset_root_path", t))
            browse_btn = QPushButton("...")
            browse_btn.setFixedWidth(20)
            browse_btn.clicked.connect(lambda: self.browse_folder(root_path_input))
            path_layout.addWidget(root_path_input)
            path_layout.addWidget(browse_btn)
            form_layout.addRow("Asset Path:", path_widget)
            
            pub_rule_widget = self.create_dropdown("publish_ruleset", PUBLISH_RULESETS, node_frame)
            form_layout.addRow("Publish Rules:", pub_rule_widget)
            
            ver_mode_widget = self.create_dropdown("versioning_mode", VERSIONING_MODES, node_frame)
            form_layout.addRow("Versioning:", ver_mode_widget)

        elif node_frame.node_type == "asset":
            # ASSET FIELDS
            # asset_code, asset_name, asset_category, primary_dcc, render_engine, publish_enabled, asset_status
            
            ast_code_edit = QLineEdit(str(node_frame.properties.get("asset_code", "")))
            ast_code_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "asset_code", t))
            form_layout.addRow("Asset Code:", ast_code_edit)
            
            ast_name_edit = QLineEdit(str(node_frame.properties.get("asset_name", "")))
            ast_name_edit.textChanged.connect(lambda t, nf=node_frame: self.on_prop_changed(nf, "asset_name", t))
            form_layout.addRow("Asset Name:", ast_name_edit)
            
            cat_widget = self.create_dropdown("asset_category", ASSET_CATEGORIES, node_frame)
            form_layout.addRow("Category:", cat_widget)
            
            dcc_widget = self.create_dropdown("primary_dcc", DCC_APPS, node_frame)
            form_layout.addRow("Primary DCC:", dcc_widget)
            
            eng_widget = self.create_dropdown("render_engine", RENDER_ENGINES, node_frame)
            form_layout.addRow("Render Engine:", eng_widget)
            
            stat_widget = self.create_dropdown("asset_status", ASSET_STATUSES, node_frame)
            form_layout.addRow("Status:", stat_widget)
            
            pub_cb = QtWidgets.QCheckBox()
            pub_cb.setChecked(bool(node_frame.properties.get("publish_enabled", True)))
            pub_cb.toggled.connect(lambda c, nf=node_frame: self.on_prop_changed(nf, "publish_enabled", c))
            form_layout.addRow("Publish Enabled:", pub_cb)

        else:
            form_layout.addRow("Entity Name:", name_input)
            
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("background-color: #3e3e3e;")
        form_layout.addRow(sep)
        
        custom_header = QLabel("Custom Attributes")
        custom_header.setStyleSheet("color: #4fc3f7; font-weight: bold; margin-top: 5px;")
        form_layout.addRow(custom_header)
        
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
            elif dtype == "path":
                container = QWidget()
                h_lay = QHBoxLayout(container)
                h_lay.setContentsMargins(0,0,0,0)
                h_lay.setSpacing(2)
                path_edit = QLineEdit(str(val))
                path_edit.setReadOnly(False)
                path_edit.textChanged.connect(lambda t, k=key, nf=node_frame: self.on_custom_prop_changed(nf, k, t))
                browse = QPushButton("...")
                browse.setFixedSize(20, 20)
                browse.clicked.connect(lambda checked=False, pe=path_edit: self.browse_file_path(pe))
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
            
        self.tab_widget.addTab(tab, display_name)
        self.tab_widget.setCurrentWidget(tab) 

    def create_dropdown(self, key, options, node_frame):
        # Dropdown helper that assumes list storage for scalar value (first item selected if existing is list)
        combo = QtWidgets.QComboBox()
        combo.addItems(options)
        
        current_val = node_frame.properties.get(key)
        # Handle if stored as list (single selection stored as list of 1) or scalar
        scalar_val = str(current_val[0]) if isinstance(current_val, list) and current_val else str(current_val)
        
        idx = combo.findText(scalar_val)
        if idx >= 0: combo.setCurrentIndex(idx)
        
        # Connect
        combo.currentTextChanged.connect(lambda t, nf=node_frame, k=key: self.on_dropdown_changed(nf, k, t))
        return combo

    def on_dropdown_changed(self, node_frame, key, text):
        # Store as list for consistency with 'list' type in requirements, or scalar?
        # Requirement said 'Type: list | Widget: dropdown'. Usually implies selection from list.
        # User implies single selection from a list of options. Storing as list ["val"] is safe.
        node_frame.properties[key] = [text]
        self.log_message.emit(f"Property '{key}' updated to ['{text}']", "INFO")

    def create_compact_multi_select(self, title, options, selected_items, callback, allow_custom=False):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(5)
        display_edit = QLineEdit()
        display_edit.setReadOnly(True)
        display_edit.setText(", ".join(selected_items))
        display_edit.setPlaceholderText("None selected")
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(40)
        edit_btn.clicked.connect(lambda: self.open_multi_select_dialog(title, options, selected_items, callback, display_edit, allow_custom))
        layout.addWidget(display_edit)
        layout.addWidget(edit_btn)
        return container

    def open_multi_select_dialog(self, title, options, current_selection, callback, display_edit, allow_custom):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Select {title}")
        dialog.setModal(True)
        dialog.resize(300, 400)
        layout = QVBoxLayout(dialog)
        list_widget = QtWidgets.QListWidget()
        list_widget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        all_options = options.copy()
        for s in current_selection:
            if s not in all_options: all_options.append(s)
        for opt in all_options:
            item = QtWidgets.QListWidgetItem(opt)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if opt in current_selection else Qt.Unchecked)
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        if allow_custom:
            add_btn = QPushButton("+ Add Custom Option")
            add_btn.clicked.connect(lambda: self.add_custom_list_option(list_widget, None)) 
            layout.addWidget(add_btn)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(dialog.accept)
        btns.rejected.connect(dialog.reject)
        layout.addWidget(btns)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_selection = []
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.checkState() == Qt.Checked:
                    new_selection.append(item.text())
            callback(new_selection)
            display_edit.setText(", ".join(new_selection))

    def add_custom_list_option(self, list_widget, callback):
        text, ok = QtWidgets.QInputDialog.getText(self, "Add Custom Option", "Name:")
        if ok and text:
            existing = [list_widget.item(i).text() for i in range(list_widget.count())]
            if text not in existing:
                item = QtWidgets.QListWidgetItem(text)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked) 
                list_widget.addItem(item)

    def browse_folder(self, line_edit):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder: line_edit.setText(folder)

    def on_date_changed(self, node_frame, key, qdate):
        date_str = qdate.toString("yyyy-MM-dd")
        self.on_prop_changed(node_frame, key, date_str)

    def on_multi_select_changed(self, node_frame, key, selection):
        node_frame.properties[key] = selection
        self.log_message.emit(f"Property '{key}' updated on {node_frame.properties.get('name')}: {selection}", "INFO")

    def on_prop_changed(self, node_frame, key, value):
        old = node_frame.properties.get(key)
        if old != value:
            node_frame.properties[key] = value
            self.log_message.emit(f"Property '{key}' changed to '{value}' on {node_frame.properties.get('name')}", "INFO")

    def on_name_changed(self, text, node_frame, name_input, code_input=None):
        node_frame.properties["name"] = text
        if node_frame.node_type == "project":
            stripped = text.replace(" ", "").upper()
            if len(text) > 10: new_code = stripped[:5]
            else: new_code = stripped[:3]
            node_frame.properties["code"] = new_code
            if code_input: code_input.setText(new_code)

    def log_change(self, msg):
        self.log_message.emit(msg, "INFO")
            
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
        type_combo.addItems(["Text", "Number", "Yes/No", "Date", "Dropdown", "Color", "File Path", "Multi-line Text"])
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
            type_map = {
                "Text": "text", "Number": "number", "Yes/No": "bool",
                "Date": "date", "Dropdown": "dropdown", "Color": "color",
                "File Path": "path", "Multi-line Text": "richtext"
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
            self.load_nodes([node_frame])

    def pick_color(self, node_frame, key):
        initial_color = QtGui.QColor(node_frame.properties["custom"][key].get("value", "#ffffff"))
        color = QtWidgets.QColorDialog.getColor(initial_color, self, "Pick Color")
        if color.isValid():
            hex_color = color.name()
            self.on_custom_prop_changed(node_frame, key, hex_color)
            self.load_nodes([node_frame])

    def browse_file_path(self, line_edit):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select File")
        if path: line_edit.setText(path)

    def remove_custom_attribute(self, node_frame, key):
        if "custom" in node_frame.properties and key in node_frame.properties["custom"]:
            del node_frame.properties["custom"][key]
            self.log_message.emit(f"Removed custom attribute: {key}", "WARNING")
            self.load_nodes([node_frame])
    
    def on_code_changed(self, text, node_frame):
        node_frame.properties["code"] = text
