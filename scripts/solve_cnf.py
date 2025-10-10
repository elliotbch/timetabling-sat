#!/usr/bin/env python3
import os, sys
# --- make project root importable (so "import solver" works when running this script directly)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import argparse
from solver.cnf import parse_dimacs_file
from solver.dpll import dpll, Trace

def main():
    ap = argparse.ArgumentParser(description="Solve a CNF (DIMACS) with our DPLL.")
    ap.add_argument("cnf_path", help="Path to the .cnf (DIMACS) file")
    ap.add_argument("--model", action="store_true",
                    help="Print a DIMACS-style model line (v ... 0) when SAT")
    ap.add_argument("--trace", action="store_true",
                    help="Print a simple UNSAT trace/log (decide/unit/pure/conflict/backtrack)")
    ap.add_argument("--no-heuristic", action="store_true",
                    help="Disable DLIS-lite branching heuristic (use naive first-unassigned)")
    args = ap.parse_args()

    # Parse CNF
    cnf = parse_dimacs_file(args.cnf_path)


    tr = Trace() if args.trace else None
    use_heuristic = not args.no_heuristic

    sat, model = dpll(cnf, trace=tr, use_heuristic=use_heuristic)

    if sat:
        print("SAT")
        if args.model:
            vals = []
            for v in range(1, cnf.num_vars + 1):
                vals.append(str(v if model.get(v, False) else -v))
            print("v " + " ".join(vals) + " 0")
        sys.exit(0)
    else:
        print("UNSAT")
        if tr is not None:
            # Print a minimal contradiction trace
            for e in tr:
                # e.kind in {"decide","unit","pure","conflict","backtrack","sat"}
                if e.kind == "sat":
                    
                    print("sat")
                else:
                    var = f"{e.var}" if e.var is not None else "-"
                    val = "T" if e.val is True else ("F" if e.val is False else "-")
                    note = f" ({e.note})" if e.note else ""
                    print(f"{e.kind}: var={var} val={val}{note}")
        # Common convention: 20 for UNSAT
        sys.exit(20)

if __name__ == "__main__":
    main()
