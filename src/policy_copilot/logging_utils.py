import logging
import sys

def setup_logging(name: str = "policy_copilot"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
