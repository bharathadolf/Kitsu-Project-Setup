from ..utils.compat import *
from ..utils import code_gen
import json

class GenerationSummaryDialog(QDialog):
    def __init__(self, plan, manager=None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.manager = manager
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
        self.btn_generate.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_generate)
        
        layout.addLayout(btn_layout)

    def on_generate_query(self):
        if not self.manager: return
        
        # 1. Execute
        self.status_label.setText("Generating Project... Please wait.")
        self.btn_generate.setEnabled(False)
        self.btn_gen_query.setEnabled(False)
        self.btn_cancel.setEnabled(False) # Temporarily lock
        QApplication.processEvents() # Force UI Update
        
        try:
            success = self.manager.execute_plan(self.plan)
            
            if not success:
                self.status_label.setText("Generation Failed. Check Console.")
                self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                self.btn_cancel.setEnabled(True)
                return

            # 2. Query (Actually reusing data from execute_plan usually suffices if we updated it, 
            # but explicit fetch if needed. We updated setup.py to store in 'fetched_data'.)
            self.status_label.setText("Project Created. Querying Data...")
            QApplication.processEvents()
            
            # We already have data in self.plan from execute_plan (passed by ref)
            # But if we strictly want a separate query Step, call fetch_entity_data
            # self.manager.fetch_entity_data(self.plan) 
            
            self.status_label.setText("Data Fetched Successfully.")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold; margin-left: 10px;")
            
            # Refresh current view
            current = self.tree.currentItem()
            if current:
                self.on_item_clicked(current, 0)
                
            # Keep buttons disabled except Cancel (to Close)
            self.btn_cancel.setEnabled(True)
            self.btn_cancel.setText("Close")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.btn_cancel.setEnabled(True)

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
            
            # Make Name (Column 1) Editable for ALL entities
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            
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
            # Update the stored plan step parameters
            step = item.data(0, Qt.UserRole)
            if step:
                # Update Name
                step['name'] = new_name
                if 'params' in step: 
                    step['params']['name'] = new_name
                    
                    # Update Code (Dynamic Dependency)
                    node_type = step.get('type')
                    new_code = None
                    
                    if node_type == "project":
                        new_code = code_gen.generate_project_code(new_name)
                    
                    # For other entities (Episode, Sequence, Shot, Asset), 
                    # the code follows a strict pattern (counters) and should NOT change 
                    # just because the user edits the descriptive Name field.
                        
                    if new_code:
                         step['params']['code'] = new_code
                
                # Update Description for entities where description = Name + Code
                # (As per user request: "changing the name column in the panel1... change description parameter")
                if node_type in ["episode", "sequence", "shot", "asset"]:
                     current_code = step['params'].get('code', '')
                     # If project, code changed, we use new_code. For others, code remains mostly unless we regenerte it? 
                     # For Episode/Seq/Shot code is usually fixed unless logic changes. 
                     # User said "changing name field will change code at run time for project entity" 
                     # "for other entities... change description because description is {name} and {code}"
                     
                     # Check if we have code
                     if current_code:
                         new_desc = f"{new_name} and {current_code}"
                         step['params']['description'] = new_desc
                         # Also update top-level 'description' if it exists in step (though step usually flat dict or has params)
                         # Step structure: {type, name, params: {...}}

                
                # Save the updated data back to the item to ensure persistence
                item.setData(0, Qt.UserRole, step)

                # Refresh details panel to show updated params
                self.refresh_details(step)


    def refresh_details(self, step):
        # Use fetched_data if available (from Query/Exec), else params (from Plan)
        params = step.get('fetched_data')
        is_fetched = False
        
        if not params:
             params = step.get('params', {})
        else:
             is_fetched = True
             
        node_type = step.get('type')
        
        # If fetched, we might want to convert some values or ensure format matches expected
        # But generally display_* methods handle dicts.
        
        # Special handling: Add a header or note if Fetched
        
        if node_type == "project":
            self.display_project_details(params)
        elif node_type == "sequence":
            self.display_sequence_details(params)
        elif node_type == "shot":
            self.display_shot_details(params)
        elif node_type == "episode":
            self.display_episode_details(params)
        elif node_type == "task":
            self.display_task_details(params)
        elif node_type == "asset_type":
            self.display_asset_type_details(params)
        elif node_type == "asset":
            self.display_asset_details(params)
        else:
            # Fallback
            text = json.dumps(params, indent=4)
            self.details.setText(text)

    def _render_html(self, title, params, core_keys, update_keys, system_keys):
        """Helper to render common HTML format"""
        html = "<html><body style='font-family:Consolas; font-size:12px; background-color:#222; color:#ddd;'>"
        html += f"<p style='margin:0; padding:5px;'><strong>{title}</strong> (Full Schema)</p>"
        html += "<hr>"
        
        def fmt(val):
            if val is None: return "null"
            if isinstance(val, str): return f'"{val}"'
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

    def display_asset_type_details(self, params):
        core = ["name"]
        update = ["short_name", "description", "archived"]
        system = ["id", "created_at", "updated_at", "type"]
        self._render_html("ASSET TYPE PARAMETERS", params, core, update, system)

    def display_asset_details(self, params):
        core = ["name", "entity_type_id"]
        update = ["code", "description", "data", "status", "canceled", "nb_frames", "is_casting_standby", "is_shared"]
        system = [
            "id", "shotgun_id", "nb_entities_out", "parent_id", "source_id", "preview_file_id", 
            "ready_for", "created_by", "created_at", "updated_at", "type", "project_id"
        ]
        self._render_html("ASSET PARAMETERS", params, core, update, system)

    def display_project_details(self, params):
        core = ["name", "production_type", "production_style"]
        update = ["code", "description", "fps", "ratio", "resolution", "start_date", "end_date", "data", "file_tree", "homepage"]
        system = [
            "id", "created_at", "updated_at", "type", "project_status_id", "has_avatar", "man_days", 
            "nb_episodes", "episode_span", "shotgun_id", "default_preview_background_file_id", 
            "from_schedule_version_id", "max_retakes", "is_clients_isolated", "is_preview_download_allowed", 
            "is_publish_default_for_artists", "is_set_preview_automated", "ld_bitrate_compression", "hd_bitrate_compression"
        ]
        self._render_html("PROJECT PARAMETERS", params, core, update, system)

    def display_sequence_details(self, params):
        core = ["name"]
        update = ["code", "description", "data"]
        system = [
            "id", "project_id", "created_at", "updated_at", "type", "status", "canceled", "nb_frames", "parent_id", 
            "nb_entities_out", "is_casting_standby", "is_shared", "preview_file_id", "ready_for", 
            "shotgun_id", "source_id", "created_by", "entity_type_id"
        ]
        self._render_html("SEQUENCE PARAMETERS", params, core, update, system)

    def display_shot_details(self, params):
        core = ["name", "sequence_name"]
        update = ["code", "description", "data", "frame_in", "frame_out", "nb_frames"]
        system = [
            "id", "project_id", "created_at", "updated_at", "type", "status", "canceled", "is_casting_standby", 
            "is_shared", "preview_file_id", "ready_for", "shotgun_id", "source_id", "created_by", 
            "entity_type_id", "project_name", "nb_entities_out", "parent_id"
        ]
        self._render_html("SHOT PARAMETERS", params, core, update, system)

    def display_episode_details(self, params):
        core = ["name"]
        update = ["code", "description", "data"]
        system = [
            "id", "project_id", "created_at", "updated_at", "type", "status", "canceled", "nb_frames", "parent_id", 
            "nb_entities_out", "is_casting_standby", "is_shared", "preview_file_id", "ready_for", 
            "shotgun_id", "source_id", "created_by", "entity_type_id"
        ]
        self._render_html("EPISODE PARAMETERS", params, core, update, system)

    def display_task_details(self, params):
        core = ["name", "task_type_name", "entity_name"]
        update = ["description", "data", "due_date", "assigner_id"]
        system = [
            "id", "created_at", "updated_at", "type", "task_status_name", "priority", "duration", "estimation", 
            "completion_rate", "retake_count", "sort_order", "difficulty", "start_date", "real_start_date", 
            "end_date", "done_date", "project_id", "project_name", "entity_id", "entity_type_name", 
            "task_status_id", "task_type_id", "last_comment_date", "last_preview_file_id", 
            "nb_assets_ready", "nb_drawings", "shotgun_id"
        ]
        self._render_html("TASK PARAMETERS", params, core, update, system)
