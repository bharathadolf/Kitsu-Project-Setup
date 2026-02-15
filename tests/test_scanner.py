import unittest
import os
import sys
import shutil
import tempfile

# Ensure parent directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project_ingester.core.scanner import FolderMapper

class TestFolderMapper(unittest.TestCase):
    def setUp(self):
        # Create a temp directory structure
        self.test_dir = tempfile.mkdtemp()
        
        # Structure:
        # MyProject/
        #   Episodes/
        #     Ep01/
        #       Sq010/
        #       Sq020/
        #     Ep02/
        
        self.proj_dir = os.path.join(self.test_dir, "MyProject")
        os.makedirs(self.proj_dir)
        
        self.eps_root = os.path.join(self.test_dir, "Episodes_Root") # Disconnected root for testing mapping
        os.makedirs(self.eps_root)
        
        os.makedirs(os.path.join(self.eps_root, "Ep01", "Sq010"))
        os.makedirs(os.path.join(self.eps_root, "Ep01", "Sq020"))
        os.makedirs(os.path.join(self.eps_root, "Ep02"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tv_show_mapping(self):
        mapper = FolderMapper()
        
        mappings = {
            "project": self.proj_dir,
            "episode": self.eps_root # Explicitly map episodes to this folder
        }
        
        # We expect:
        # Project(MyProject)
        #   Episode(Ep01)
        #     Sequence(Sq010)
        #     Sequence(Sq020)
        #   Episode(Ep02)
        
        result = mapper.scan_structure("TV Show", mappings)
        
        self.assertEqual(result['type'], 'project')
        self.assertEqual(result['name'], 'MyProject')
        self.assertEqual(len(result['children']), 2) # Ep01, Ep02
        
        ep1 = next((c for c in result['children'] if c['name'] == 'Ep01'), None)
        self.assertIsNotNone(ep1)
        self.assertEqual(ep1['type'], 'episode')
        
        # Check sequences in Ep01
        # They should be discovered automatically because Sequence is child of Episode in TV Show rules
        self.assertEqual(len(ep1['children']), 2)
        seq_names = sorted([c['name'] for c in ep1['children']])
        self.assertEqual(seq_names, ['Sq010', 'Sq020'])

if __name__ == '__main__':
    unittest.main()
