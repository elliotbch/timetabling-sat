#!/usr/bin/env python3

import os, sys, argparse
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# --- Defaults for PDF-ready figures ---
def set_style(dark=False):
    # Font and DPI for crisp PDF/PNG
    matplotlib.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.fontsize": 10,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.autolayout": True,
    })
    if dark:
        plt.style.use("dark_background")
        # lighten grid in dark mode
        matplotlib.rcParams.update({
            "grid.color": "#BBBBBB",
        })
    else:
        # colorblind-friendly palette
        plt.style.use("seaborn-v0_8-whitegrid")

def ensure_dirs():
    os.makedirs("experiments/plots", exist_ok=True)

def savefig(base, fmt):
    path = f"experiments/plots/{base}.{fmt}"
    plt.savefig(path, bbox_inches="tight", transparent=False)
    print("Wrote", path)

def label_bars(ax, fmt="{:.3g}"):
    for p in ax.patches:
        h = p.get_height()
        if h <= 0:
            continue
        ax.annotate(fmt.format(h),
                    (p.get_x() + p.get_width()/2, h),
                    ha="center", va="bottom", xytext=(0, 2),
                    textcoords="offset points", fontsize=9)

def map_size_order(df):
    # enforce S, M, L ordering even if CSV is shuffled
    order = {"S": 0, "M": 1, "L": 2}
    if "label" in df.columns:
        df = df.copy()
        df["_ord"] = df["label"].map(order)
        df = df.sort_values("_ord").drop(columns=["_ord"])
    return df

def load_csvs():
    res = pd.read_csv("experiments/results.csv")
    res = map_size_order(res)
    # baseline is optional
    bl = None
    if os.path.exists("experiments/baseline.csv"):
        bl = pd.read_csv("experiments/baseline.csv")
        bl = map_size_order(bl)
    return res, bl

def bar_time_ours(df, fmt):
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    colors = ["#0072B2", "#009E73", "#D55E00"]  # colorblind-friendly
    ax.bar(df["label"], df["time_sec"], color=colors, edgecolor="black", linewidth=0.6)
    ax.set_title("Solve time by size (our DPLL)")
    ax.set_xlabel("Instance size")
    ax.set_ylabel("Time (s)")
    label_bars(ax, fmt="{:.3g}")
    savefig("time_by_size", fmt)
    plt.close(fig)

def bar_stats(df, col, title, ylab, base_name, fmt):
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    colors = ["#0072B2", "#009E73", "#D55E00"]
    ax.bar(df["label"], df[col], color=colors, edgecolor="black", linewidth=0.6)
    ax.set_title(title)
    ax.set_xlabel("Instance size")
    ax.set_ylabel(ylab)
    label_bars(ax, fmt="{:.3g}")
    savefig(base_name, fmt)
    plt.close(fig)

def bar_memory(df, fmt):
    if "memory_mb" not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    colors = ["#0072B2", "#009E73", "#D55E00"]
    ax.bar(df["label"], df["memory_mb"], color=colors, edgecolor="black", linewidth=0.6)
    ax.set_title("Memory footprint (resident) by size")
    ax.set_xlabel("Instance size")
    ax.set_ylabel("MB")
    label_bars(ax, fmt="{:.3g}")
    savefig("memory_by_size", fmt)
    plt.close(fig)

def grouped_baseline(df_res, df_bl, fmt, solve_only=True, logy=False):
    if df_bl is None:
        print("baseline.csv not found — skipping baseline plots.")
        return
    # Merge on label to align rows
    m = df_res[["label", "time_sec"]].merge(
        df_bl[["label", "pysat_solve", "z3_solve", "pysat_build", "z3_build"]],
        on="label", how="inner"
    )
    # choose columns
    if solve_only:
        series = [("Our DPLL", "time_sec"),
                  ("PySAT solve", "pysat_solve"),
                  ("Z3 solve", "z3_solve")]
        title = "Solve time comparison (solve-only)"
        base = "compare_baseline_solve"
    else:
        series = [("Our DPLL", "time_sec"),
                  ("PySAT build", "pysat_build"),
                  ("PySAT solve", "pysat_solve"),
                  ("Z3 build", "z3_build"),
                  ("Z3 solve", "z3_solve")]
        title = "Time comparison (build and solve)"
        base = "compare_baseline_build_solve"

    # Plot grouped bars
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    n = len(series)
    width = 0.8 / n
    x = range(len(m))
    colors = ["#0072B2", "#56B4E9", "#009E73", "#E69F00", "#CC79A7"]  # colorblind set
    for i, (label, col) in enumerate(series):
        ax.bar([xi + (i - n/2 + 0.5)*width for xi in x],
               m[col], width=width, label=label,
               color=colors[i % len(colors)], edgecolor="black", linewidth=0.5)
    ax.set_xticks(list(x)); ax.set_xticklabels(m["label"])
    ax.set_title(title)
    ax.set_xlabel("Instance size"); ax.set_ylabel("Time (s)")
    if logy:
        ax.set_yscale("log")
        ax.set_ylabel("Time (s, log scale)")
    ax.legend(ncol=3, frameon=False)
    savefig(base + ("_log" if logy else ""), fmt)
    plt.close(fig)

def scatter_clauses_time(df, fmt):
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.scatter(df["num_clauses"], df["time_sec"], s=40, color="#0072B2", edgecolor="black", linewidth=0.5)
    for _, row in df.iterrows():
        ax.annotate(row["label"], (row["num_clauses"], row["time_sec"]),
                    textcoords="offset points", xytext=(5, 3), fontsize=9)
    ax.set_title("Runtime vs number of clauses (our DPLL)")
    ax.set_xlabel("#Clauses")
    ax.set_ylabel("Time (s)")
    savefig("runtime_vs_clauses", fmt)
    plt.close(fig)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=["light","dark"], default="light")
    ap.add_argument("--fmt", choices=["png","svg"], default="png",
                    help="Output format. SVG recommended for LaTeX/PDF.")
    args = ap.parse_args()

    set_style(dark=(args.style=="dark"))
    ensure_dirs()
    df_res, df_bl = load_csvs()

    # Our solver plots
    bar_time_ours(df_res, args.fmt)
    for col, title, ylab, base in [
        ("decisions", "Decisions by size (our DPLL)", "Count", "decisions_by_size"),
        ("propagations", "Propagations by size (our DPLL)", "Count", "propagations_by_size"),
        ("backtracks", "Backtracks by size (our DPLL)", "Count", "backtracks_by_size"),
    ]:
        if col in df_res.columns:
            bar_stats(df_res, col, title, ylab, base, args.fmt)
    bar_memory(df_res, args.fmt)

    # Baseline comparisons
    grouped_baseline(df_res, df_bl, args.fmt, solve_only=True, logy=False)
    grouped_baseline(df_res, df_bl, args.fmt, solve_only=True, logy=True)
    grouped_baseline(df_res, df_bl, args.fmt, solve_only=False, logy=False)

    # Extra: scatter of clauses vs time
    scatter_clauses_time(df_res, args.fmt)

    print("All plots generated in experiments/plots/")

if __name__ == "__main__":
    main()
