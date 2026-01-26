#!/usr/bin/env python3
"""
Main GUI application with three panels:
1. Project Structure
2. Properties Panel
3. Console Log
"""

import sys
import os
from datetime import datetime

# Import our compatibility module
from pyside_compat import *

# ============================================================================
# RULE MAPS
# ============================================================================

FEATURE_FILM_RULES = {
    "project": {
        "children": ["sequence", "asset_type"],
        "deletable": False
    },
    "sequence": {
        "children": ["shot"],
        "deletable": True
    },
    "shot": {
        "children": [],
        "deletable": True
    },
    "asset_type": {
        "children": ["asset"],
        "deletable": True
    },
    "asset": {
        "children": [],
        "deletable": True
    }
}

TV_SHOW_RULES = {
    "project": {
        "children": ["episode"],
        "deletable": False
    },
    "episode": {
        "children": ["sequence"],
        "deletable": True
    },
    "sequence": {
        "children": ["shot"],
        "deletable": True
    },
    "shot": {
        "children": [],
        "deletable": True
    }
}

SHOTS_ONLY_RULES = {
    "project": {
        "children": ["sequence"],
        "deletable": False
    },
    "sequence": {
        "children": ["shot"],
        "deletable": True
    },
    "shot": {
        "children": [],
        "deletable": True
    }
}

ASSET_ONLY_RULES = {
    "project": {
        "children": ["asset_type"],
        "deletable": False
    },
    "asset_type": {
        "children": ["asset"],
        "deletable": True
    },
    "asset": {
        "children": [],
        "deletable": True
    }
}

# Unified Rule Map
RULE_MAP = {
    "Feature Film": FEATURE_FILM_RULES,
    "TV Show": TV_SHOW_RULES,
    "Shots Only": SHOTS_ONLY_RULES,
    "Asset Only": ASSET_ONLY_RULES,
    "Custom": {"project": {"children": [], "deletable": False}} # Custom has empty defaults
}

class ConsoleWidget(QTextEdit):
    """Enhanced console widget with logging capabilities"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup console appearance"""
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monospace';
                font-size: 11px;
                border: 1px solid #3e3e3e;
                border-radius: 3px;
            }
        """)
        
    def log(self, message, level="INFO"):
        """Log a message to console with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_colors = {
            "INFO": "#4fc3f7",
            "WARNING": "#ffb74d",
            "ERROR": "#f44336",
            "SUCCESS": "#4caf50"
        }
        color = level_colors.get(level, "#d4d4d4")
        
        html_message = f"""
        <div style="margin: 2px 0;">
            <span style="color: #888;">[{timestamp}]</span>
            <span style="color: {color}; font-weight: bold;"> [{level}]</span>
            <span style="color: #d4d4d4;"> {message}</span>
        </div>
        """
        
        self.append(html_message)
        # Auto-scroll to bottom
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        )

class ProjectStructureWidget(QWidget):
    """Project structure panel with tree view"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup project structure panel"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Project Structure")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #2d2d30;
                padding: 8px;
                border-bottom: 2px solid #007acc;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        
        # Tree view for project structure
        self.tree_view = QTreeView()
        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-size: 11px;
            }
            QTreeView::item:hover {
                background-color: #2a2d2e;
            }
            QTreeView::item:selected {
                background-color: #094771;
            }
        """)
        
        # Add some demo items
        from pyside_compat import QtGui
        model = QtGui.QStandardItemModel()
        root = model.invisibleRootItem()
        
        # Empty model for now
        self.tree_view.setModel(model)
        
        self.tree_view.setModel(model)
        self.tree_view.expandAll()
        
        layout.addWidget(header)
        layout.addWidget(self.tree_view)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def apply_template(self, template_name):
        """Apply a structure template"""
        from pyside_compat import QtGui
        model = QtGui.QStandardItemModel()
        root = model.invisibleRootItem()
        
        rules = RULE_MAP.get(template_name, {})
        project_rules = rules.get("project", {})
        
        # Always create Root Project
        project_item = QtGui.QStandardItem("Project")
        project_item.setIcon(QtGui.QIcon.fromTheme("folder"))
        project_item.setData("project", Qt.UserRole) # Store type
        
        # Create immediate children based on rules
        children_types = project_rules.get("children", [])
        
        for child_type in children_types:
            # Create a folder for this type
            # Convention: Capitalize string
            item = QtGui.QStandardItem(child_type.replace("_", " ").title())
            item.setIcon(QtGui.QIcon.fromTheme("folder"))
            item.setData(child_type, Qt.UserRole)
            project_item.appendRow(item)
            
        root.appendRow(project_item)
        self.tree_view.setModel(model)
        self.tree_view.expandAll()

class PropertiesWidget(QWidget):
    """Properties panel with editable properties"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup properties panel"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Properties Panel")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #2d2d30;
                padding: 8px;
                border-bottom: 2px solid #68217a;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        
        # Properties list
        self.properties_list = QListWidget()
        self.properties_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-size: 11px;
                alternate-background-color: #2a2d2e;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3e3e3e;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        
        # Empty list for now
        # self.properties_list.addItem("Select an item to view properties")
        
        layout.addWidget(header)
        layout.addWidget(self.properties_list)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

class MainWindow(QMainWindow):
    """Main application window with three panels"""
    
    def __init__(self):
        super().__init__()
        self.console = None
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main window UI"""
        self.setWindowTitle("Project ingester")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Create the three panels
        self.project_panel = ProjectStructureWidget()
        self.properties_panel = PropertiesWidget()
        
        # Create console panel
        console_container = QWidget()
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(0)
        
        # Console header
        console_header = QLabel("Console Log")
        console_header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
                background-color: #2d2d30;
                padding: 8px;
                border-bottom: 2px solid #4caf50;
            }
        """)
        console_header.setAlignment(Qt.AlignCenter)
        
        # Console widget
        self.console = ConsoleWidget()
        
        # Console controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        clear_btn = QPushButton("Clear Console")
        clear_btn.clicked.connect(self.clear_console)
        
        test_log_btn = QPushButton("Test Log")
        test_log_btn.clicked.connect(self.test_log_message)
        
        controls_layout.addWidget(clear_btn)
        controls_layout.addWidget(test_log_btn)
        controls_layout.addStretch()
        
        # Assemble console panel
        console_layout.addWidget(console_header)
        console_layout.addWidget(self.console)
        console_layout.addWidget(controls_widget)
        
        # Add panels to splitter
        splitter.addWidget(self.project_panel)
        splitter.addWidget(self.properties_panel)
        splitter.addWidget(console_container)
        
        # Set initial sizes (30%, 30%, 40%)
        splitter.setSizes([400, 400, 600])
        
        # Make panels collapsible
        splitter.setChildrenCollapsible(True)
        
        main_layout.addWidget(splitter)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        status_bar = QStatusBar()
        qt_version = get_qt_version()
        status_bar.showMessage(f"PySide{qt_version} - Ready")
        self.setStatusBar(status_bar)
        
        # Log startup message
        self.console.log("Application started successfully", "SUCCESS")
        self.console.log(f"Using PySide{qt_version}", "INFO")

        # Apply default template
        self.apply_template("Custom")

    def apply_template(self, template_name):
        self.project_panel.apply_template(template_name)
        self.console.log(f"Applied template: {template_name}", "INFO")
        
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Project", self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open Project", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)

        # Template Submenu
        template_menu = view_menu.addMenu("Template")
        
        # Add actions for each rule
        for rule_name in RULE_MAP.keys():
            action = QAction(rule_name, self)
            action.triggered.connect(lambda checked=False, r=rule_name: self.apply_template(r))
            template_menu.addAction(action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def new_project(self):
        """Handle new project creation"""
        self.console.log("Creating new project...", "INFO")
        
    def open_project(self):
        """Handle opening a project"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", 
            "All Files (*);;Python Files (*.py)", 
            options=options
        )
        
        if file_path:
            self.console.log(f"Opening project: {file_path}", "SUCCESS")
            
    def refresh_view(self):
        """Refresh the view"""
        self.console.log("View refreshed", "INFO")
        
    def show_about(self):
        """Show about dialog"""
        qt_version = get_qt_version()
        QMessageBox.about(
            self, 
            "About GUI Tool",
            f"Multi-Panel GUI Tool\n\n"
            f"Compatible with both PySide2 and PySide6\n"
            f"Currently using: PySide{qt_version}\n\n"
            f"Features:\n"
            f"• Project Structure Panel\n"
            f"• Properties Panel\n"
            f"• Console Log Panel"
        )
        
    def clear_console(self):
        """Clear the console"""
        self.console.clear()
        self.console.log("Console cleared", "INFO")
        
    def test_log_message(self):
        """Test logging different message types"""
        self.console.log("This is an info message", "INFO")
        self.console.log("This is a warning message", "WARNING")
        self.console.log("This is an error message", "ERROR")
        self.console.log("This is a success message", "SUCCESS")
        
    def closeEvent(self, event):
        """Handle application close"""
        reply = QMessageBox.question(
            self, 'Exit Application',
            'Are you sure you want to exit?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.console.log("Application closing...", "INFO")
            event.accept()
        else:
            event.ignore()

def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()