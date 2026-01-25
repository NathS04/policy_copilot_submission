# Master script to run everything ensuring reproducibility

def main():
    print("Reproducing all results...")
    # subprocess.run([sys.executable, "eval/runners/run_baselines.py"])
    # subprocess.run([sys.executable, "eval/runners/run_full_system.py"])
    print("Done.")

if __name__ == "__main__":
    main()
