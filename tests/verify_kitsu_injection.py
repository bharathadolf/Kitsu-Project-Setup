import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

# Mock gazu before importing setup
sys.modules["gazu"] = MagicMock()
import gazu
from project_ingester.core.setup import ProjectManager

class TestKitsuInjection(unittest.TestCase):
    def setUp(self):
        self.logs = []
        self.manager = ProjectManager(log_callback=lambda msg, level: self.logs.append((msg, level)))
        self.manager.connected = True # Bypass connect

        # Setup Gazu Mocks
        gazu.project.get_project_by_name.return_value = None
        gazu.project.new_project.return_value = {"id": "proj_id", "name": "Test Project"}
        gazu.shot.get_episode_by_name.return_value = None
        gazu.shot.new_episode.return_value = {"id": "ep_id", "name": "EP01"}
        gazu.shot.get_sequence_by_name.return_value = None
        gazu.shot.new_sequence.return_value = {"id": "seq_id", "name": "SEQ01"}
        gazu.shot.get_shot_by_name.return_value = None
        gazu.shot.new_shot.return_value = {"id": "shot_id", "name": "SH010"}
        gazu.asset.get_asset_by_name.return_value = None
        gazu.asset.new_asset.return_value = {"id": "asset_id", "name": "Hero"}
        
        # Reset mocks
        gazu.project.update_project.reset_mock()
        gazu.project.update_project_data.reset_mock()
        gazu.shot.update_episode.reset_mock()
        gazu.shot.update_episode_data.reset_mock()
        
    def test_project_injection(self):
        """Verify Project Code, Desc, Data logs and calls."""
        plan = [{
            "type": "project",
            "name": "Test Project",
            "params": {
                "name": "Test Project",
                "code": "TP",
                "description": "Test Desc",
                "data": {"my_key": "my_val"}
            }
        }]
        
        self.manager.execute_plan(plan)
        
        # Logs
        log_msgs = [l[0] for l in self.logs]
        self.assertTrue(any("adding value to code parameter in the project entity" in m for m in log_msgs), f"Logs: {log_msgs}")
        self.assertTrue(any("adding value to description parameter in the project entity" in m for m in log_msgs))
        self.assertTrue(any("adding data to 'data' parameter in the project entity" in m for m in log_msgs))
        
        # Calls
        gazu.project.update_project.assert_called()
        gazu.project.update_project_data.assert_called()

    def test_episode_injection(self):
        """Verify Episode Code, Desc, Data logs and calls."""
        # Need context project
        context_proj = {"id": "proj_id", "name": "Test Project"}
        # Pre-seed context if I could, but execute_plan builds it. 
        # I'll create a plan with Project AND Episode
        plan = [
            {"type": "project", "name": "P", "params": {"name": "P"}},
            {"type": "episode", "name": "EP01", "params": {
                "code": "ep01", "description": "Desc EP", "data": {"status": "wip"}
            }}
        ]
        
        self.manager.execute_plan(plan)
        
        log_msgs = [l[0] for l in self.logs]
        self.assertTrue(any("adding value to code parameter in the episode entity" in m for m in log_msgs))
        self.assertTrue(any("adding value to description parameter in the episode entity" in m for m in log_msgs))
        self.assertTrue(any("adding data to 'data' parameter in the episode entity" in m for m in log_msgs))
        
        gazu.shot.update_episode.assert_called()
        gazu.shot.update_episode_data.assert_called()

if __name__ == '__main__':
    unittest.main()
