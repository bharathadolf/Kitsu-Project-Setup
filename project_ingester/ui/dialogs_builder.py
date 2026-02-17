from ..utils.compat import *
from ..data.rules import RULE_MAP
from .themes import DARK_THEME # Fallback
import os
# Fallback removed, relying on compat

from ..utils.compat import * 


class DropLineEdit(QLineEdit):
    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Select or Drag Project Folder here...")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self.setText(path)
                    self.file_dropped.emit(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class BuilderTreeWidget(QTreeWidget):
    folder_dropped = Signal(object, str) # Item, Path
    root_dropped = Signal(str) # Path
    item_moved = Signal(object, object) # Item, TargetItem
    request_menu = Signal(object, object) # Item, GlobalPos

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTreeWidget.DragDrop) # Enable Dragging too
        self.setDropIndicatorShown(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def on_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            global_pos = self.mapToGlobal(pos)
            self.request_menu.emit(item, global_pos)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # Internal drag
            super().dragEnterEvent(event)
            event.accept()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
            event.accept()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # External File Drop
            urls = event.mimeData().urls()
            target_item = self.itemAt(event.pos())
            
            if target_item:
                for url in urls:
                    path = url.toLocalFile()
                    if os.path.isdir(path):
                        self.folder_dropped.emit(target_item, path)
            else:
                # Dropped on empty space
                if self.topLevelItemCount() == 0:
                     for url in urls:
                        path = url.toLocalFile()
                        if os.path.isdir(path):
                            self.root_dropped.emit(path)
                            break # Only take one root
            
            event.acceptProposedAction()
        else:
            # Internal Move (Drag and Drop within tree)
            target_item = self.itemAt(event.pos())
            selected_items = self.selectedItems()
            
            if target_item and selected_items:
                # Emit signal to let Dialog handle logic
                # We assume single selection or handle multiple
                for item in selected_items:
                    self.item_moved.emit(item, target_item)
            
            event.ignore() # We don't want default QTreeWidget internal move behavior (which clones/moves items purely visually)
            # We want to handle it logically

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.topLevelItemCount() == 0:
            painter = QPainter(self.viewport())
            painter.save()
            
            # Draw Text
            text = "Drag n drop root folder"
            font = QtGui.QFont("Arial", 14, QtGui.QFont.Bold)
            painter.setFont(font)
            
            # Center Text
            rect = self.viewport().rect()
            
            # Get color from theme? Or hardcode decent grey
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(rect, Qt.AlignCenter, text)
            
            painter.restore()

class FolderBuilderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Build Project from Folders")
        self.resize(800, 600)
        self.result_data = None
        
        # Data storage
        self.project_root = None
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Top Bar: Template & Project Root
        form_layout = QFormLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItems(list(RULE_MAP.keys()))
        self.template_combo.currentIndexChanged.connect(self.refresh_tree)
        form_layout.addRow("Template:", self.template_combo)
        
        root_layout = QHBoxLayout()
        self.root_edit = DropLineEdit()
        self.root_edit.setReadOnly(True)
        self.root_edit.file_dropped.connect(self.on_root_dropped)
        
        self.root_btn = QPushButton("Browse...")
        self.root_btn.clicked.connect(self.browse_project_root)
        root_layout.addWidget(self.root_edit)
        root_layout.addWidget(self.root_btn)
        form_layout.addRow("Project Root:", root_layout)
        
        layout.addLayout(form_layout)
        
        # 2. Tree Widget
        # Columns: [Entity/Instance Name, Folder Mapping/Path, Checkbox (implicit)]
        # 3. Tree Widget
        # Columns: [Entity/Instance Name, Folder Mapping/Path, Checkbox (implicit)]
        self.tree = BuilderTreeWidget()
        self.tree.folder_dropped.connect(self.handle_drop)
        self.tree.root_dropped.connect(self.on_root_dropped)
        self.tree.item_moved.connect(self.on_item_moved)
        self.tree.request_menu.connect(self.show_context_menu)
        
        self.tree.setHeaderLabels(["Entity / Instance", "Mapped Folder", "Info"])
        self.tree.setColumnWidth(0, 300)
        self.tree.setColumnWidth(1, 400)
        self.tree.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.tree)
        
        # 3. Dialog Buttons
        btn_box = QHBoxLayout()
        self.status_label = QLabel("Select a project root to begin.")
        btn_box.addWidget(self.status_label)
        btn_box.addStretch()
        
        build_btn = QPushButton("Build")
        build_btn.clicked.connect(self.on_build)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_box.addWidget(cancel_btn)
        btn_box.addWidget(build_btn)
        
        # 4. Stats / Log Widget (Bottom Right essentially, but we put it below tree for now or split)
        # Requirement: "at the right bottom of the tool ,there should be log like thing"
        # Let's use a Splitter for Tree and Log, or just put Log at bottom.
        # User said "right bottom", maybe next to buttons? Or below tree?
        # Let's put it below the tree for visibility.
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(100)
        self.log_edit.setPlaceholderText("Statistics will appear here...")
        layout.addWidget(self.log_edit)

        layout.addLayout(btn_box)

    def browse_project_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Root Folder")
        if folder:
            self.project_root = folder
            self.root_edit.setText(folder)
            self.refresh_tree()

    def on_root_dropped(self, folder_path):
        """
        Calculates tree when folder is dropped.
        """
        self.project_root = folder_path
        self.refresh_tree()

    def calculate_stats(self):
        """
        Traverses the tree to count mapped/unmapped entities and updates the log.
        """
        root = self.tree.topLevelItem(0)
        if not root:
             self.log_edit.setText("No project loaded.")
             return

        stats = {
            "level_1_count": 0,
            "level_2_count": 0,
            "unmapped_categories": 0,
            "mapped_categories": 0
        }

        # Helper to recurse
        def traverse(item):
            data = item.data(0, Qt.UserRole)
            if not data: return

            kind = data.get('node_kind')
            
            if kind == 'category':
                # Check if mapped
                widget = self.tree.itemWidget(item, 1)
                is_mapped = False
                if isinstance(widget, QComboBox):
                    if widget.currentData(): # Has a path selected
                        is_mapped = True
                
                if is_mapped:
                    stats["mapped_categories"] += 1
                else:
                    stats["unmapped_categories"] += 1
                
                # Recurse children (Instances)
                for i in range(item.childCount()):
                    traverse(item.child(i))

            elif kind == 'instance':
                # Determine level?
                # Root is level 0 (Project)
                # Children of Root Category are Level 1
                # Children of Level 1 Category are Level 2
                
                # We can approximate by depth or check parent chain
                parent = item.parent()

                if parent: # Not root project
                    # Parent is a Category
                    grandparent = parent.parent()
                    if grandparent == root:
                         stats["level_1_count"] += 1
                    elif grandparent and grandparent.parent() and grandparent.parent().parent() == root:
                         stats["level_2_count"] += 1
                         
                # Recurse children (Categories)
                for i in range(item.childCount()):
                    traverse(item.child(i))

        traverse(root)
        
        msg = (f"<b>Project Statistics:</b><br>"
               f"• Level 1 Entities (e.g. Sequences): {stats['level_1_count']}<br>"
               f"• Level 2 Entities (e.g. Shots): {stats['level_2_count']}<br>"
               f"• Mapped Entity Groups: {stats['mapped_categories']}<br>"
               f"<font color='#ff6666'>• Unmapped Groups: {stats['unmapped_categories']}</font>")
        
        self.log_edit.setHtml(msg)

    def refresh_tree(self):
        self.tree.clear()
        if not self.project_root:
            return

        template_name = self.template_combo.currentText()
        rules = RULE_MAP.get(template_name, {})
        
        # Root Node: Project
        project_name = os.path.basename(self.project_root)
        root_item = QTreeWidgetItem(self.tree)

        root_item.setText(0, f"Project: {project_name}")
        root_item.setText(1, self.project_root)
        root_item.setCheckState(0, Qt.Checked)
        root_item.setData(0, Qt.UserRole, {
            "type": "project", 
            "path": self.project_root,
            "node_kind": "instance"
        })
        root_item.setExpanded(True)
        
        project_children = rules.get("project", {}).get("children", [])

        # Determine if Single-Entity or Multi-Entity
        # Heuristic: If only 1 child type (and it's 'sequence' or 'asset_type'), treating as Single Entity Mode?
        # User defined: "Shots Only" (Sequence), "Asset Only" (Asset Type).
        # Actually template keys: "Shots Only" maps to SHOTS_ONLY_RULES.
        
        is_single_entity_mode = False
        if template_name in ["Shots Only", "Asset Only"]:
            is_single_entity_mode = True
            
        if is_single_entity_mode:
            # === SINGLE ENTITY MODE (Old Behavior) ===
            all_children_ok = True
            for child_type in project_children:
                # We map all subfolders to this single entity type immediately
                cat_item = self.add_category_row(root_item, child_type, self.project_root, is_root_child=True, force_direct=True)
                if cat_item.childCount() == 0:
                    all_children_ok = False
            root_item.setExpanded(not all_children_ok)
            
        else:
            # === MULTI ENTITY MODE (Unmapped Workflow) ===
            
            # 1. Create UNMAPPED Node
            unmapped_item = QTreeWidgetItem(root_item)
            unmapped_item.setText(0, "Unmapped Folders")
            unmapped_item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirClosedIcon))
            # Make it look distinct
            for col in range(3):
                unmapped_item.setBackground(col, QColor("#444444"))
                unmapped_item.setForeground(col, QColor("#AAAAAA"))
                
            unmapped_item.setData(0, Qt.UserRole, {"node_kind": "unmapped_root"})
            unmapped_item.setFlags(unmapped_item.flags() & ~Qt.ItemIsUserCheckable) # Not checkable
            
            # Populate Unmapped with direct children of Root
            try:
                if os.path.exists(self.project_root):
                    for entry in os.scandir(self.project_root):
                        if entry.is_dir() and not entry.name.startswith("."):
                            # Add as unmapped folder item
                            self.add_unmapped_item(unmapped_item, entry.name, entry.path)
            except Exception:
                pass
                
            unmapped_item.setExpanded(True)
            
            # 2. Create Empty Categories
            for child_type in project_children:
                self.add_category_row(root_item, child_type, self.project_root, is_root_child=True, sorting_mode=True)
                
            root_item.setExpanded(True)

        self.calculate_stats()

    def add_unmapped_item(self, parent_item, name, path):
        item = QTreeWidgetItem(parent_item)
        item.setText(0, name)
        item.setText(1, path)
        item.setData(0, Qt.UserRole, {
            "node_kind": "unmapped_item",
            "name": name,
            "path": path
        })
        return item

    def get_color_for_entity(self, entity_type):
        # Try to get theme from parent (MainWindow)
        parent = self.parent()
        colors = None
        if hasattr(parent, 'current_theme'):
             colors = parent.current_theme.colors
        else:
             colors = DARK_THEME.colors
             
        key = f"node_bg_{entity_type.lower()}"
        bg_color = colors.get(key, colors.get('node_bg', '#333333'))
        return QColor(bg_color)

    def add_category_row(self, parent_item, entity_type, parent_path, is_root_child=False, force_direct=False, sorting_mode=False):
        """
        Adds a row asking the user to map a folder for 'entity_type' inside 'parent_path'.
        Returns the created item.
        """
        item = QTreeWidgetItem(parent_item)
        item.setText(0, f"Category: {entity_type}")
        
        bg_color = self.get_color_for_entity(entity_type)
        for col in range(3):
            item.setBackground(col, bg_color)
            item.setForeground(col, QColor("#ffffff"))

        item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
        if sorting_mode:
            # Allow dropping onto it
            item.setFlags(item.flags() | Qt.ItemIsDropEnabled)
        
        item.setData(0, Qt.UserRole, {
            "node_kind": "category", 
            "entity_type": entity_type,
            "parent_path": parent_path
        })
        
        # If Sorting Mode (Multi Entity), we DON'T show ComboBox. We wait for drops.
        if sorting_mode:
            item.setText(1, "Drag folders here from Unmapped")
            return item
            
        # Create ComboBox for Mapping Mode (or Single Entity)
        combo = QComboBox()
        combo.addItem("Select Folder...", None)
        
        # <Direct Children> Option
        combo.addItem(f"<Direct Children of {os.path.basename(parent_path)}>", parent_path)

        # Scan subfolders
        subfolders = []
        try:
            if os.path.exists(parent_path):
                for entry in os.scandir(parent_path):
                    if entry.is_dir() and not entry.name.startswith("."):
                        subfolders.append(entry.name)
        except Exception:
            pass
            
        subfolders.sort()
        for f in subfolders:
            combo.addItem(f, os.path.join(parent_path, f))
            
        # -- HEURISTIC AUTO-SELECTION --
        selected_index = 0 
        
        if force_direct:
            selected_index = 1 # Select Direct Children
            
        else:
            # 1. Try to find explicit folder matching name (e.g. "sequences") or Aliases
            # Check Aliases if defined? (User asked for it, even if we are in sorting mode now? 
            # Well, single entity uses this path still).
            # We haven't implemented aliases in this block yet, let's stick to name match for now or basic alias.
            
            # Simple alias check if we wanted
            normalized_type = entity_type.lower()
            aliases = [normalized_type, normalized_type + "s"]
            
            for i in range(combo.count()):
                text = combo.itemText(i).lower()
                if text in aliases:
                    selected_index = i
                    break
            
            if selected_index == 0 and len(subfolders) > 0:
                 # Default logic: Assume Direct Children if no specific folder found
                 selected_index = 1

        combo.setCurrentIndex(selected_index)
        combo.currentIndexChanged.connect(lambda idx, it=item, cb=combo: self.on_category_mapped(it, cb))
        
        self.tree.setItemWidget(item, 1, combo)
        
        # Trigger logic
        if selected_index != 0:
            self.on_category_mapped(item, combo)
            
        return item

    def on_category_mapped(self, category_item, combo):
        """
        Called when user selects a folder for a Category (e.g. "sequences").
        We then scan that folder and add Instances (e.g. sq01, sq02) as children.
        """
        # Clear existing children (Instances)
        category_item.takeChildren()
        
        folder_path = combo.currentData()
        if not folder_path:
            self.calculate_stats()
            return

        # Scan for Instances
        instances = []
        try:
            if os.path.exists(folder_path):
                for entry in os.scandir(folder_path):
                    if entry.is_dir() and not entry.name.startswith("."):
                        # If we are using <Direct Children>, we must be careful not to include 
                        # folders that are actually Categories for the Parent.
                        # But here, 'folder_path' IS the path we are scanning.
                        # If folder_path == category_parent_path (Direct Children), 
                        # we might pick up "assets", "shots" folders as instances if they exist?
                        # It's a risk. But "Build from Folders" usually assumes uniform structure.
                        # If strictly adhering to template, we could filter out names that match sibling categories?
                        # For now, let's assume everything is an instance.
                        instances.append(entry)
        except Exception:
            pass
            
        instances.sort(key=lambda x: x.name)
        
        # Get Rules to know what children these instances might have
        data = category_item.data(0, Qt.UserRole)
        entity_type = data['entity_type']
        template_name = self.template_combo.currentText()
        rules = RULE_MAP.get(template_name, {})
        allowed_children = rules.get(entity_type, {}).get("children", [])
        
        for entry in instances:
            self.add_instance_row(category_item, entity_type, entry.name, entry.path, allowed_children)
            
        category_item.setExpanded(True)
        
        # Trigger Auto-Apply to siblings
        if not combo.signalsBlocked(): 
             self.auto_apply_to_siblings(category_item, combo.currentText())
        
        self.calculate_stats()

    def add_instance_row(self, parent_item, entity_type, name, path, children_types):
        """
        Adds a specific instance (e.g. 'sq01').
        """
        item = QTreeWidgetItem(parent_item)
        item.setText(0, name)
        item.setText(1, path)
        item.setCheckState(0, Qt.Checked)
        
        # Colorize Instance same as entity type? Or slightly different?
        # User asked: "add colors to the entities just to differentiate on the UI"
        # Usually instances inherit the color or are slightly lighter.
        # Let's use the same color for consistency, maybe lower alpha?
        # Or just solid color.
        # Custom color
        bg_color = self.get_color_for_entity(entity_type)
        # Apply to all columns
        for col in range(3):
            item.setBackground(col, bg_color)
            item.setForeground(col, QColor("#ffffff"))

        item.setData(0, Qt.UserRole, {
            "node_kind": "instance",
            "type": entity_type,
            "name": name,
            "path": path
        })
        
        # If this instance has children (e.g. Sequence has Shots), add Category rows for them
        all_children_ok = True
        for child_type in children_types:
            cat_item = self.add_category_row(item, child_type, path)
            # Check if this category automatically found instances
            if cat_item.childCount() == 0:
                all_children_ok = False
        
        # Collapse if all children found (found = has instances), Expand if missing
        item.setExpanded(not all_children_ok)

    def handle_drop(self, target_item, folder_path):
        """
        Handle drag & drop of a folder onto a tree item.
        """
        data = target_item.data(0, Qt.UserRole)
        if not data: return
        
        node_kind = data.get('node_kind')
        folder_name = os.path.basename(folder_path)
        
        if node_kind == 'category':
            # User dropped a folder onto a Category (e.g. "Sequences")
            # This means they want to add this folder as an Instance of this Category.
            # e.g. Dropped "sq05" onto "Sequences".
            
            # Check if it already exists?
            # We just add it.
            entity_type = data.get('entity_type')
            
            # Get allowed children for this new instance
            template_name = self.template_combo.currentText()
            rules = RULE_MAP.get(template_name, {})
            allowed_children = rules.get(entity_type, {}).get("children", [])
            
            self.add_instance_row(target_item, entity_type, folder_name, folder_path, allowed_children)
            target_item.setExpanded(True)
            
        elif node_kind == 'instance':
            # User dropped a folder onto an Instance (e.g. "sq01")
            # They probably want to add it to a sub-category?
            # e.g. Dropped "shots" onto "sq01"?
            # OR dropped "sh010" onto "sq01" expecting it to go into "Shots"?
            
            # If the folder name matches a child category, we map that category?
            # e.g. dropped "Shots" folder onto "sq01".
            
            # Find child category with matching name?
            # Or if there is only one child category, put it there?
            
            # Strategy:
            # 1. Check if folder name matches any child category name.
            # 2. If it's a generic folder (e.g. "sh010"), check if there is a valid category to put it in.
            
            # Let's check children of this instance (which are Categories)
            for i in range(target_item.childCount()):
                cat_item = target_item.child(i)
                cat_data = cat_item.data(0, Qt.UserRole)
                cat_type = cat_data.get('entity_type')
                
                # Case A: Dropped folder IS the category folder (e.g. "shots")
                # We should set the mapping for that category.
                if folder_name.lower() == cat_type.lower() or folder_name.lower() == cat_type.lower() + "s":
                     # Setup mapping
                     widget = self.tree.itemWidget(cat_item, 1)
                     if isinstance(widget, QComboBox):
                         # Add custom item
                         widget.addItem(folder_name, folder_path)
                         widget.setCurrentIndex(widget.count() - 1)
                         # on_category_mapped will trigger
                     return
            
            # Case B: Dropped folder is an ITEM for a child category (e.g. "sh010" dropped on "sq01")
            # We likely want to add it to the "Shots" category of "sq01".
            # If there are multiple categories (e.g. Shots, Plates), it's ambiguous.
            # But usually there is a "primary" child type?
            
            # Let's try to find a category that "accepts" this item?
            # Or just default to the first Category child?
            if target_item.childCount() > 0:
                 first_cat = target_item.child(0)
                 # Add as instance to this category
                 first_cat_data = first_cat.data(0, Qt.UserRole)
                 cat_type = first_cat_data.get('entity_type')
                 
                 template_name = self.template_combo.currentText()
                 rules = RULE_MAP.get(template_name, {})
                 allowed_children = rules.get(cat_type, {}).get("children", [])
                 
                 self.add_instance_row(first_cat, cat_type, folder_name, folder_path, allowed_children)
                 target_item.setExpanded(True)
                 first_cat.setExpanded(True)


    def on_item_changed(self, item, column):
        """
        Handle checkbox changes.
        """
        if column == 0:
            # If checked/unchecked, maybe propagate to children?
            state = item.checkState(0)
            # Recursive check/uncheck for children (instances)
            block = self.tree.blockSignals(True)
            self._recursive_check(item, state)
            self.tree.blockSignals(block)

    def _recursive_check(self, item, state):
        for i in range(item.childCount()):
            child = item.child(i)
            # If child is instance, set check. 
            # If child is Category, recurse? No, Category not checkable.
            # But Category children ARE instances.
            
            data = child.data(0, Qt.UserRole)
            kind = data.get('node_kind')
            
            if kind == 'instance':
                child.setCheckState(0, state)
                self._recursive_check(child, state)
            elif kind == 'category':
                self._recursive_check(child, state)

    def auto_apply_to_siblings(self, category_item, selected_folder_name):
        """
        If user selected 'shots' folder for 'sq01', try to select 'shots' for 'sq02', 'sq03' etc.
        """
        # 1. Identify valid scope: Siblings of the Parent Instance
        # Structure: ParentInstance (sq01) -> Category (Shots) -> [Selected]
        # We need to go up: Category -> ParentInstance (sq01) -> GrandParentCategory (Sequences)
        
        parent_instance = category_item.parent()
        if not parent_instance: return
        
        grand_parent_category = parent_instance.parent()
        if not grand_parent_category: return
        
        # 2. Iterate over all sibling instances (sq02, sq03...)
        target_category_type = category_item.data(0, Qt.UserRole)['entity_type']
        
        for i in range(grand_parent_category.childCount()):
            sibling_instance = grand_parent_category.child(i)
            if sibling_instance == parent_instance:
                continue
                
            # Find the matching Category child in sibling
            sibling_category_item = None
            for j in range(sibling_instance.childCount()):
                child = sibling_instance.child(j)
                if child.data(0, Qt.UserRole)['entity_type'] == target_category_type:
                    sibling_category_item = child
                    break
            
            if sibling_category_item:
                # 3. Check if this sibling has a folder with the same name
                widget = self.tree.itemWidget(sibling_category_item, 1)
                if isinstance(widget, QComboBox):
                    # Check if selected_folder_name exists in this combo
                    # The combo items are just names relative to parent path
                    index = widget.findText(selected_folder_name)
                    if index != -1:
                        # Prevent infinite recursion if we trigger signal
                        # We can block signals on the combo
                        widget.blockSignals(True)
                        widget.setCurrentIndex(index)
                        widget.blockSignals(False)
                        
                        # We MUST manually trigger the logic to populate children
                        self.on_category_mapped(sibling_category_item, widget)

    def on_item_moved(self, item, target_item):
        """
        Handle internal drag and drop (sorting).
        """
        data = item.data(0, Qt.UserRole)
        target_data = target_item.data(0, Qt.UserRole)
        
        if not data or not target_data: return
        
        # Only allow moving "unmapped_item"
        if data.get('node_kind') != 'unmapped_item':
            return
            
        # Target must be a Category (or an instance within a category, implying the category)
        target_category = None
        if target_data.get('node_kind') == 'category':
            target_category = target_item
        elif target_data.get('node_kind') == 'instance':
            # Dropped onto an existing instance? Add to same category.
            target_category = target_item.parent()
            
        if target_category and target_category.data(0, Qt.UserRole).get('node_kind') == 'category':
            self.move_folder_to_category(item, target_category)

    def move_folder_to_category(self, folder_item, category_item):
        """
        Moves a folder from Unmapped to a Category.
        """
        data = folder_item.data(0, Qt.UserRole)
        cat_data = category_item.data(0, Qt.UserRole)
        
        name = data['name']
        path = data['path']
        entity_type = cat_data['entity_type']
        
        # Get allowed children for the new instance
        template_name = self.template_combo.currentText()
        rules = RULE_MAP.get(template_name, {})
        allowed_children = rules.get(entity_type, {}).get("children", [])
        
        # Add Instance
        self.add_instance_row(category_item, entity_type, name, path, allowed_children)
        category_item.setExpanded(True)
        
        # Remove from Unmapped
        parent = folder_item.parent()
        parent.removeChild(folder_item)
        
        # Update text of Category to clear "Drag here..." if needed? 
        # Actually "Drag folders here..." is useful to keep.
        
        self.calculate_stats()

    def show_context_menu(self, item, global_pos):
        data = item.data(0, Qt.UserRole)
        if not data: return
        
        kind = data.get('node_kind')
        
        menu = QMenu()
        
        if kind == 'unmapped_item':
            # Assign to...
            assign_menu = menu.addMenu("Assign to...")
            
            # Find available categories in Root
            # Root is item.parent().parent()? Unmapped -> Root
            unmapped_node = item.parent()
            root_node = unmapped_node.parent()
            
            if root_node:
                for i in range(root_node.childCount()):
                    child = root_node.child(i)
                    c_data = child.data(0, Qt.UserRole)
                    if c_data.get('node_kind') == 'category':
                        cat_name = c_data.get('entity_type')
                        action = assign_menu.addAction(cat_name)
                        action.triggered.connect(lambda ch=False, it=item, cat=child: self.move_folder_to_category(it, cat))
            
            menu.addSeparator()
            remove_action = menu.addAction("Remove")
            remove_action.triggered.connect(lambda: self.remove_unmapped_item(item))
            
        elif kind == 'instance':
            # Allow removing instance if it came from Unmapped?
            # For now, maybe just "Remove" which puts it back to Unmapped? 
            # Or just deletes it?
            # User said: "remove which will remove from the options"
            # If we remove an assigned instance, we should probably delete it.
            # But if it was "Unmapped", does it go back?
            # Let's simple "Remove" deletes it from tree.
            # If user wants to re-map, they re-drag from unmapped? 
            # But if we delete it, it's gone. 
            # Maybe "Unassign" -> Move back to Unmapped?
            # For iteration 1, let's implement "Remove" (delete) for instances too?
            # Or "Unassign"?
            # Let's stick to Unmapped items Context Menu as requested first.
            pass
            
        if not menu.isEmpty():
            menu.exec_(global_pos)

    def remove_unmapped_item(self, item):
        parent = item.parent()
        parent.removeChild(item)
        self.calculate_stats()
        
    def calculate_stats(self):
        """
        Traverses the tree to count mapped/unmapped entities and updates the log.
        """
        root = self.tree.topLevelItem(0)
        if not root:
             self.log_edit.setText("No project loaded.")
             return
             
        stats = {
            "unmapped_count": 0,
            "mapped_instances": 0
        }
        
        # Find Unmapped Node
        unmapped_node = None
        for i in range(root.childCount()):
            child = root.child(i)
            if child.data(0, Qt.UserRole).get('node_kind') == 'unmapped_root':
                unmapped_node = child
                break
                
        if unmapped_node:
            stats["unmapped_count"] = unmapped_node.childCount()
            if stats["unmapped_count"] == 0:
                 # Hide 'Unmapped' node if empty?
                 # unmapped_node.setHidden(True)
                 # Or keep it to show "Done"?
                 pass
        
        # Count mapped instances (Level 1)
        for i in range(root.childCount()):
            child = root.child(i)
            if child.data(0, Qt.UserRole).get('node_kind') == 'category':
                 stats["mapped_instances"] += child.childCount()
                 
        msg = ""
        if stats["unmapped_count"] > 0:
            msg += f"<font color='#ff4444'><b>WARNING: {stats['unmapped_count']} Unmapped Folders remaining.</b></font><br>"
            msg += "Please drag them to a Category or right-click to Remove.<br>"
            self.status_label.setText(f"Unmapped: {stats['unmapped_count']}")
            self.status_label.setStyleSheet("color: #ff4444; font-weight: bold;")
        else:
            msg += f"<font color='#55ff55'><b>All folders mapped!</b></font><br>"
            self.status_label.setText("Ready to Build")
            self.status_label.setStyleSheet("color: #55ff55; font-weight: bold;")
            
        msg += f"Mapped Entities: {stats['mapped_instances']}"
        self.log_edit.setHtml(msg)

    def on_build(self):
        # 0. Validation: Check for Unmapped Items
        root = self.tree.topLevelItem(0)
        if root:
            unmapped_node = None
            for i in range(root.childCount()):
                child = root.child(i)
                if child.data(0, Qt.UserRole).get('node_kind') == 'unmapped_root':
                    unmapped_node = child
                    break
            
            if unmapped_node and unmapped_node.childCount() > 0:
                QMessageBox.warning(self, "Unmapped Folders", 
                                    f"There are {unmapped_node.childCount()} unmapped folders.\n"
                                    "Please assign them to an Entity or Remove them before building.")
                return

        # Traverse Tree to build structure
        if not root:
            return

        project_data = self._parse_item(root)
        if project_data:
            self.result_data = project_data
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Could not build structure.")

    def _parse_item(self, item):
        """
        Recursive parser.
        Returns dict or None.
        """
        data = item.data(0, Qt.UserRole)
        if not data: return None
        
        kind = data.get('node_kind', 'instance') # root is instance-like
        
        # We only care about Instances (Project, Sequence, Shot). 
        # Categories are structural helpers in the UI, not nodes in the final tree.
        
        if kind == 'category':
            # Skip the category node itself, but return its children (Instances)
            # But wait, the parent expects a list of children.
            # This function returns a Single Node.
            # So we shouldn't call _parse_item on a category expecting a node.
            # We should handle category children in the parent's loop.
            return None

        # It's an instance (Project, Sequence, Shot...)
        # Check if included
        if item.checkState(0) != Qt.Checked:
            return None
            
        node = {
            "type": data.get("type", "unknown"),
            "name": data.get("name", item.text(0).replace("Project: ", "")),
            "path": data.get("path"),
            "children": []
        }
        
        # Iterate UI children
        for i in range(item.childCount()):
            child = item.child(i)
            child_data = child.data(0, Qt.UserRole)
            
            if child_data['node_kind'] == 'category':
                # This child is a Category wrapper (e.g. "Sequences")
                # Iterate ITS children (which are instances e.g. "sq01")
                for j in range(child.childCount()):
                    grand_child = child.child(j)
                    parsed_grand_child = self._parse_item(grand_child)
                    if parsed_grand_child:
                        node['children'].append(parsed_grand_child)
                        
            elif child_data['node_kind'] == 'instance':
                # Direct instance child? Rare given our structure, but possible.
                parsed = self._parse_item(child)
                if parsed:
                    node['children'].append(parsed)
                    
        return node
