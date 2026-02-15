from ..utils.compat import *
from ..utils import code_gen
import json

class GenerationSummaryDialog(QDialog):
    def __init__(self, plan, manager=None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.manager = manager
        self.is_generated = False
        self.setWindowTitle("Confirm Generation")
        self.resize(800, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter for List and Details
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left: Entity List
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Entity Type", "Name", "Action"])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 200)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.itemChanged.connect(self.on_item_changed) # Connect change signal
        splitter.addWidget(self.tree)
        
        # Right: Parameters
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setStyleSheet("font-family: Consolas, monospace;")
        splitter.addWidget(self.details)
        
        splitter.setSizes([450, 350])
        
        # Populate List
        self.populate_tree()
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-style: italic; margin-left: 10px;")
        btn_layout.addWidget(self.status_label)
        
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        if self.manager:
             self.btn_gen_query = QPushButton("Generate & Query")
             self.btn_gen_query.setStyleSheet("background-color: #1976D2; color: white; font-weight: bold; padding: 5px 15px;")
             self.btn_gen_query.clicked.connect(self.on_generate_query)
             btn_layout.addWidget(self.btn_gen_query)
        
        self.btn_generate = QPushButton("Generate")
        self.btn_generate.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_generate.clicked.connect(self.on_generate)
        btn_layout.addWidget(self.btn_generate)
        
        layout.addLayout(btn_layout)

    def sanity_check(self):
        """Returns True if safe to proceed, False otherwise."""
        if not self.plan: return False
        
        # Check Project Name uniqueness
        proj_step = self.plan[0]
        if proj_step['type'] == 'project':
            name = proj_step['name']
            self.status_label.setText(f"Verifying project '{name}'...")
            QApplication.processEvents()
            
            valid, msg = self.manager.sanity_check_project(name)
            if not valid:
                self.status_label.setText(f"Error: {msg}")
                self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                return False
        return True

    def on_generate(self):
        if not self.manager: return
        
        # 1. Sanity Check
        if not self.sanity_check(): return

        # 2. Execute
        self.status_label.setText("Generating Project... Please wait.")
        self.set_buttons_enabled(False)
        QApplication.processEvents()
        
        try:
            success = self.manager.execute_plan(self.plan)
            if success:
                self.is_generated = True
                self.accept() # Close on success
            else:
                 self.status_label.setText("Generation Failed. Check Console.")
                 self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                 self.set_buttons_enabled(True)
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.set_buttons_enabled(True)

    def on_generate_query(self):
        if not self.manager: return
        
        # 1. Sanity Check
        if not self.sanity_check(): return
        
        # 2. UI Prep
        self.status_label.setText("Starting Generation... Please wait.")
        self.set_buttons_enabled(False)
        
        # 3. Threaded Execution
        self.worker = GenerationWorker(self.manager, self.plan)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.error.connect(self.on_generation_error)
        self.worker.start()

    def update_status(self, msg):
        self.status_label.setText(msg)
        # self.status_label.repaint() # Optional

    def on_generation_finished(self, success):
        self.is_generated = success
        if success:
            self.status_label.setText("Generation & Query Complete.")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; margin-left: 10px;")
            
            # Re-bind the updated plan data (which was modified in-place by the worker)
            self.populate_tree()
            
            self.btn_cancel.setEnabled(True)
            self.btn_cancel.setText("Close")
        else:
             self.status_label.setText("Generation Failed.")
             self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
             self.set_buttons_enabled(True)

    def on_generation_error(self, err_msg):
        self.status_label.setText(f"Error: {err_msg}")
        self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        self.set_buttons_enabled(True)

    def set_buttons_enabled(self, enabled):
        self.btn_generate.setEnabled(enabled)
        if hasattr(self, 'btn_gen_query'): self.btn_gen_query.setEnabled(enabled)
        self.btn_cancel.setEnabled(True) 
        pass

    def populate_tree(self):
        self.tree.blockSignals(True) # excessive signals prevent
        self.tree.clear()
        
        # Map source QTreeWidgetItem -> Dialog QTreeWidgetItem
        # This allows us to reconstruct the hierarchy if the plan items are ordered parents-first
        item_map = {}
        
        for step in self.plan:
            # Try to find parent in our map
            parent_item = None
            widget = step.get('widget')
            
            if widget and hasattr(widget, 'item'):
                source_item = widget.item
                source_parent = source_item.parent()
                if source_parent in item_map:
                    parent_item = item_map[source_parent]
            
            # Create item attached to parent (or root)
            if parent_item:
                item = QTreeWidgetItem(parent_item)
            else:
                item = QTreeWidgetItem(self.tree)
                
            item.setText(0, step.get('type', 'Unknown').capitalize())
            item.setText(1, step.get('name', 'Unknown'))
            
            # Action column
            role = step.get('role', 'Create/Update')
            item.setText(2, role)
            
            # Make Name (Column 1) Editable for ALL entities only if NOT generated
            if not self.is_generated:
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            else:
                # Remove editable flag if present (default usually isn't, but let's be safe)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            # Store full step data in item
            item.setData(0, Qt.UserRole, step)
            
            # Register in map
            if widget and hasattr(widget, 'item'):
                item_map[widget.item] = item
            
            # Expand by default
            item.setExpanded(True)
            
        self.tree.expandAll()
        self.tree.blockSignals(False)
        
    def on_item_clicked(self, item, column):
        step = item.data(0, Qt.UserRole)
        if step:
            self.refresh_details(step)

    def on_item_changed(self, item, column):
        if column == 1:
            new_name = item.text(column)
            # Update the stored plan step parameters (Name only first)
            step = item.data(0, Qt.UserRole)
            if step:
                step['name'] = new_name
                if 'params' in step: 
                    step['params']['name'] = new_name
                    
                # Save initial name change
                item.setData(0, Qt.UserRole, step)
                
                # Trigger Recursive Update from this node down
                self.log_update(f"Renamed {step.get('type')} to {new_name}. Recalculating dependencies...")
                self._recursive_update(item)
                
                # Refresh details if currently selected
                if self.tree.currentItem() == item:
                     self.refresh_details(step)




    def log_update(self, message):
         if self.manager and hasattr(self.manager, 'log'):
             self.manager.log(message, "DEBUG")
         else:
             print(f"[Dialog] {message}")

    def _recursive_update(self, item):
        """
        Recursively updates 'item' and all its children based on hierarchy.
        Ensures paths and codes are strictly derived from names and parent contexts.
        """
        step = item.data(0, Qt.UserRole)
        if not step: return

        node_type = step.get('type')
        params = step.get('params', {})
        data = params.get('data')
        
        # 1. Update Self (Code & Path & inherited params)
        if data:
            parent_item = item.parent()
            parent_step = parent_item.data(0, Qt.UserRole) if parent_item else None
            parent_data = parent_step['params'].get('data') if parent_step else None
            
            # A. Inherit Context (Project Info)
            if parent_data:
                # Propagate Project Info
                for key in ['project_code', 'project_path', 'production_type']:
                    if key in parent_data:
                        data[key] = parent_data[key]
                
                # Update Parent Info
                data['parent_type'] = parent_step.get('type')
                data['parent_code'] = parent_data.get(f"{parent_step.get('type')}_code")
                data['parent_path'] = parent_data.get(f"{parent_step.get('type')}_path")
            
            # B. Update Own Code (Name-based)
            # Project is unique: Code is generated specially OR assumes user edited it?
            # User said: "Project Name changed -> dependent parameters change" 
            # In previous logic: generate_project_code(name).
            if node_type == "project":
                new_code = code_gen.generate_project_code(params['name'])
                params['code'] = new_code
                data['project_code'] = new_code.lower()
                
                # Update Description if it matches pattern?
                # params['description'] = f"{params['name']} and {new_code}" # User requested generic update
                
                # Update Project Path
                root = data.get('root_path', "")
                if root:
                    data['project_path'] = f"{root}/{new_code.lower()}".replace("\\", "/")
            
            else:
                # For others, internal 'code' param (e.g. ep01) technically stays incremental?
                # User said: "dependent parameters on the asset entity should also be changed"
                # And "Asset Type name changed -> child Asset params change"
                # We KEEP the internal param['code'] (ID) as is (e.g. ep01), 
                # but update the DATA code (name.lower()).
                
                # Update generic description
                current_code = params.get('code', '')
                if current_code:
                     params['description'] = f"{params['name']} and {current_code}"
                
                # Update Data Code
                name_key = f"{node_type}_name"
                code_key = f"{node_type}_code"
                path_key = f"{node_type}_path"
                
                data[name_key] = params['name']
                data[code_key] = params['name'].lower()
                
                # Update Data Path
                # Depends on Parent Path
                # Logic for path construction:
                
                parent_path = data.get('project_path') # Default base
                if parent_data:
                     # Usually direct parent
                     parent_path = parent_data.get(f"{parent_step.get('type')}_path")
                
                # Special Case: Asset under Asset Type (which has no data)
                is_film_seq = (node_type == "sequence" and 
                               data.get('parent_type') == "project" and 
                               data.get('production_type') == "film")

                if data.get('parent_type') == 'asset_type' or (parent_step and parent_step.get('type') == 'asset_type'):
                     # Update Asset Type context from parent Name
                     at_name = parent_step['name']
                     data['asset_type'] = at_name
                     
                     # Re-calc paths
                     # Need project path (should be in own data or context)
                     proj_path = data.get('project_path', "")
                     if proj_path:
                         slug = at_name.lower().replace(" ", "")
                         at_path = f"{proj_path}/assets/{slug}".replace("\\", "/")
                         data['asset_type_path'] = at_path
                         
                         # Update Asset Path
                         data[path_key] = f"{at_path}/{data[code_key]}".replace("\\", "/")
                         
                # Special Case: Sequence under Film Project
                elif is_film_seq:
                     # {project_path}/film/{sequence_code}
                     # parent_path here is project_path
                     data[path_key] = f"{parent_path}/film/{data[code_key]}".replace("\\", "/")
                elif parent_path:
                     # Standard: {parent_path}/{self_code}
                     # Asset Logic: {asset_type_path}/{asset_code}
                     # Asset Type Logic: {project_path}/assets/{asset_type_slug}
                     
                     if node_type == "asset_type":
                          # Asset Types are usually under Project/root, but need special handling?
                          # They are typically children of Root in tree or under "Assets" folder?
                          # In plan, they are nodes.
                          # Path: {project_path}/assets/{slug}
                           proj_path = data.get('project_path')
                           slug = params['name'].lower().replace(" ", "")
                           data[path_key] = f"{proj_path}/assets/{slug}".replace("\\", "/")
                     else:
                          # Episode, Shot, Asset, Sequence(TV)
                          data[path_key] = f"{parent_path}/{data[code_key]}".replace("\\", "/")
        
        # Save updates
        item.setData(0, Qt.UserRole, step)
        
        # 2. Recurse Children
        child_count = item.childCount()
        for i in range(child_count):
            self._recursive_update(item.child(i))

    def refresh_details(self, step):
        # Use fetched_data if available (from Query/Exec), else params (from Plan)
        fetched = step.get('fetched_data')
        params = step.get('params', {}).copy() # Start with plan params
        is_fetched = False
        
        if fetched:
             # Merge fetched into params, overwriting plan values with live values
             # But keep plan values if missing in fetched?
             # Actually, fetched object is the Source of Truth.
             # But it might be flat (no 'data' dict if not requested?)
             # Gazu objects usually flat properties.
             params.update(fetched)
             is_fetched = True
             
        node_type = step.get('type')
        
        if node_type == "project":
            self.display_project_details(params, is_fetched)
        elif node_type == "sequence":
            self.display_sequence_details(params, is_fetched)
        elif node_type == "shot":
            self.display_shot_details(params, is_fetched)
        elif node_type == "episode":
            self.display_episode_details(params, is_fetched)
        elif node_type == "task":
            self.display_task_details(params, is_fetched)
        elif node_type == "asset_type":
            self.display_asset_type_details(params, is_fetched)
        elif node_type == "asset":
            self.display_asset_details(params, is_fetched)
        else:
            # Fallback
            text = json.dumps(params, indent=4)
            self.details.setText(text)

    def _render_html(self, title, params, core_keys, update_keys, system_keys, is_fetched=False):
        """Helper to render common HTML format"""
        bg_col = "#222"
        if is_fetched:
            title += " (LIVE DATA)"
            bg_col = "#003300" # Explicit Green
            
        html = f"<html><body style='font-family:Consolas; font-size:12px; background-color:{bg_col}; color:#ddd;'>"
        html += f"<p style='margin:0; padding:5px;'><strong>{title}</strong></p>"
        html += "<hr>"
        
        def fmt(val):
            if val is None: return "null"
            if isinstance(val, str): return f'"{val}"'
            if isinstance(val, dict):
                # Pretty Print Dictionary
                import json
                pretty = json.dumps(val, indent=4)
                return f"<pre style='margin:0; font-family:Consolas; color:#aaa;'>{pretty}</pre>"
            return str(val)

        # 1. CORE (Green)
        for k in core_keys:
             val = fmt(params.get(k, ""))
             html += f"<div style='margin-bottom:2px;'><span style='color:#4CAF50; font-weight:bold;'>{k}:</span> {val}</div>"

        # 2. UPDATE (Orange)
        for k in update_keys:
             val = fmt(params.get(k)) if k in params else ""
             html += f"<div style='margin-bottom:2px;'><span style='color:#FF9800;'>{k}:</span> {val}</div>"

        # 3. SYSTEM (Grey)
        for k in system_keys:
            val = fmt(params.get(k)) if k in params else ""
            html += f"<div style='margin-bottom:2px;'><span style='color:#888; text-shadow: 0 0 2px #555;'>{k}:</span> {val}</div>"
                
        html += "</body></html>"
        self.details.setHtml(html)

    def display_asset_type_details(self, params, is_fetched=False):
        core = ["name"]
        update = ["short_name", "description", "archived"]
        system = ["id", "created_at", "updated_at", "type"]
        self._render_html("ASSET TYPE PARAMETERS", params, core, update, system, is_fetched)

    def display_asset_details(self, params, is_fetched=False):
        core = ["name"]
        update = ["code", "description", "data", "status", "canceled", "nb_frames", "is_casting_standby", "is_shared"]
        system = [
            "id", "shotgun_id", "nb_entities_out", "parent_id", "source_id", "preview_file_id", 
            "ready_for", "created_by", "created_at", "updated_at", "type", "project_id", "entity_type_id"
        ]
        self._render_html("ASSET PARAMETERS", params, core, update, system, is_fetched)

    def display_project_details(self, params, is_fetched=False):
        core = ["name", "production_type", "production_style"]
        
        # Base update keys
        potential_update = ["code", "description", "data", "file_tree", "homepage"]
        
        # Optional keys with toggles
        optional_map = {
            "fps": "use_fps",
            "ratio": "use_ratio",
            "resolution": "use_resolution",
            "has_avatar": "use_has_avatar" 
        }
        
        # Add enabled optionals
        for key, use_flag in optional_map.items():
            if params.get(use_flag):
                potential_update.append(key)
                
        update = potential_update
        
        system = [
            "id", "created_at", "updated_at", "type", "project_status_id", "man_days", 
            "nb_episodes", "episode_span", "shotgun_id", "default_preview_background_file_id", 
            "from_schedule_version_id", "max_retakes", "is_clients_isolated", "is_preview_download_allowed", 
            "is_publish_default_for_artists", "is_set_preview_automated", "ld_bitrate_compression", "hd_bitrate_compression"
        ]
        self._render_html("PROJECT PARAMETERS", params, core, update, system, is_fetched)

    def display_sequence_details(self, params, is_fetched=False):
        core = ["name"]
        update = ["code", "description", "data"]
        system = [
            "id", "project_id", "created_at", "updated_at", "type", "status", "canceled", "nb_frames", "parent_id", 
            "nb_entities_out", "is_casting_standby", "is_shared", "preview_file_id", "ready_for", 
            "shotgun_id", "source_id", "created_by", "entity_type_id"
        ]
        self._render_html("SEQUENCE PARAMETERS", params, core, update, system)

    def display_shot_details(self, params, is_fetched=False):
        core = ["name", "sequence_name"]
        update = ["code", "description", "data", "frame_in", "frame_out", "nb_frames"]
        system = [
            "id", "project_id", "created_at", "updated_at", "type", "status", "canceled", "is_casting_standby", 
            "is_shared", "preview_file_id", "ready_for", "shotgun_id", "source_id", "created_by", 
            "entity_type_id", "project_name", "nb_entities_out", "parent_id"
        ]
        self._render_html("SHOT PARAMETERS", params, core, update, system, is_fetched)

    def display_episode_details(self, params, is_fetched=False):
        core = ["name"]
        update = ["code", "description", "data"]
        system = [
            "id", "project_id", "created_at", "updated_at", "type", "status", "canceled", "nb_frames", "parent_id", 
            "nb_entities_out", "is_casting_standby", "is_shared", "preview_file_id", "ready_for", 
            "shotgun_id", "source_id", "created_by", "entity_type_id"
        ]
        self._render_html("EPISODE PARAMETERS", params, core, update, system, is_fetched)

    def display_task_details(self, params, is_fetched=False):
        core = ["name", "task_type_name", "entity_name"]
        update = ["description", "data", "due_date", "assigner_id"]
        system = [
            "id", "created_at", "updated_at", "type", "task_status_name", "priority", "duration", "estimation", 
            "completion_rate", "retake_count", "sort_order", "difficulty", "start_date", "real_start_date", 
            "end_date", "done_date", "project_id", "project_name", "entity_id", "entity_type_name", 
            "task_status_id", "task_type_id", "last_comment_date", "last_preview_file_id", 
            "nb_assets_ready", "nb_drawings", "shotgun_id"
        ]
        self._render_html("TASK PARAMETERS", params, core, update, system, is_fetched)

class EntityViewerDialog(GenerationSummaryDialog):
    def __init__(self, params, node_type, parent=None):
        # We don't call super().__init__ because we want a different UI
        # But we want to reuse the display methods. 
        # So we initialize QDialog and reuse methods.
        QDialog.__init__(self, parent)
        self.params = params
        self.node_type = node_type
        self.setWindowTitle(f"Entity Viewer: {node_type.capitalize()}")
        self.resize(500, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.details)
        
        # Display Data
        self.refresh_details()
        
        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
    def refresh_details(self):
        # Delegate to the specific display methods of the parent class
        # We can call them directly as we inherited them
        is_fetched = True # Always treat as live fetched data for viewer
        
        if self.node_type == "project":
            self.display_project_details(self.params, is_fetched)
        elif self.node_type == "sequence":
            self.display_sequence_details(self.params, is_fetched)
        elif self.node_type == "shot":
            self.display_shot_details(self.params, is_fetched)
        elif self.node_type == "episode":
            self.display_episode_details(self.params, is_fetched)
        elif self.node_type == "task":
            self.display_task_details(self.params, is_fetched)
        elif self.node_type == "asset_type":
            self.display_asset_type_details(self.params, is_fetched)
        elif self.node_type == "asset":
            self.display_asset_details(self.params, is_fetched)
        else:

            # Fallback
            import json
            text = json.dumps(self.params, indent=4)
            self.details.setText(text)

class GenerationWorker(QThread):
    progress = Signal(str)
    finished = Signal(bool)
    error = Signal(str)

    def __init__(self, manager, plan):
        super().__init__()
        self.manager = manager
        self.plan = plan

    def run(self):
        try:
            self.progress.emit("Executing Creation Plan...")
            success = self.manager.execute_plan(self.plan)
            
            if not success:
                self.finished.emit(False)
                return

            self.progress.emit("Waiting for Kitsu propagation...")
            import time
            time.sleep(2)
            
            self.progress.emit("Querying Live Data...")
            self.manager.fetch_entity_data(self.plan)
            
            self.finished.emit(True)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

class LoginDialog(QDialog):
    def __init__(self, parent=None, host="", email="", password=""):
        super().__init__(parent)
        self.setWindowTitle("Kitsu Login")
        self.resize(300, 150)
        self.host = host
        self.email = email
        self.password = password
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.host_edit = QLineEdit(self.host)
        self.host_edit.setPlaceholderText("http://localhost/api")
        form_layout.addRow("Kitsu Host:", self.host_edit)
        
        self.email_edit = QLineEdit(self.email)
        self.email_edit.setPlaceholderText("admin@example.com")
        form_layout.addRow("Email:", self.email_edit)
        
        self.pass_edit = QLineEdit(self.password)
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.pass_edit.setPlaceholderText("Password")
        form_layout.addRow("Password:", self.pass_edit)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)
        
        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.on_login)
        self.btn_login.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 5px 15px;")
        btn_layout.addWidget(self.btn_login)
        
        layout.addLayout(btn_layout)
        
    def on_login(self):
        self.host = self.host_edit.text().strip()
        self.email = self.email_edit.text().strip()
        self.password = self.pass_edit.text().strip()
        
        if not self.host or not self.email or not self.password:
             QMessageBox.warning(self, "Validation Error", "All fields are required.")
             return
             
        self.accept()
        
    def get_credentials(self):
        return self.host, self.email, self.password

