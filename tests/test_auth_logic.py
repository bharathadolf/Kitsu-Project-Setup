
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Path setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils.compat import QApplication
# Create App for Widgets
app = QApplication.instance() or QApplication(sys.argv)

from project_ingester.core.setup import ProjectManager
from project_ingester.ui.dialogs import LoginDialog

class TestAuthLogic(unittest.TestCase):
    

    @patch('project_ingester.core.setup.gazu')
    @patch('project_ingester.core.setup.LoginDialog')
    def test_connect_success_first_try(self, MockDialog, mock_gazu):
        """Test that if gazu.log_in works, no dialog is shown."""
        mock_log = MagicMock()
        manager = ProjectManager(log_callback=mock_log)
        result = manager.connect()
        
        self.assertTrue(result)
        mock_gazu.log_in.assert_called_once()
        MockDialog.assert_not_called()

    @patch('project_ingester.core.setup.gazu')
    @patch('project_ingester.core.setup.LoginDialog')
    def test_connect_fail_then_cancel(self, MockDialog, mock_gazu):
        """Test failure then user verify cancel."""
        # Fail first login
        mock_gazu.log_in.side_effect = Exception("Auth Failed")
        
        # Configure Mock Dialog to return Rejected (False)
        mock_instance = MockDialog.return_value
        mock_instance.exec_.return_value = False
        
        mock_log = MagicMock()
        manager = ProjectManager(log_callback=mock_log)
        result = manager.connect()
        
        self.assertFalse(result)
        # Attempted login once
        self.assertEqual(mock_gazu.log_in.call_count, 1)
        # Showed dialog
        MockDialog.assert_called_once()

    @patch('project_ingester.core.setup.gazu')
    @patch('project_ingester.core.setup.LoginDialog')
    def test_connect_fail_then_retry_success(self, MockDialog, mock_gazu):
        """Test failure, then user enters creds, then success."""
        # First call fails, Second call succeeds
        mock_gazu.log_in.side_effect = [Exception("Fail"), None]
        
        # Configure Mock Dialog
        mock_instance = MockDialog.return_value
        mock_instance.exec_.return_value = True # Accepted
        mock_instance.get_credentials.return_value = ("http://new", "new@mail.com", "newpass")
        
        mock_log = MagicMock()
        manager = ProjectManager(log_callback=mock_log)
        result = manager.connect()
        
        self.assertTrue(result)
        # Logged in twice (1 fail, 1 success)
        self.assertEqual(mock_gazu.log_in.call_count, 2)
        
        # Verify second call used new credentials
        mock_gazu.set_host.assert_called_with("http://new")
        mock_gazu.log_in.assert_called_with("new@mail.com", "newpass")

if __name__ == '__main__':
    unittest.main()
