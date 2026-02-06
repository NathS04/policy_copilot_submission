"""
Reproducibility script: Run all experiments and regenerate figures/tables.
Usage: python scripts/run_all_experiments.py
"""
import subprocess
import sys

def run_command(cmd_list):
    # Use the current python executable to ensure we use the venv
    if cmd_list[0] == "python":
        cmd_list[0] = sys.executable

    print(f"Running: {' '.join(cmd_list)}")
    try:
        subprocess.run(cmd_list, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)

def main():
    print("=== STARTING FULL EXPERIMENTAL RUN ===")
    
    # 1. Run Baselines on All splits
    # B1 (Prompt Only)
    run_command(["python", "scripts/run_eval.py", "--baseline", "b1", "--split", "all", "--force"])
    
    # B2 (Naive RAG)
    run_command(["python", "scripts/run_eval.py", "--baseline", "b2", "--split", "all", "--force"])
    
    # B3 (Full System) - Default Generative
    run_command(["python", "scripts/run_eval.py", "--baseline", "b3", "--split", "all", "--force"])
    
    # 2. Run Ablations (B3 variants)
    # No Rerank
    run_command([
        "python", "scripts/run_eval.py", "--baseline", "b3", "--split", "all", 
        "--no_rerank", "--run_name", "b3_ablation_no_rerank", "--force"
    ])
    
    # No Verify (Ungrounded check)
    run_command([
        "python", "scripts/run_eval.py", "--baseline", "b3", "--split", "all", 
        "--no_verify", "--run_name", "b3_ablation_no_verify", "--force"
    ])

    # 3. Generate Figures & Tables
    print("=== GENERATING FIGURES ===")
    run_command(["python", "eval/analysis/make_figures.py"])
    
    print("=== DONE ===")
    print("Results updated in results/tables/ and results/figures/")

if __name__ == "__main__":
    main()
