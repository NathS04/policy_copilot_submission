# Helper script to run only baselines
import argparse
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

def main():
    parser = argparse.ArgumentParser(description="Run baseline models.")
    parser.parse_args()
    logger.info("Running baselines B1 & B2...")

if __name__ == "__main__":
    main()
