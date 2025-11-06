"""
--------------------------------------------------------
 Timetabling → CNF encoder + Standalone CLI
--------------------------------------------------------
Run examples (from the project root):

  Small built-in demo (for testing & video demo)
  python -m models.timetabling --demo --model

  Predefined sizes (as in the experiments)
  python -m models.timetabling --size S --seed 06 --model
  python -m models.timetabling --size M --seed 34
  python -m models.timetabling --size L --seed 6 --no-heuristic

  Fully custom instance
  python -m models.timetabling --courses 6 --rooms 3 --times 4 --teachers 3 \
      --unavail 0.15 --seed 42 --model

Export CNF to DIMACS format (for external solver)
  python -m models.timetabling --size S --dump-cnf experiments/tmp_s.cnf
--------------------------------------------------------
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import argparse
import random
import time
import os

from solver.cnf import CNF
from solver.dpll import dpll, Trace, Stats

# --- Types (aliases for clarity) ---
Course  = str
Room    = str
Time    = str
Teacher = str

@dataclass
class Instance:
    """
    Timetabling instance:
    - courses/rooms/times are identifiers (strings)
    - teacher_of maps each course to exactly one teacher
    - teacher_available maps each teacher to a list of allowed time slots
    """
    courses: List[Course]
    rooms: List[Room]
    times: List[Time]
    teacher_of: Dict[Course, Teacher]
    teacher_available: Dict[Teacher, List[Time]]  # allowed times per teacher

# ---------------------------------------------------------------------
# Variable mapping: (c,r,t) -> DIMACS variable id in [1..N]
# ---------------------------------------------------------------------
def var_index(inst: Instance, c: Course, r: Room, t: Time) -> int:
    """
    Map (course, room, time) to a unique positive integer (1-based).
    Layout: 1 + c*(|R|*|T|) + r*|T| + t
    """
    ci = inst.courses.index(c)
    ri = inst.rooms.index(r)
    ti = inst.times.index(t)
    nR = len(inst.rooms)
    nT = len(inst.times)
    return 1 + ci * (nR * nT) + ri * nT + ti

# ---------------------------------------------------------------------
# CNF encoder
# ---------------------------------------------------------------------
def encode(inst: Instance) -> CNF:
    """
    Build CNF with hard constraints:
      (1) Exactly one (room,time) per course
      (2) At most one course per (room,time)
      (3) Same teacher cannot teach two courses at the same time
      (4) Teacher availability respected
    """
    nvars = len(inst.courses) * len(inst.rooms) * len(inst.times)
    cnf = CNF(num_vars=nvars)
    C, R, T = inst.courses, inst.rooms, inst.times

    # (1) Exactly-one for each course: at least-one + at-most-one (pairwise)
    for c in C:
        ids = [var_index(inst, c, r, t) for r in R for t in T]
        # at least one
        cnf.add_clause(ids)
        # at most one (pairwise)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                cnf.add_clause([-ids[i], -ids[j]])

    # (2) At most one course per (room,time)
    for r in R:
        for t in T:
            ids = [var_index(inst, c, r, t) for c in C]
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    cnf.add_clause([-ids[i], -ids[j]])

    # (3) Teacher cannot teach two courses at the same time
    for i in range(len(C)):
        for j in range(i + 1, len(C)):
            c1, c2 = C[i], C[j]
            if inst.teacher_of[c1] != inst.teacher_of[c2]:
                continue
            for t in T:
                ids1 = [var_index(inst, c1, r, t) for r in R]
                ids2 = [var_index(inst, c2, r, t) for r in R]
                for a in ids1:
                    for b in ids2:
                        cnf.add_clause([-a, -b])

    # (4) Teacher availability
    for c in C:
        teacher = inst.teacher_of[c]
        allowed = set(inst.teacher_available.get(teacher, T))  # default: all allowed
        for t in T:
            if t not in allowed:
                for r in R:
                    cnf.add_clause([-var_index(inst, c, r, t)])

    return cnf

# ---------------------------------------------------------------------
# Model decoder (CNF model → concrete timetable)
# ---------------------------------------------------------------------
def decode(inst: Instance, model: Dict[int, bool]) -> List[Tuple[Course, Room, Time]]:
    """
    Convert a satisfying model (variable→bool) into a readable schedule:
    returns a list of (course, room, time) for all x[c,r,t] set to True.
    """
    out: List[Tuple[Course, Room, Time]] = []
    for c in inst.courses:
        for r in inst.rooms:
            for t in inst.times:
                v = var_index(inst, c, r, t)
                if model.get(v) is True:
                    out.append((c, r, t))
    return out

# ---------------------------------------------------------------------
# Demos & Generators
# ---------------------------------------------------------------------
def small_demo_instance() -> Instance:
    """
    Small deterministic instance:
      - 2 courses, 2 rooms, 3 times
      - both courses share the same teacher (forces separation in time)
      - teacher is available at all times
    """
    courses = ["C1", "C2"]
    rooms = ["R1", "R2"]
    times = ["T1", "T2", "T3"]
    teacher_of = {"C1": "A", "C2": "A"}
    teacher_available = {"A": ["T1", "T2", "T3"]}
    return Instance(courses, rooms, times, teacher_of, teacher_available)


def generate_instance(
    n_courses: int, n_rooms: int, n_times: int,
    n_teachers: int = 2,
    unavailable_prob: float = 0.0,
    seed: Optional[int] = 0
) -> Instance:
    """
    Pseudo-random instance:
      - Each course gets a random teacher.
      - For each teacher & time, availability is true with prob (1 - unavailable_prob).
      - We guarantee at least one allowed time per teacher.
    """
    rnd = random.Random(seed)

    courses  = [f"C{i+1}" for i in range(n_courses)]
    rooms    = [f"R{j+1}" for j in range(n_rooms)]
    times    = [f"T{k+1}" for k in range(n_times)]
    teachers = [f"P{p+1}" for p in range(n_teachers)]

    teacher_of: Dict[str, str] = {c: rnd.choice(teachers) for c in courses}

    teacher_available: Dict[str, List[str]] = {}
    for t in teachers:
        allowed = [tt for tt in times if rnd.random() > unavailable_prob]
        if not allowed:
            allowed = [rnd.choice(times)]
        teacher_available[t] = allowed

    return Instance(courses, rooms, times, teacher_of, teacher_available)

# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Encode and solve a timetabling instance with the custom DPLL solver."
    )
    g = ap.add_mutually_exclusive_group(required=False)
    g.add_argument("--demo", action="store_true", help="Run the built-in tiny demo instance.")
    g.add_argument("--size", choices=["S", "M", "L"], help="Predefined sizes.")

    ap.add_argument("--courses", type=int, help="Number of courses (custom mode).")
    ap.add_argument("--rooms", type=int, help="Number of rooms (custom mode).")
    ap.add_argument("--times", type=int, help="Number of time slots (custom mode).")
    ap.add_argument("--teachers", type=int, default=2, help="Number of teachers (custom).")
    ap.add_argument("--unavail", type=float, default=0.0,
                    help="Teacher unavailability probability in [0,1].")
    ap.add_argument("--seed", type=int, default=0, help="Random seed.")

    ap.add_argument("--model", action="store_true", help="Print decoded timetable if SAT.")
    ap.add_argument("--trace", action="store_true", help="Print a short decision/propagation trace.")
    ap.add_argument("--no-heuristic", action="store_true", help="Disable DLIS-lite (use naive order).")
    ap.add_argument("--dump-cnf", type=str, help="Path to export the CNF in DIMACS.")
    return ap.parse_args()


def build_instance_from_args(args: argparse.Namespace) -> Instance:
    if args.demo:
        return small_demo_instance()

    if args.size:
        # Suggested sizes (align with your experiments/run_all.py)
        if args.size == "S":
            return generate_instance(4, 2, 3, n_teachers=2, unavailable_prob=0.10, seed=args.seed)
        if args.size == "M":
            return generate_instance(8, 3, 4, n_teachers=3, unavailable_prob=0.15, seed=args.seed)
        if args.size == "L":
            return generate_instance(12, 4, 5, n_teachers=4, unavailable_prob=0.20, seed=args.seed)

    # Custom mode: require courses/rooms/times
    if args.courses and args.rooms and args.times:
        return generate_instance(
            n_courses=args.courses, n_rooms=args.rooms, n_times=args.times,
            n_teachers=args.teachers, unavailable_prob=args.unavail, seed=args.seed
        )

    # Default fallback: small demo
    return small_demo_instance()


def maybe_dump_dimacs(cnf: CNF, path: Optional[str]) -> None:
    if not path:
        return
    # Write a simple DIMACS file
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(f"p cnf {cnf.num_vars} {len(cnf.clauses)}\n")
        for cl in cnf.clauses:
            f.write(" ".join(str(l) for l in cl) + " 0\n")
    print(f"[CNF] Wrote DIMACS to {path}")


def main() -> None:
    args = parse_args()

    # Build instance and encode
    inst = build_instance_from_args(args)
    cnf = encode(inst)

    # Optional export
    maybe_dump_dimacs(cnf, args.dump_cnf)

    # Solve
    use_heur = not args.no_heuristic
    stats = Stats()
    trace = Trace() if args.trace else None

    t0 = time.perf_counter()
    sat, model = dpll(cnf, trace=trace, use_heuristic=use_heur, stats=stats)
    dt = (time.perf_counter() - t0)

    # Report
    print(f"Vars={cnf.num_vars} Clauses={len(cnf.clauses)} Heuristic={'ON' if use_heur else 'OFF'}")
    if sat:
        print(f"SAT  | time={dt:.6f}s  decisions={stats.decisions}  propagations={stats.propagations}  backtracks={stats.backtracks}")
        if args.model:
            schedule = decode(inst, model)
            print("Model:")
            for (c, r, t) in schedule:
                print(f"  {c} -> {r} @ {t}")
    else:
        print(f"UNSAT | time={dt:.6f}s  decisions={stats.decisions}  propagations={stats.propagations}  backtracks={stats.backtracks}")

    # Optional trace
    if trace:
        print("Trace:")
        for ev in trace:
            if ev.var is None:
                print(f"  {ev.kind}")
            else:
                note = f" ({ev.note})" if ev.note else ""
                print(f"  {ev.kind}: var={ev.var} val={'T' if ev.val else 'F'}{note}")


if __name__ == "__main__":
    main()
