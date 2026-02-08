
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from project_ingester.core.setup import ProjectManager

class TestFetchBackend(unittest.TestCase):
    def test_fetch_with_created_id(self):
        manager = ProjectManager(None) # No UI
        manager.log = MagicMock()
        
        # Mock Gazu
        import gazu
        gazu.project.get_project = MagicMock(return_value={"id": "prod-123", "name": "Prod", "type": "project"})
        
        # Create a mock plan with 'created_entity' populated
        plan = [
            {
                "type": "project",
                "name": "Prod",
                "params": {},
                "created_entity": {"id": "prod-123", "name": "Prod"} # Simulator execution result
            }
        ]
        
        # Run Fetch
        manager.fetch_entity_data(plan)
        
        # Verify
        gazu.project.get_project.assert_called_with("prod-123")
        self.assertIn("fetched_data", plan[0])
        self.assertEqual(plan[0]["fetched_data"]["id"], "prod-123")
        print("[PASS] Fetch used created_entity ID.")

if __name__ == '__main__':
    unittest.main()
