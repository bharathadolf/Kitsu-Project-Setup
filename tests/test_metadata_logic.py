import sys
import unittest
from PySide6 import QtWidgets

# Ensure package is found
sys.path.append(r"D:\AfterZFx\ProjectIngester")
from project_ingester.ui.tree import NodeFrame
from project_ingester.ui.properties import PropertiesWidget
from project_ingester.config import OUTPUT_FORMATS

app = QtWidgets.QApplication.instance()
if not app:
    app = QtWidgets.QApplication(sys.argv)

class TestMetadata(unittest.TestCase):
    def test_episode_metadata(self):
        print("Testing Episode Metadata...")
        node = NodeFrame("episode")
        self.assertIn("episode_name", node.properties)
        self.assertIn("episode_order", node.properties)
        self.assertEqual(node.properties["episode_name"], "Episode 1")

    def test_shot_metadata(self):
        print("Testing Shot Metadata...")
        node = NodeFrame("shot", node_id="010")
        self.assertEqual(node.properties["shot_code"], "SH_010")
        self.assertEqual(node.properties["output_format"], ["exr"])
        self.assertEqual(node.properties["rv_context_group"], "shot_default")

    def test_asset_metadata(self):
        print("Testing Asset Metadata...")
        node = NodeFrame("asset")
        self.assertIn("asset_category", node.properties)
        self.assertIn("render_engine", node.properties)
        self.assertTrue(node.properties["publish_enabled"])
        
    def test_dropdown_logic(self):
        print("Testing Dropdown Logic...")
        node = NodeFrame("shot")
        widget = PropertiesWidget()
        # Simulate dropdown change
        widget.on_dropdown_changed(node, "output_format", "jpg")
        self.assertEqual(node.properties["output_format"], ["jpg"])

if __name__ == '__main__':
    unittest.main()
