import argparse
import json
import sys
from pathlib import Path

from policy_copilot.config import settings
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()


def build_index(input_path: Path, index_dir: Path) -> None:
