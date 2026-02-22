from pathlib import Path

REPO_DIR = Path("/Users/natha/Documents/All Files/UOL/3rd Year Comp sci/Dissertation/policy_copilot_submission")
BACKUP_DIR = REPO_DIR.parent / "policy_copilot_backup_tmp"

test_path = ".gitignore"
src = BACKUP_DIR / test_path
print(f"Src .gitignore exists? {src.exists()} at {src}")
