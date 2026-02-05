import unittest
import sys
import os

# Add project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_ingester.utils import code_gen

class TestCodeGen(unittest.TestCase):
    def test_project_code(self):
        # < 10 chars
        self.assertEqual(code_gen.generate_project_code("MyProj"), "MYP")
        self.assertEqual(code_gen.generate_project_code("ShortNm"), "SHO") 
        
        # >= 10 chars, 5-letter Acronym
        # "A Very Long Project Name" -> Words: A, Very, Long, Project, Name -> AVLPN (5 chars)
        self.assertEqual(code_gen.generate_project_code("A Very Long Project Name"), "AVLPN")
        
        # Fallback (Acronym too short)
        # "A Long Project Name" -> ALPN (4 chars) -> Fallback to "ALONG"
        self.assertEqual(code_gen.generate_project_code("A Long Project Name"), "ALONG")

    def test_incremental_code(self):
        existing = ["seq01", "seq02"]
        self.assertEqual(code_gen.generate_incremental_code("seq", existing, 0), "seq03")
        self.assertEqual(code_gen.generate_incremental_code("seq", existing, 1), "seq04")
        
        existing_empty = []
        self.assertEqual(code_gen.generate_incremental_code("ep", existing_empty, 0), "ep01")

        # Test case insensitive
        existing_caps = ["SEQ01", "SEQ02"]
        self.assertEqual(code_gen.generate_incremental_code("seq", existing_caps, 0), "seq03")

    def test_shot_code(self):
        self.assertEqual(code_gen.generate_shot_code("seq01", 1), "seq01_sh01")
        self.assertEqual(code_gen.generate_shot_code("seq03", 10), "seq03_sh10")

    def test_asset_code(self):
        self.assertEqual(code_gen.generate_asset_code("Character", "Hero Boy"), "character_hero_boy")

if __name__ == '__main__':
    unittest.main()
