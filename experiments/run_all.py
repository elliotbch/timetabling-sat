#!/usr/bin/env python3
import os, sys, csv, argparse, resource
from time import perf_counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.timetabling import generate_instance, encode
from solver.dpll import dpll, Stats

SIZES = [
    ("S", dict(n_courses=4,  n_rooms=2, n_times=3, n_teachers=2, unavailable_prob=0.10)),
    ("M", dict(n_courses=8,  n_rooms=3, n_times=4, n_teachers=3, unavailable_prob=0.15)),
    ("L", dict(n_courses=12, n_rooms=4, n_times=5, n_teachers=4, unavailable_prob=0.20)),
]

def get_max_rss_mb() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    maxrss = usage.ru_maxrss
    if sys.platform == "darwin":
        return maxrss / (1024*1024)  # bytes -> MB
    else:
        return maxrss / 1024.0       # kB -> MB

def run_suite(seed=20251003):
    rows = []
    for label, params in SIZES:
        inst = generate_instance(seed=seed, **params)
        cnf = encode(inst)
        stats = Stats()
        t0 = perf_counter()
        sat, _ = dpll(cnf, stats=stats)
        t1 = perf_counter()
        rows.append({
            "label": label,
            **params,
            "num_vars": cnf.num_vars,
            "num_clauses": len(cnf.clauses),
            "sat": int(sat),
            "time_sec": round(t1 - t0, 6),
            "decisions": stats.decisions,
            "propagations": stats.propagations,
            "backtracks": stats.backtracks,
            "memory_mb": round(get_max_rss_mb(), 3),
            "seed": seed,
        })
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20251003)
    args = parser.parse_args()
    rows = run_suite(seed=args.seed)
    os.makedirs("experiments", exist_ok=True)
    out = os.path.join("experiments", "results.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()
