
import sys
import os
import unittest

# Setup path first!
project_root = r"d:\AfterZFx\ProjectIngester"
if project_root not in sys.path:
    sys.path.append(project_root)

# Import compat to get the correct Qt version
from project_ingester.utils.compat import QApplication, QT_VERSION
from project_ingester.ui.app import MainWindow

print(f"Running test with QT_VERSION: {QT_VERSION}")

class TestPanelResize(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_panel_labels(self):
        print("Creating MainWindow...")
        window = MainWindow()
        window.show()
        
        # Check initial panels
        print("Checking initial panel sizes...")
        initial_sizes = window.splitter.sizes()
        expected_text = f"Panels: {initial_sizes}"
        
        # Normalize text to avoid whitespace issues
        actual_text = window.panel_size_label.text()
        print(f"Initial Label: '{actual_text}'")
        self.assertEqual(actual_text, expected_text)
        
        # Resize window (which should resize panels via splitter stretch)
        print("Resizing window...")
        window.resize(1200, 800)
        self.app.processEvents()
        
        new_sizes = window.splitter.sizes()
        expected_new_text = f"Panels: {new_sizes}"
        print(f"New Label: '{window.panel_size_label.text()}'")
        self.assertEqual(window.panel_size_label.text(), expected_new_text)
        
        # Verify sizes actually changed
        self.assertNotEqual(initial_sizes, new_sizes)

        window.close()

if __name__ == '__main__':
    unittest.main(verbosity=2)
