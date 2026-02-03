# Helper script to run full system
import argparse
from policy_copilot.logging_utils import setup_logging

logger = setup_logging()

def main():
    parser = argparse.ArgumentParser(description="Run full policy copilot system.")
    parser.parse_args()
    logger.info("Running full system B3...")

if __name__ == "__main__":
    main()
