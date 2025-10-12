
import unittest
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from policy_copilot.config import settings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

class TestRunConfig(unittest.TestCase):
    def test_run_config_has_mode_and_backend(self):
        """scripts/run_eval.py should save mode and backend to run_config.json."""
        # This is an integration test of run_baseline's config saving logic.
        # We can import run_baseline safely if we mock components it uses.
        
        # We'll use a temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            # Update settings to point to this tmpdir
            original_output_dir = settings.OUTPUT_DIR
            settings.OUTPUT_DIR = Path(tmpdir)
            
            try:
                # Import here to avoid early side effects if any
                from scripts.run_eval import run_baseline
                
                # Mock loaded components to avoid actual compute
                mock_retriever_instance = MagicMock()
                mock_retriever_instance.loaded = True
                mock_retriever_instance.backend_used = "bm25"
                mock_retriever_instance.backend_requested = "bm25"

                with patch("scripts.run_eval.Answerer"), \
                     patch("scripts.run_eval.Retriever", return_value=mock_retriever_instance), \
                     patch("scripts.run_eval._load_existing_outputs", return_value=set()), \
                     patch("pandas.read_csv", return_value=MagicMock(iterrows=lambda: [])), \
                     patch("scripts.run_eval._write_run_readme"), \
                     patch("scripts.run_eval._write_summary_metrics"), \
                     patch("policy_copilot.config.Settings.get_output_dir", return_value=Path(tmpdir) / "test_run"):
                    
                    # Run a dummy baseline
                    ablations = {"backend": "bm25", "allow_fallback": True}
                    run_baseline("b2", "dummy_gold.csv", "test_run", ablations=ablations)
                    
                    # Check run_config.json
                    run_dir = Path(tmpdir) / "test_run"
                    config_path = run_dir / "run_config.json"
                    
                    self.assertTrue(config_path.exists())
                    with open(config_path) as f:
                        cfg = json.load(f)
                        
                    self.assertIn("ablations", cfg)
                    self.assertEqual(cfg["ablations"].get("backend"), "bm25")
                    self.assertEqual(cfg["ablations"].get("allow_fallback"), True)
                    # Check mode is present (inferred or explicit)
                    self.assertIn("mode", cfg)
                    
            finally:
                settings.OUTPUT_DIR = original_output_dir

if __name__ == "__main__":
    unittest.main()
