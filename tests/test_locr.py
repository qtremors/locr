import unittest
import os
import shutil
import tempfile
import sys

# Ensure import of locr from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from locr import LocrEngine, Colors

class TestLocr(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for each test
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def create_file(self, path, content):
        """Helper to create files easily inside the temp dir."""
        full_path = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return full_path

    def test_python_counts(self):
        """Test basic counting logic for Python."""
        content = (
            "import os\n"           # Code
            "\n"                    # Blank
            "# This is a comment\n" # Comment
            "def main():\n"         # Code
            "    pass\n"            # Code
        )
        self.create_file("main.py", content)

        engine = LocrEngine(self.test_dir)
        results = engine.scan()

        py_stats = results["Python"]
        self.assertEqual(py_stats["files"], 1)
        self.assertEqual(py_stats["code"], 3)
        self.assertEqual(py_stats["comment"], 1)
        self.assertEqual(py_stats["blank"], 1)

    def test_default_ignores(self):
        """Ensure node_modules is ignored by default."""
        self.create_file("node_modules/junk.js", "console.log('ignore me');")
        self.create_file("src/valid.js", "console.log('count me');")

        engine = LocrEngine(self.test_dir)
        results = engine.scan()

        # Should only find the valid.js, ignoring node_modules completely
        self.assertEqual(results["JavaScript"]["files"], 1)

    def test_gitignore_respect(self):
        """Ensure .gitignore rules are respected."""
        # 1. Create a .gitignore
        self.create_file(".gitignore", "*.log\nsecret.py")
        
        # 2. Create files that should be ignored
        self.create_file("error.log", "error data")
        self.create_file("secret.py", "api_key = '123'")
        
        # 3. Create a valid file
        self.create_file("app.py", "print('hello')")

        engine = LocrEngine(self.test_dir)
        results = engine.scan()

        # Python should only see app.py (1 file), ignoring secret.py
        self.assertEqual(results["Python"]["files"], 1)
        # Should not find any log files (assuming .log isn't in LANGUAGES anyway, 
        # but secret.py IS in LANGUAGES, so checking that confirms gitignore works)

    def test_heuristic_edge_cases(self):
        """ 
        Testing the limitations of the heuristic scanner.
        """
        content = (
            "x = 1\n"                       # Code
            "s = '# This is a string'\n"    # Code (Should be code)
            "   # Indented comment\n"       # Comment (Should be comment)
            "print('Hash # inside')\n"      # Code
        )
        self.create_file("edge_case.py", content)

        engine = LocrEngine(self.test_dir)
        results = engine.scan()
        py = results["Python"]

        # Line 1: Code.
        # Line 2: Code. (scanner checks .startswith('#'). It does not. Correct.)
        # Line 3: Comment. (scanner strips whitespace. .startswith('#'). Correct.)
        # Line 4: Code.
        
        # If this test PASSES, heuristic is good!
        self.assertEqual(py["code"], 3)
        self.assertEqual(py["comment"], 1)

    def test_multi_line_comments(self):
        """Test block comments (docstrings)."""
        content = (
            '"""\n'             # Comment (Block start)
            'This is a docstring\n' # Comment
            '"""\n'             # Comment (Block end)
            'x = 10'            # Code
        )
        self.create_file("doc.py", content)
        
        engine = LocrEngine(self.test_dir)
        results = engine.scan()
        
        self.assertEqual(results["Python"]["comment"], 3)
        self.assertEqual(results["Python"]["code"], 1)

if __name__ == '__main__':
    unittest.main()