#!/usr/bin/env python3
import os, sys, csv, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from models.timetabling import generate_instance, encode
from solver.cnf import CNF

def pysat_build_and_solve(cnf: CNF):
    t_build0 = time.perf_counter()
    from pysat.solvers import Minisat22
    with Minisat22() as m:
        for cl in cnf.clauses:
            m.add_clause(cl)
        t_build1 = time.perf_counter()
        t_solve0 = time.perf_counter()
        sat = m.solve()
        t_solve1 = time.perf_counter()
        model = m.get_model() if sat else None
    return sat, model, (t_build1 - t_build0), (t_solve1 - t_solve0)

def z3_build_and_solve(cnf: CNF):
    t_build0 = time.perf_counter()
    from z3 import Solver, Bool, Or, And, Not, sat as Z3SAT
    X = {v: Bool(f"x{v}") for v in range(1, cnf.num_vars+1)}
    s = Solver()
    z3_clauses = []
    for cl in cnf.clauses:
        lits = [(X[abs(l)] if l > 0 else Not(X[abs(l)])) for l in cl]
        z3_clauses.append(Or(lits))
    s.add(And(z3_clauses))
    t_build1 = time.perf_counter()
    t_solve0 = time.perf_counter()
    r = s.check()
    t_solve1 = time.perf_counter()
    if r == Z3SAT:
        m = s.model()
        model = [v if m.evaluate(X[v], model_completion=True) else -v for v in X]
        sat = True
    else:
        model, sat = None, False
    return sat, model, (t_build1 - t_build0), (t_solve1 - t_solve0)

def main():
    SIZES = [
        ("S", dict(n_courses=4,  n_rooms=2, n_times=3, n_teachers=2, unavailable_prob=0.10)),
        ("M", dict(n_courses=8,  n_rooms=3, n_times=4, n_teachers=3, unavailable_prob=0.15)),
        ("L", dict(n_courses=12, n_rooms=4, n_times=5, n_teachers=4, unavailable_prob=0.20)),
    ]
    rows = []
    for label, params in SIZES:
        inst = generate_instance(seed=20251003, **params)
        cnf = encode(inst)

        sat_py, _, build_py, solve_py = pysat_build_and_solve(cnf)
        sat_z3, _, build_z3, solve_z3 = z3_build_and_solve(cnf)

        rows.append({
            "label": label, **params,
            "num_vars": cnf.num_vars, "num_clauses": len(cnf.clauses),
            "pysat_sat": int(sat_py), "pysat_build": round(build_py, 6), "pysat_solve": round(solve_py, 6),
            "z3_sat": int(sat_z3),   "z3_build": round(build_z3, 6),     "z3_solve": round(solve_z3, 6),
        })

    os.makedirs("experiments", exist_ok=True)
    out = os.path.join("experiments", "baseline.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {out}")
    for r in rows:
        print(r)

if __name__ == "__main__":
    main()
