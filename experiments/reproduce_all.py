# experiments/reproduce_all.py
#!/usr/bin/env python3
import os, sys, subprocess, argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    ap = argparse.ArgumentParser(description="Reproduce all tables/plots.")
    ap.add_argument("--seed", type=int, default=20251003)
    args = ap.parse_args()

    run([sys.executable, "experiments/run_all.py", "--seed", str(args.seed)])
    run([sys.executable, "experiments/baseline_compare.py"])
    run([sys.executable, "experiments/plot_results.py"])
    print("All done. See experiments/results.csv, experiments/baseline.csv and experiments/plots/.")

if __name__ == "__main__":
    main()
