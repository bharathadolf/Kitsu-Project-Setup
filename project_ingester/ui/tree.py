from datetime import datetime, timedelta
import json

from ..utils.compat import *
from ..config import *
from ..data.rules import RULE_MAP

class NodeFrame(QFrame):
    add_child_req = Signal()
    add_sibling_req = Signal()
    delete_req = Signal()
    clicked = Signal(object)

    def __init__(self, node_type, is_root=False, rules=None, node_id=""):
        super().__init__()
        self.node_type = node_type
        self.rules = rules or {}
        self.node_id = node_id
        self.is_loaded = False
        
        # Default Naming Logic
        name_val = node_type.capitalize()
        local_index = 1
        
        if self.node_id:
            try:
                parts = str(self.node_id).split("::")
                local_index = int(parts[-1])
            except:
                pass

        if node_type == "project":
            name_val = "proj"
        elif node_type == "asset_type":
            name_val = "asset_type"
        elif node_type == "asset":
            if local_index <= 1: name_val = "New asset"
            else: name_val = f"New asset{local_index:02d}"
        elif node_type == "episode":
            name_val = f"Episode {local_index:02d}"
        elif node_type == "sequence":
            name_val = f"SQ{local_index:03d}"
        elif node_type == "shot":
            name_val = f"SH{local_index:03d}"
             
        self.properties = {"name": name_val, "code": ""}
        
        # Auto-generate 'code' if not root and has ID
        # User Req: "nth sequence will be 'seqn' n follows two digit padding"
        # "same applies for other entities code parameter"
        if not is_root and self.node_id:
            try:
                # node_id might be "1" or "1::2" etc. We want the last part.
                # But wait, shot ID "1::1" -> Shot 1 of Seq 1.
                # If we want unique code, "sh01" might conflict if global?
                # Usually Shot codes are unique per sequence.
                # "Shot#1::1" -> "sh01". "Shot#1::2" -> "sh02".
                # "Shot#2::1" -> "sh01". This looks correct for local context.
                
                parts = str(self.node_id).split("::")
                local_index = int(parts[-1])
                
                prefix_map = {
                    "sequence": "seq",
                    "shot": "sh", # Standard shot prefix
                    "episode": "ep",
                    "asset": "ast",
                    "asset_type": "at"
                }
                
                prefix = prefix_map.get(node_type.lower(), node_type[:3].lower())
                code_val = f"{prefix}{local_index:02d}"
                self.properties["code"] = code_val
            except:
                # Fallback if node_id is not parseable
                pass

        # Initial placeholders
        self.properties["data"] = {}
        
        if node_type == "project":
            self.properties.update({
                "production_type": "short", 
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "root_path": "" + name_val.lower().replace(" ", "_"),
                "production_style": "2d3d",
                "task_template": [],
                "asset_types": []
            })
            if is_root:
                 self.properties["code"] = "PRO"
                 
        elif node_type == "episode":
            self.properties.update({
                "episode_name": "Episode 1",
                "episode_order": 1
            })
            if self.node_id: 
                 self.properties["episode_name"] = f"Episode {self.node_id}"
                 try: self.properties["episode_order"] = int(self.node_id)
                 except: pass

        elif node_type == "sequence":
            # Removed sequence_code and sequence_name as requested
            pass
            
        elif node_type == "shot":
            # Removed shot_code, output_format, rv_context_group, delivery_tag as requested
            pass
            
        elif node_type == "asset_type":
             self.properties.update({
                 "asset_type_code": "AT",
                 "asset_root_path": "",
                 "publish_ruleset": ["standard"],
                 "versioning_mode": ["v001"]
             })
             
        elif node_type == "asset":
             self.properties.update({
                 "asset_code": f"AST_{self.node_id}" if self.node_id else "AST",
                 "asset_name": "New Asset",
                 "asset_category": ["prop"],
                 "primary_dcc": ["maya"],
                 "render_engine": ["arnold"],
                 "publish_enabled": True,
                 "asset_status": ["concept"]
             })

        self.is_root = is_root
        self.setFixedSize(NODE_WIDTH, NODE_HEIGHT)
        self.setMouseTracking(True)
        self.current_theme = None
        self._is_selected = False
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)

        self.name_edit = QLineEdit()
        self.name_edit.setText(node_type.capitalize())
        self.name_edit.setReadOnly(True)
        self.name_edit.setAlignment(Qt.AlignCenter)
        self.name_edit.setFocusPolicy(Qt.NoFocus)
        self.name_edit.installEventFilter(self)
        layout.addWidget(self.name_edit)


        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(2)
        btn_layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(btn_layout)

        can_add_child = bool(self.rules.get("children"))
        is_deletable = self.rules.get("deletable", True)

        if is_root:
            if can_add_child:
                btn_add = self.create_btn("+", "Add Child")
                btn_add.clicked.connect(self.add_child_req.emit)
                btn_layout.addWidget(btn_add)
        else:
            btn_sib = self.create_btn("S", "Add Sibling")
            btn_sib.clicked.connect(self.add_sibling_req.emit)
            btn_layout.addWidget(btn_sib)

            if can_add_child:
                btn_child = self.create_btn("+", "Add Child")
                btn_child.clicked.connect(self.add_child_req.emit)
                btn_layout.addWidget(btn_child)

            if is_deletable:
                self.btn_del = self.create_btn("x", "Delete Node")
                # We can style delete button specifically if needed in theme, 
                # or just leave it red as exception. For now, let's leave hardcoded red as warning.
                self.btn_del.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #c62828; 
                        border: 1px solid #c62828;
                        border-radius: {int(BTN_SIZE / 2)}px;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #e53935; }}
                """)
                self.btn_del.clicked.connect(self.delete_req.emit)
                btn_layout.addWidget(self.btn_del)
                self.btn_del.hide() # Default hidden, controlled by logic logic
            else:
                 self.btn_del = None


        layout.addStretch()
        
        if self.node_id:
            id_layout = QHBoxLayout()
            id_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            self.id_label = QLabel(self.node_id)
            self.id_label.setStyleSheet("color: #eeeeee; font-size: 8px; font-weight: bold; background: transparent;")
            id_layout.addWidget(self.id_label)
            layout.addLayout(id_layout)

    def update_styles(self, theme):
        self.current_theme = theme
        self.setStyleSheet(theme.get_node_style("selected" if self._is_selected else "base", self.node_type))

    def set_delete_visible(self, visible):
        if hasattr(self, 'btn_del') and self.btn_del:
            self.btn_del.setVisible(visible)


    def eventFilter(self, source, event):
        if source == self.name_edit and event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.clicked.emit(self)
                return True
        return super().eventFilter(source, event)

    def create_btn(self, text, tooltip):
        btn = QPushButton(text)
        btn.setFixedSize(BTN_SIZE, BTN_SIZE)
        btn.setToolTip(tooltip)
        return btn

    def enterEvent(self, event):
        if not self._is_selected and self.current_theme:
            self.setStyleSheet(self.current_theme.get_node_style("hover", self.node_type))
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_selected and self.current_theme:
            self.setStyleSheet(self.current_theme.get_node_style("base", self.node_type))
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)
            event.accept()
        else:
            super().mousePressEvent(event)

    def set_selected(self, selected):
        self._is_selected = selected
        if self.current_theme:
            state = "selected" if selected else "base"
            self.setStyleSheet(self.current_theme.get_node_style(state, self.node_type))

class HybridNodeContainer(QWidget):
    request_add_child = Signal()
    request_add_sibling = Signal()
    request_delete = Signal()
    
    def __init__(self, tree, item, node_type, is_root=False, rules=None, node_id=""):
        super().__init__()
        self.tree = tree
        self.item = item
        self.is_root = is_root

        self.is_root = is_root

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Context Menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

        self.btn_expand = QPushButton("▼")
        self.btn_expand.setFixedSize(16, 16)
        self.btn_expand.setStyleSheet("""
            QPushButton {
                background: #424242;
                color: #bdbdbd;
                border: 1px solid #616161;
                border-radius: 8px;
                font-size: 8px;
                padding: 0px;
                text-align: center;
            }
            QPushButton:hover {
                background: #616161;
                border: 1px solid #757575;
            }
        """)
        self.btn_expand.clicked.connect(self.toggle_expand)
        layout.addWidget(self.btn_expand)
        
        spacer = QFrame()
        spacer.setFixedSize(5, 2)
        spacer.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(spacer)

        self.node_frame = NodeFrame(node_type, is_root, rules, node_id)
        self.node_frame.add_child_req.connect(self.request_add_child.emit)
        self.node_frame.add_sibling_req.connect(self.request_add_sibling.emit)
        self.node_frame.delete_req.connect(self.request_delete.emit)
        layout.addWidget(self.node_frame)

        # Connect name_edit context menu to custom handler
        self.node_frame.name_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.node_frame.name_edit.customContextMenuRequested.connect(self.on_name_edit_context_menu)

        self.update_expander_icon()

    def toggle_expand(self):
        is_expanded = self.item.isExpanded()
        self.item.setExpanded(not is_expanded)
        self.update_expander_icon()

    def update_expander_icon(self):
        if self.item.childCount() == 0:
            self.btn_expand.setText("•")
            ss = self.btn_expand.styleSheet()
            self.btn_expand.setStyleSheet(ss.replace("background: #424242", "background: #1e1e1e"))
        else:
            if self.item.isExpanded():
                self.btn_expand.setText("▼")
                ss = self.btn_expand.styleSheet()
                self.btn_expand.setStyleSheet(ss.replace("background: #1e1e1e", "background: #424242"))
            else:
                self.btn_expand.setText("▶")

    def on_context_menu(self, pos):
        if self.node_frame.geometry().contains(pos):
            global_pos = self.mapToGlobal(pos)
            self._show_node_context_menu(global_pos)
        else:
            global_pos = self.mapToGlobal(pos)
            self._show_background_context_menu(global_pos)

    def on_name_edit_context_menu(self, pos):
        global_pos = self.node_frame.name_edit.mapToGlobal(pos)
        self._show_node_context_menu(global_pos)

    def _show_node_context_menu(self, global_pos):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: #d4d4d4; border: 1px solid #555; } QMenu::item:selected { background-color: #0d47a1; }")
        
        if self.node_frame.is_loaded:
            # Viewer Option
            action_viewer = QAction("Viewer", self)
            action_viewer.triggered.connect(self.open_viewer)
            menu.addAction(action_viewer)
        else:
            # Dry Run Menu
            dry_run_menu = menu.addMenu("Dry-run")
            
            action_dry_sel = QAction("Selected Entity Only", self)
            action_dry_sel.triggered.connect(lambda: self.run_dry_run(hierarchy=False))
            dry_run_menu.addAction(action_dry_sel)
            
            action_dry_hier = QAction("Includes Hierarchy", self)
            action_dry_hier.triggered.connect(lambda: self.run_dry_run(hierarchy=True))
            dry_run_menu.addAction(action_dry_hier)
            
            # Generate Menu
            gen_menu = menu.addMenu("Generate")
            
            action_gen_sel = QAction("Selected Entity Only", self)
            action_gen_sel.triggered.connect(lambda: self.run_generate(hierarchy=False))
            gen_menu.addAction(action_gen_sel)
            
            action_gen_hier = QAction("Includes Hierarchy", self)
            action_gen_hier.triggered.connect(lambda: self.run_generate(hierarchy=True))
            gen_menu.addAction(action_gen_hier)
        
        if QT_VERSION == 6:
            menu.exec(global_pos)
        else:
            menu.exec_(global_pos)

    def open_viewer(self):
        # We need to open a dialog to show properties
        # We can implement a simplified viewer dialog here or emit signal
        # Let's emit a signal or call a method on tree to bubble up
        if hasattr(self.tree, 'viewer_requested'):
             self.tree.viewer_requested.emit(self.node_frame.properties, self.node_frame.node_type)
        else:
             self.log_to_console("Viewer not connected", "WARNING")

    def _show_background_context_menu(self, global_pos):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: #d4d4d4; border: 1px solid #555; } QMenu::item:selected { background-color: #0d47a1; }")
        action = QAction("Export as JSON", self)
        action.triggered.connect(self.tree.export_structure_to_json)
        menu.addAction(action)
        
        if QT_VERSION == 6:
            menu.exec(global_pos)
        else:
            menu.exec_(global_pos)

    def run_dry_run(self, hierarchy=False):
        from ..core.setup import ProjectManager
        import json
        
        node_name = self.node_frame.properties.get("name", "Unknown")
        
        output_lines = []
        output_lines.append(f"========================================")
        output_lines.append(f"[DRY-RUN] Started for: {node_name}")
        output_lines.append(f"Mode: {'Hierarchy' if hierarchy else 'Selected Only'}")
        
        try:
            # We use a dummy logger to avoid polluting the main console with 'Resolving...' messages
            # unless an error occurs. Or we can pass self.log_to_console if we want them.
            # User wants to see the RESULTING data structure.
            manager = ProjectManager(log_callback=lambda m, l: None)
            
            # We must ensure we are connected or at least have context if needed, 
            # though build_plan tries to be standalone if possible. 
            # Verify if connection is needed for generate codes? 
            # Yes, build_plan checks connection for existing codes.
            # If not connected, it might fallback to locals or default.
            # We'll try to connect if possible or standard manager logic.
            if hasattr(manager, 'connect') and not manager.connected:
                 # Check if we can connect without credentials? No.
                 # We'll assume user might be connected or we proceed offline (best effort).
                 pass

            plan = manager.build_plan(self.item, self.tree, hierarchy=hierarchy)
            
            if not plan:
                output_lines.append("No entities found to generate.")
            else:
                for step in plan:
                    s_type = step['type']
                    s_name = step['name']
                    s_params = step['params']
                    
                    output_lines.append(f"--- {s_type}: {s_name} ---")
                    
                    # Highlight DATA if present
                    if 'data' in s_params:
                        output_lines.append("    [Computed Data]:")
                        data_str = json.dumps(s_params['data'], indent=4)
                        for line in data_str.split('\n'):
                            output_lines.append(f"        {line}")
                            
                    # Show other params briefly? or full?
                    # User specifically asked for dry run log to match Generate log which shows "data parameter".
                    # Let's show full params minus data (already shown) or just full params.
                    # Showing full params is safest.
                    
                    output_lines.append("    [All Parameters]:")
                    # Exclude 'data' from this dump to avoid duplication if it's large?
                    # or just dump everything.
                    full_str = json.dumps(s_params, indent=4)
                    for line in full_str.split('\n'):
                        output_lines.append(f"        {line}")
                        
        except Exception as e:
            output_lines.append(f"ERROR during Dry-Run: {str(e)}")
            import traceback
            output_lines.append(traceback.format_exc())
            
        output_lines.append(f"========================================")
        
        self.log_to_console("\n".join(output_lines), "INFO")

    def run_generate(self, hierarchy=False):
        from ..core.setup import ProjectManager
        try:
            manager = ProjectManager(log_callback=self.log_to_console)
            manager.process_node(self.item, self.tree, hierarchy=hierarchy)
        except Exception as e:
            self.log_to_console(f"Generate failed: {e}", "ERROR")
            import traceback
            self.log_to_console(traceback.format_exc(), "ERROR")

    def log_to_console(self, message, level="INFO"):
        # We need to bubble this up to ProjectStructureWidget -> MainWindow -> Console
        # HybridNodeContainer -> VisualTree -> ProjectStructureWidget
        if hasattr(self.tree, 'log_requested'):
             self.tree.log_requested.emit(message, level)


class VisualTree(QtWidgets.QTreeWidget):
    customItemClicked = Signal(object)
    selectionRectRequested = Signal(object, object)
    log_requested = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.watermark_text = "Custom"
        self.current_theme = None
        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.origin = QPoint()

        self.setHeaderHidden(True)
        self.setIndentation(NODE_WIDTH + 20)
        self.setAnimated(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setRootIsDecorated(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def set_theme(self, theme):
        self.current_theme = theme
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {theme.colors['bg_panel']};
                border: none;
                outline: none;
                show-decoration-selected: 0;
            }}
            QTreeWidget::item {{
                height: {ROW_HEIGHT}px;
                border: none;
                background: transparent;
            }}
            QTreeWidget::item:hover {{
                background: transparent;
            }}
            QTreeWidget::branch {{
                border-image: none;
                image: none;
                background: transparent;
            }}
        """)
        # Update connection lines color
        self.viewport().update()
        
        # Update all node frames
        for frame in self.get_all_node_frames():
            frame.update_styles(theme)

    def on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            widget = self.itemWidget(item, 0)
            if widget and hasattr(widget, 'on_context_menu'):
                # Delegate to widget context menu logic
                # Map global position because on_context_menu expects relative or global?
                # HybridNodeContainer.on_context_menu expects relative pos to widget usually if called by signal, 
                # but let's check what it uses. It uses mapToGlobal(pos).
                # If we pass tree relative pos, widget.mapToGlobal(pos) might be wrong if pos is not in widget coords.
                # However, QMenu.exec usually wants Global.
                
                # Let's call a helper on widget that takes GLOBAL pos directly to be safe, 
                # OR map pos from Tree to Widget.
                
                # Tree pos -> Global
                global_pos = self.mapToGlobal(pos)
                
                # Widget expects 'pos' to be relative to itself to do mapToGlobal(pos) inside? 
                # Wait, looking at HybridNodeContainer code:
                #    global_pos = self.mapToGlobal(pos)
                # It expects 'pos' to be local to the widget.
                
                # So we map Tree Pos -> Widget Pos
                widget_pos = widget.mapFromGlobal(global_pos)
                widget.on_context_menu(widget_pos)
                return

        menu = QtWidgets.QMenu(self)
        action = QAction("Export as JSON", self)
        action.triggered.connect(self.export_structure_to_json)
        menu.addAction(action)
        global_pos = self.mapToGlobal(pos)
        if QT_VERSION == 6:
            menu.exec(global_pos)
        else:
            menu.exec_(global_pos)

    def export_structure_to_json(self):
        import json
        data = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            node_data = self._recursive_serialize(child)
            if node_data:
                data.append(node_data)
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
                self.log_requested.emit(f"Exported JSON to: {filename}", "SUCCESS")
            except Exception as e:
                self.log_requested.emit(f"Export failed: {e}", "ERROR")

    def _recursive_serialize(self, item):
        widget = self.itemWidget(item, 0)
        if not widget:
            return None
        node_data = {
            "type": widget.node_frame.node_type,
            "properties": widget.node_frame.properties.copy(),
            "children": []
        }
        for i in range(item.childCount()):
            child = item.child(i)
            child_data = self._recursive_serialize(child)
            if child_data:
                node_data["children"].append(child_data)
        return node_data

    def drawBranches(self, painter, rect, index):
        pass

    def get_all_node_frames(self):
        frames = []
        iterator = QtWidgets.QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            widget = self.itemWidget(item, 0)
            if widget and hasattr(widget, 'node_frame'):
                frames.append(widget.node_frame)
            iterator += 1
        return frames

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint() if QT_VERSION >= 6 else event.pos()
            self.origin = pos
            self.rubberband.setGeometry(QtCore.QRect(self.origin, QSize()))
            self.rubberband.show()
            return 
        if event.button() == Qt.RightButton:
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull() and self.rubberband.isVisible():
             pos = event.position().toPoint() if QT_VERSION >= 6 else event.pos()
             self.rubberband.setGeometry(QtCore.QRect(self.origin, pos).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rubberband.isVisible():
            rect = self.rubberband.geometry()
            self.rubberband.hide()
            self.selectionRectRequested.emit(rect, QApplication.keyboardModifiers())
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter()
        if painter.begin(self.viewport()):
            try:
                painter.setRenderHint(QPainter.Antialiasing)
                
                # --- WATERMARK ---
                if self.watermark_text:
                    painter.save()
                    font = QtGui.QFont("Arial", 40, QtGui.QFont.Bold)
                    painter.setFont(font)
                    
                    # Color based on theme logic or fixed dim color
                    text_color = QColor(255, 255, 255, 20) # Very faint white/gray
                    if self.current_theme and 'Light' in self.current_theme.name:
                         text_color = QColor(0, 0, 0, 20)
                    
                    painter.setPen(text_color)
                    
                    rect = self.viewport().rect()
                    painter.drawText(rect, Qt.AlignCenter, self.watermark_text.upper())
                    painter.restore()
                # -----------------
                
                line_color = "#546e7a" # Fallback
                if self.current_theme:
                    line_color = self.current_theme.colors['border']
                    
                pen = QPen(QColor(line_color))
                pen.setWidth(2)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                
                count = self.topLevelItemCount()
                for i in range(count):
                    self.draw_recursive(painter, self.topLevelItem(i))
            finally:
                painter.end()
                
    def draw_recursive(self, painter, item):
        child_count = item.childCount()
        for i in range(child_count):
            child = item.child(i)
            self.draw_connector(painter, item, child)
            if item.isExpanded():
                self.draw_recursive(painter, child)
                
    def draw_connector(self, painter, parent, child):
        parent_w = self.itemWidget(parent, 0)
        child_w = self.itemWidget(child, 0)
        if not parent_w or not child_w:
            return
        if not child_w.isVisible():
            return
        
        if hasattr(parent_w, 'node_frame'):
            # Logic without save/restore as we don't modify painter state
            p_frame = parent_w.node_frame
            p_origin = p_frame.mapTo(self.viewport(), QPoint(int(p_frame.width() / 2), p_frame.height()))
            start_point = p_origin
            
            c_btn = child_w.btn_expand
            c_origin = c_btn.mapTo(self.viewport(), QPoint(0, int(c_btn.height() / 2)))
            end_point = c_origin
            
            dy = end_point.y() - start_point.y()
            dx = end_point.x() - start_point.x()
            c1 = QPoint(start_point.x(), start_point.y() + int(dy * 0.5))
            c2 = QPoint(end_point.x() - int(dx * 0.5), end_point.y())

            path = QPainterPath()
            path.moveTo(start_point)
            path.cubicTo(c1, c2, end_point)
            painter.drawPath(path)

class VisualTree(QtWidgets.QTreeWidget):
    customItemClicked = Signal(object)
    selectionRectRequested = Signal(object, object)
    log_requested = Signal(str, str)
    viewer_requested = Signal(dict, str) # params, type
    
    def __init__(self):
        super().__init__()
        self.watermark_text = "Custom"
        self.origin = QtCore.QPoint()
        self.rubberband = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self.setUniformRowHeights(True)
        self.setIndentation(NODE_WIDTH + 20)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setMouseTracking(True)
        self.setRootIsDecorated(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)
        
        self.current_theme = None

        # Set up custom branch drawing
        self.setAllColumnsShowFocus(True)
        self.header().hide()
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        
        # Set up stylesheet for transparent background and no borders
        if self.current_theme:
            self.set_theme(self.current_theme)

    def set_theme(self, theme):
        self.current_theme = theme
        # Set up stylesheet for transparent background and no borders
        self.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                height: {ROW_HEIGHT}px;
                background: transparent;
            }}
            QTreeWidget::item:hover {{
                background: transparent;
            }}
            QTreeWidget::branch {{
                border-image: none;
                image: none;
                background: transparent;
            }}
        """)
        # Update connection lines color
        self.viewport().update()
        
        # Update all node frames
        for frame in self.get_all_node_frames():
            frame.update_styles(theme)

    def on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            widget = self.itemWidget(item, 0)
            if widget and hasattr(widget, 'on_context_menu'):
                # Delegate to widget context menu logic
                # Map global position because on_context_menu expects relative or global?
                # HybridNodeContainer.on_context_menu expects relative pos to widget usually if called by signal, 
                # but let's check what it uses. It uses mapToGlobal(pos).
                # If we pass tree relative pos, widget.mapToGlobal(pos) might be wrong if pos is not in widget coords.
                # However, QMenu.exec usually wants Global.
                
                # Let's call a helper on widget that takes GLOBAL pos directly to be safe, 
                # OR map pos from Tree to Widget.
                
                # Tree pos -> Global
                global_pos = self.mapToGlobal(pos)
                
                # Widget expects 'pos' to be local to the widget.
                # Wait, looking at HybridNodeContainer code:
                #    global_pos = self.mapToGlobal(pos)
                # It expects 'pos' to be local to the widget.
                
                # So we map Tree Pos -> Widget Pos
                widget_pos = widget.mapFromGlobal(global_pos)
                widget.on_context_menu(widget_pos)
                return

        menu = QtWidgets.QMenu(self)
        action = QAction("Export as JSON", self)
        action.triggered.connect(self.export_structure_to_json)
        menu.addAction(action)
        global_pos = self.mapToGlobal(pos)
        if QT_VERSION == 6:
            menu.exec(global_pos)
        else:
            menu.exec_(global_pos)

    def export_structure_to_json(self):
        import json
        data = []
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            child = root.child(i)
            node_data = self._recursive_serialize(child)
            if node_data:
                data.append(node_data)
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export JSON", "", "JSON Files (*.json)")
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
                self.log_requested.emit(f"Exported JSON to: {filename}", "SUCCESS")
            except Exception as e:
                self.log_requested.emit(f"Export failed: {e}", "ERROR")

    def _recursive_serialize(self, item):
        widget = self.itemWidget(item, 0)
        if not widget:
            return None
        node_data = {
            "type": widget.node_frame.node_type,
            "properties": widget.node_frame.properties.copy(),
            "children": []
        }
        for i in range(item.childCount()):
            child = item.child(i)
            child_data = self._recursive_serialize(child)
            if child_data:
                node_data["children"].append(child_data)
        return node_data

    def drawBranches(self, painter, rect, index):
        pass

    def get_all_node_frames(self):
        frames = []
        iterator = QtWidgets.QTreeWidgetItemIterator(self)
        while iterator.value():
            item = iterator.value()
            widget = self.itemWidget(item, 0)
            if widget and hasattr(widget, 'node_frame'):
                frames.append(widget.node_frame)
            iterator += 1
        return frames

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint() if QT_VERSION >= 6 else event.pos()
            self.origin = pos
            self.rubberband.setGeometry(QtCore.QRect(self.origin, QSize()))
            self.rubberband.show()
            return 
        if event.button() == Qt.RightButton:
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.origin.isNull() and self.rubberband.isVisible():
             pos = event.position().toPoint() if QT_VERSION >= 6 else event.pos()
             self.rubberband.setGeometry(QtCore.QRect(self.origin, pos).normalized())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.rubberband.isVisible():
            rect = self.rubberband.geometry()
            self.rubberband.hide()
            self.selectionRectRequested.emit(rect, QApplication.keyboardModifiers())
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter()
        if painter.begin(self.viewport()):
            try:
                painter.setRenderHint(QPainter.Antialiasing)
                
                # --- WATERMARK ---
                if self.watermark_text:
                    painter.save()
                    font = QtGui.QFont("Arial", 40, QtGui.QFont.Bold)
                    painter.setFont(font)
                    
                    # Color based on theme logic or fixed dim color
                    text_color = QColor(255, 255, 255, 20) # Very faint white/gray
                    if self.current_theme and 'Light' in self.current_theme.name:
                         text_color = QColor(0, 0, 0, 20)
                    
                    painter.setPen(text_color)
                    
                    rect = self.viewport().rect()
                    painter.drawText(rect, Qt.AlignCenter, self.watermark_text.upper())
                    painter.restore()
                # -----------------
                
                line_color = "#546e7a" # Fallback
                if self.current_theme:
                    line_color = self.current_theme.colors['border']
                    
                pen = QPen(QColor(line_color))
                pen.setWidth(2)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                
                count = self.topLevelItemCount()
                for i in range(count):
                    self.draw_recursive(painter, self.topLevelItem(i))
            finally:
                painter.end()
                
    def draw_recursive(self, painter, item):
        child_count = item.childCount()
        for i in range(child_count):
            child = item.child(i)
            self.draw_connector(painter, item, child)
            if item.isExpanded():
                self.draw_recursive(painter, child)
                
    def draw_connector(self, painter, parent, child):
        parent_w = self.itemWidget(parent, 0)
        child_w = self.itemWidget(child, 0)
        if not parent_w or not child_w:
            return
        if not child_w.isVisible():
            return
        
        if hasattr(parent_w, 'node_frame'):
            # Logic without save/restore as we don't modify painter state
            p_frame = parent_w.node_frame
            p_origin = p_frame.mapTo(self.viewport(), QPoint(int(p_frame.width() / 2), p_frame.height()))
            start_point = p_origin
            
            c_btn = child_w.btn_expand
            c_origin = c_btn.mapTo(self.viewport(), QPoint(0, int(c_btn.height() / 2)))
            end_point = c_origin
            
            dy = end_point.y() - start_point.y()
            dx = end_point.x() - start_point.x()
            c1 = QPoint(start_point.x(), start_point.y() + int(dy * 0.5))
            c2 = QPoint(end_point.x() - int(dx * 0.5), end_point.y())

            path = QPainterPath()
            path.moveTo(start_point)
            path.cubicTo(c1, c2, end_point)
            painter.drawPath(path)

class ProjectStructureWidget(QWidget):
    node_selected = Signal(object)
    log_message = Signal(str, str)
    viewer_requested = Signal(dict, str) # Bubble up
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_template = "Custom"
        self.current_theme = None
        self.selected_nodes = []
        self.setup_ui()
        
    def set_theme(self, theme):
        self.current_theme = theme
        self.header_label.setStyleSheet(theme.get_header_style(theme.colors['accent']))
        self.tree.set_theme(theme)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.header_label = QLabel("Project Structure")
        # Style will be set by set_theme initially in MainWindow
        self.header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.header_label)
        
        self.tree = VisualTree()
        self.tree.selectionRectRequested.connect(self.on_rubberband_selection)
        self.tree.log_requested.connect(self.log_message.emit)
        self.tree.viewer_requested.connect(self.viewer_requested.emit)
        layout.addWidget(self.tree)
        
        # Status Label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-style: italic; padding: 5px; background-color: #1e1e1e;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
    def apply_template(self, template_name):
        self.log_message.emit(f"Applied Template: {template_name}", "INFO")
        self.current_template = template_name
        self.tree.watermark_text = template_name # Set Watermark
        self.tree.viewport().update() # Trigger repaint
        self.tree.clear()
        rules = RULE_MAP.get(template_name, {})
        project_rules = rules.get("project", {})
        
        type_map = {
            "Feature Film": "movie",
            "TV Show": "tvshow",
            "Shots Only": "short",
            "Asset Only": "commercial",
            "Custom": "short"
        }
        prod_type = type_map.get(template_name, "short")
        
        item = self.add_node(None, "project", is_root=True, rules=project_rules)
        widget = self.tree.itemWidget(item, 0)
        if widget and widget.node_frame:
            widget.node_frame.properties["production_type"] = prod_type
            
        self.populate_default_structure(item, "project")

    def populate_default_structure(self, parent_item, parent_type):
        full_rules = RULE_MAP.get(self.current_template, {})
        parent_rules = full_rules.get(parent_type, {})
        children_types = parent_rules.get("children", [])
        
        for child_type in children_types:
            new_item = self.add_node(parent_item, child_type)
            self.populate_default_structure(new_item, child_type)

    def add_node(self, parent_item, node_type, is_root=False, rules=None):
        item = QtWidgets.QTreeWidgetItem(parent_item if parent_item else self.tree)
        item.setSizeHint(0, QSize(NODE_WIDTH + 80, ROW_HEIGHT))
        
        if not rules:
            full_rules = RULE_MAP.get(self.current_template, {})
            rules = full_rules.get(node_type, {})

        node_id = ""
        if not is_root and parent_item:
             count = parent_item.childCount()
             idx = parent_item.indexOfChild(item)
             sibling_num = idx + 1
             parent_widget = self.tree.itemWidget(parent_item, 0)
             parent_id = ""
             if parent_widget and hasattr(parent_widget, 'node_frame'):
                  parent_id = parent_widget.node_frame.node_id
             
             if not parent_id: node_id = str(sibling_num)
             else: node_id = f"{parent_id}::{sibling_num}"

        widget = HybridNodeContainer(self.tree, item, node_type, is_root, rules, node_id)
        if self.current_theme:
            widget.node_frame.update_styles(self.current_theme)
            
        widget.request_add_child.connect(lambda: self.on_add_child(item, node_type))
        widget.request_add_sibling.connect(lambda: self.on_add_sibling(item, node_type))
        widget.request_delete.connect(lambda: self.on_delete_node(item))
        widget.node_frame.clicked.connect(self.on_node_clicked)
        
        self.tree.setItemWidget(item, 0, widget)
        
        if parent_item:
            parent_item.setExpanded(True)
            parent_widget = self.tree.itemWidget(parent_item, 0)
            if parent_widget: parent_widget.update_expander_icon()
            self.refresh_siblings_buttons(parent_item)
            

            
        return item


    def on_node_clicked(self, node_frame):
        mods = QApplication.keyboardModifiers()
        if mods & Qt.ControlModifier:
            if node_frame in self.selected_nodes: self.deselect_node(node_frame)
            else: self.select_node(node_frame, add=True)
        else:
            self.clear_selection()
            self.select_node(node_frame, add=True)

    def select_node(self, node_frame, add=False):
        if not add: self.clear_selection()
        if node_frame not in self.selected_nodes:
            self.selected_nodes.append(node_frame)
            node_frame.set_selected(True)
            self.log_message.emit(f"Selected Node: {node_frame.properties.get('name', 'Unknown')}", "INFO")
        self.node_selected.emit(self.selected_nodes)

    def deselect_node(self, node_frame):
         if node_frame in self.selected_nodes:
             self.selected_nodes.remove(node_frame)
             node_frame.set_selected(False)
         self.node_selected.emit(self.selected_nodes)
             
    def clear_selection(self):
         for n in self.selected_nodes:
             try:
                 if n and n.isVisible(): n.set_selected(False)
             except RuntimeError: pass
         self.selected_nodes = []
         self.node_selected.emit(self.selected_nodes)
         
    def on_rubberband_selection(self, rect, modifiers):
        if not (modifiers & Qt.ControlModifier): self.clear_selection()
        all_frames = self.tree.get_all_node_frames()
        for frame in all_frames:
             frame_pos = frame.mapTo(self.tree, QPoint(0,0))
             frame_rect = QtCore.QRect(frame_pos, frame.size())
             if rect.intersects(frame_rect): self.select_node(frame, add=True)

    def on_add_child(self, parent_item, parent_type):
        full_rules = RULE_MAP.get(self.current_template, {})
        parent_rules = full_rules.get(parent_type, {})
        allowed_children = parent_rules.get("children", [])
        if not allowed_children: return
            
        if len(allowed_children) == 1:
            child_type = allowed_children[0]
            self.add_node(parent_item, child_type)
        else:
            menu = QtWidgets.QMenu(self.tree)
            menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: #d4d4d4; border: 1px solid #555; } QMenu::item:selected { background-color: #0d47a1; }")
            for child_type in allowed_children:
                action = QAction(child_type.capitalize(), self.tree)
                action.triggered.connect(lambda checked=False, ct=child_type: self.add_node(parent_item, ct))
                menu.addAction(action)
            pos = QtGui.QCursor.pos()
            if QT_VERSION == 6: menu.exec(pos)
            else: menu.exec_(pos)
        
    def on_add_sibling(self, item, node_type):
        parent_item = item.parent()
        if not parent_item: return 
        self.add_node(parent_item, node_type)
        
    def on_delete_node(self, item):
        parent = item.parent()
        if parent:
            parent.removeChild(item)
            parent_widget = self.tree.itemWidget(parent, 0)
            if parent_widget: parent_widget.update_expander_icon()
            self.refresh_siblings_buttons(parent)

    def refresh_siblings_buttons(self, parent_item):
        if not parent_item: return
        child_count = parent_item.childCount()
        for i in range(child_count):
            child = parent_item.child(i)
            widget = self.tree.itemWidget(child, 0)
            if widget and hasattr(widget, 'node_frame'):
                # Rule: First sibling (index 0) cannot be deleted.
                # Rule: Only the LAST added sibling (latest) can be deleted.
                is_last_sibling = (i == child_count - 1)
                can_delete = (i > 0) and is_last_sibling
                widget.node_frame.set_delete_visible(can_delete)

    def populate_from_structure(self, data):
        """
        Rebuilds the tree based on the nested dictionary returned by FolderMapper.
        data format: { 'type':..., 'name':..., 'children': [ ... ] }
        """
        self.tree.clear()
        
        # 1. Root
        root_type = data.get('type', 'project')
        # Ensure rules exist? We assume template is already set or we should set it?
        # The App should sets template before calling this if needed.
        
        root_item = self.add_node(None, root_type, is_root=True)
        self._apply_data_to_node(root_item, data)
        self.tree.expandItem(root_item)
        
        # 2. Children
        self._recursive_populate(root_item, data.get('children', []))
        
    def _recursive_populate(self, parent_item, children_data):
        for child in children_data:
            node_type = child.get('type')
            
            # Check if allowed by rules? 
            # add_node checks NOTHING regarding validity usually, it just adds.
            # But the UI buttons invoke 'on_add_child' which checks rules.
            # Here we force add.
            
            new_item = self.add_node(parent_item, node_type)
            self._apply_data_to_node(new_item, child)
            
            # Recurse
            self._recursive_populate(new_item, child.get('children', []))

    def _apply_data_to_node(self, item, data):
        widget = self.tree.itemWidget(item, 0)
        if widget and widget.node_frame:
            name = data.get('name', 'Unknown')
            widget.node_frame.properties['name'] = name
            widget.node_frame.name_edit.setText(name)
            
            # Update Code if possible? 
            # The node_frame might have auto-generated a code based on "New Asset".
            # We should probably re-trigger code generation or let the user see the current state.
            # For now, we trust the name.
            
            # Also store path in extra properties if we want to use it later?
            if 'path' in data:
                path_val = data['path']
                widget.node_frame.properties['local_scan_path'] = path_val
                
                # FIX: If this is the Project node, we must set 'root_path' 
                # so the ProjectForm (Panel 2) picks it up.
                if widget.node_frame.node_type == 'project':
                    widget.node_frame.properties['root_path'] = path_val
                    
                    # Also update the special 'data' dictionary which ProjectForm uses
                    if 'data' not in widget.node_frame.properties:
                        widget.node_frame.properties['data'] = {}
                    
                    # Ensure it's a dict (it might be None if initialized empty)
                    if not isinstance(widget.node_frame.properties['data'], dict):
                        widget.node_frame.properties['data'] = {}
                        
                    widget.node_frame.properties['data']['root_path'] = path_val



