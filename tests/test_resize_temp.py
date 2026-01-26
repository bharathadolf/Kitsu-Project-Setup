
import sys
import os
import unittest
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QSize

# Setup path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from project_ingester.ui.app import MainWindow

class TestResizeFeedback(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def test_resize_label(self):
        window = MainWindow()
        window.show()
        
        # Check initial size
        initial_width = window.width()
        initial_height = window.height()
        expected_text = f"{initial_width} x {initial_height}"
        self.assertEqual(window.size_label.text(), expected_text)
        
        # Resize
        new_width = 800
        new_height = 600
        window.resize(new_width, new_height)
        
        # Allow events to process
        self.app.processEvents()
        
        # Check new size label
        expected_new_text = f"{new_width} x {new_height}"
        self.assertEqual(window.size_label.text(), expected_new_text)
        
        window.close()

if __name__ == '__main__':
    unittest.main()
