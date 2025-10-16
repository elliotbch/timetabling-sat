import os, pandas as pd, matplotlib.pyplot as plt

def main():
    df = pd.read_csv("experiments/results.csv")
    print(df)
    os.makedirs("experiments/plots", exist_ok=True)

    # Runtime 
    plt.figure(figsize=(5,3))
    plt.bar(df["label"], df["time_sec"], color=["#6aa84f","#3d85c6","#cc0000"])
    plt.title("Solve time by size (our DPLL)")
    plt.xlabel("Size"); plt.ylabel("seconds")
    plt.tight_layout(); plt.savefig("experiments/plots/time_by_size.png")

    # Stats
    for col in ["decisions","propagations","backtracks"]:
        if col in df.columns:
            plt.figure(figsize=(5,3))
            plt.bar(df["label"], df[col], color=["#6aa84f","#3d85c6","#cc0000"])
            plt.title(f"{col.title()} by size")
            plt.xlabel("Size"); plt.ylabel(col)
            plt.tight_layout(); plt.savefig(f"experiments/plots/{col}_by_size.png")

    # Baseline vs ours
    try:
        bl = pd.read_csv("experiments/baseline.csv")
        m = df[["label","time_sec"]].merge(bl[["label","pysat_solve","z3_solve"]], on="label")
        plt.figure(figsize=(6,3))
        x = range(len(m))
        width = 0.25
        plt.bar([i - width for i in x], m["time_sec"], width=width, label="Our DPLL")
        plt.bar(x, m["pysat_solve"], width=width, label="PySAT solve")
        plt.bar([i + width for i in x], m["z3_solve"], width=width, label="Z3 check()")
        plt.xticks(list(x), m["label"])
        plt.ylabel("seconds"); plt.title("Our solver vs Baseline (solve-only)")
        plt.legend()
        plt.tight_layout(); plt.savefig("experiments/plots/compare_baseline.png")
    except Exception as e:
        print("Baseline CSV not found or incompatible:", e)

    print("Wrote plots in experiments/plots/")

if __name__ == "__main__":
    main()
