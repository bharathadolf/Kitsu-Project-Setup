import sys
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QMenu
from PySide6.QtCore import Qt

# Adjust path to import project_ingester
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_ingester.ui.app import MainWindow

class TestLoadProjectUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    @patch('project_ingester.ui.app.ProjectLoader')
    def test_load_project_flow(self, MockLoader):
        # Setup Mock
        mock_loader_instance = MockLoader.return_value
        mock_loader_instance.connect.return_value = True
        mock_loader_instance.get_all_projects.return_value = [
            {"name": "Test Project", "id": "proj-123"}
        ]
        mock_loader_instance.load_full_project.return_value = {
            "type": "project",
            "properties": {"name": "Test Project", "id": "proj-123", "production_type": "short"},
            "children": [
                {
                    "type": "sequence",
                    "properties": {"name": "SEQ01", "id": "seq-1"},
                    "children": [
                        {
                            "type": "shot",
                            "properties": {"name": "SH010", "id": "sh-1"},
                            "children": []
                        }
                    ]
                }
            ]
        }

        # Init Window
        window = MainWindow()
        
        # Verify Menu
        # Access directly as it's an attribute of MainWindow
        load_proj_menu = window.load_project_menu
        self.assertIsNotNone(load_proj_menu)
        self.assertEqual(load_proj_menu.title(), "Load Project")
        
        # Trigger Populate
        # We need to simulate the aboutToShow signal or just call the method
        window.populate_projects_menu()
        
        # Verify Loader calls
        mock_loader_instance.connect.assert_called()
        mock_loader_instance.get_all_projects.assert_called()
        
        # Check Actions in Menu
        # We need to ensure the menu actions are populated
        # Note: In PySide6, actions() might return internal C++ objects that are tricky
        # But since we just populated it, it should be fine.
        actions = load_proj_menu.actions()
        self.assertEqual(len(actions), 1)
        # Check text. For safety, just check count and maybe first action text if possible
        # Or check if mock was used to populate.
        # But let's try to access text.
        self.assertEqual(actions[0].text(), "Test Project")
        
        # Trigger Load
        # We can't easily click the action signal in test without event loop, but we can call the slot manually
        # checking if the lambda was connected correctly is hard, but we can verify load_project_action logic
        
        window.load_project_action("proj-123")
        
        mock_loader_instance.load_full_project.assert_called_with("proj-123")
        
        # Verify Tree Population
        tree = window.project_panel.tree
        root = tree.topLevelItem(0)
        self.assertIsNotNone(root)
        
        root_widget = tree.itemWidget(root, 0)
        self.assertEqual(root_widget.node_frame.properties["name"], "Test Project")
        
        # Check children
        self.assertEqual(root.childCount(), 1)
        seq_item = root.child(0)
        seq_widget = tree.itemWidget(seq_item, 0)
        self.assertEqual(seq_widget.node_frame.properties["name"], "SEQ01")
        
        self.assertEqual(seq_item.childCount(), 1)
        shot_item = seq_item.child(0)
        shot_widget = tree.itemWidget(shot_item, 0)
        self.assertEqual(shot_widget.node_frame.properties["name"], "SH010")
        
        print("\nTest Finished Successfully")

if __name__ == "__main__":
    unittest.main()
