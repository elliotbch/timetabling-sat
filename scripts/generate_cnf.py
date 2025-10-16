#!/usr/bin/env python3
import os, sys, argparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.timetabling import generate_instance, encode

def main():
    ap = argparse.ArgumentParser(description="Generate a timetabling CNF (DIMACS).")
    ap.add_argument("--courses", type=int, default=6)
    ap.add_argument("--rooms", type=int, default=3)
    ap.add_argument("--times", type=int, default=4)
    ap.add_argument("--teachers", type=int, default=2)
    ap.add_argument("--unavail", type=float, default=0.15, help="unavailable probability per teacher×slot")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=str, default="samples/timetable.cnf")
    args = ap.parse_args()

    inst = generate_instance(args.courses, args.rooms, args.times,
                             n_teachers=args.teachers, unavailable_prob=args.unavail,
                             seed=args.seed)
    cnf = encode(inst)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write(cnf.to_dimacs())
    print(f"Wrote {args.out} with {cnf.num_vars} vars and {len(cnf.clauses)} clauses")

if __name__ == "__main__":
    main()
