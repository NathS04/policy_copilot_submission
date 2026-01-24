"""
run_eval must persist backend provenance in run_config.json.
When dense is requested but unavailable in core env, backend_used should show bm25 fallback.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from policy_copilot.config import settings


class TestBackendProvenanceWritten(unittest.TestCase):
    def test_run_config_writes_backend_requested_and_used(self):
        original_output_dir = settings.OUTPUT_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            settings.OUTPUT_DIR = Path(tmpdir)
            try:
                from scripts.run_eval import run_baseline

                mock_retriever = MagicMock()
                mock_retriever.loaded = True
                mock_retriever.backend_requested = "dense"
                mock_retriever.backend_used = "bm25"
                mock_retriever.retrieve.return_value = []

                fake_df = MagicMock()
                fake_df.iterrows.return_value = []
                fake_df.__len__.return_value = 0
                fake_df.columns = []

                with patch("scripts.run_eval.Answerer"), \
                     patch("scripts.run_eval.Retriever", return_value=mock_retriever), \
                     patch("scripts.run_eval._load_existing_outputs", return_value=set()), \
                     patch("pandas.read_csv", return_value=fake_df), \
                     patch("scripts.run_eval._write_run_readme"), \
                     patch("scripts.run_eval._write_summary_metrics"), \
                     patch("policy_copilot.config.Settings.get_output_dir", return_value=Path(tmpdir) / "prov_run"):
                    run_baseline(
                        "b2",
                        "dummy_gold.csv",
                        "prov_run",
                        force=True,
                        ablations={"backend": "dense", "allow_fallback": True},
                        split="test",
                        cli_args={"baseline": "b2", "backend": "dense"},
                    )

                cfg_path = Path(tmpdir) / "prov_run" / "run_config.json"
                self.assertTrue(cfg_path.exists(), "run_config.json must be written")
                with open(cfg_path) as f:
                    cfg = json.load(f)

                self.assertEqual(cfg.get("backend_requested"), "dense")
                self.assertEqual(cfg.get("backend_used"), "bm25")
                self.assertIn("cli_args", cfg)
            finally:
                settings.OUTPUT_DIR = original_output_dir


if __name__ == "__main__":
    unittest.main()
