
import unittest
import subprocess
import sys

class TestBuildIndexHelp(unittest.TestCase):
    def test_help_does_not_crash(self):
        """scripts/build_index.py --help should exit with 0."""
        # We run it as a subprocess to simulate a fresh environment state
        result = subprocess.run(
            [sys.executable, "scripts/build_index.py", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Command failed: {result.stderr}")
        self.assertIn("usage:", result.stdout)

if __name__ == "__main__":
    unittest.main()
