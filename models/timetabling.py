from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import random

from solver.cnf import CNF
from solver.dpll import dpll

# --- Types ---
Course = str
Room = str
Time = str
Teacher = str

@dataclass
class Instance:
    courses: List[Course]
    rooms: List[Room]
    times: List[Time]
    teacher_of: Dict[Course, Teacher]
    teacher_available: Dict[Teacher, List[Time]]  # allowed times per teacher

# --- Variable mapping ---
# x[c,r,t] is True  <=> course c is scheduled in room r at time t
# Encode (c,r,t) -> integer variable id in [1..N]
def var_index(inst: Instance, c: Course, r: Room, t: Time) -> int:
    ci = inst.courses.index(c)
    ri = inst.rooms.index(r)
    ti = inst.times.index(t)
    nR = len(inst.rooms)
    nT = len(inst.times)
    return 1 + ci * (nR * nT) + ri * nT + ti

# --- Encoder ---
def encode(inst: Instance) -> CNF:
    """
    Build a CNF with constraints:
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
        allowed = set(inst.teacher_available.get(teacher, T))
        for t in T:
            if t not in allowed:
                for r in R:
                    cnf.add_clause([-var_index(inst, c, r, t)])

    return cnf

# --- Decoder ---
def decode(inst: Instance, model: Dict[int, bool]) -> List[Tuple[Course, Room, Time]]:
    out: List[Tuple[Course, Room, Time]] = []
    for c in inst.courses:
        for r in inst.rooms:
            for t in inst.times:
                v = var_index(inst, c, r, t)
                if model.get(v) is True:
                    out.append((c, r, t))
    return out

# --- Small demo instance ---
def small_demo_instance() -> Instance:
    courses = ["C1", "C2"]
    rooms = ["R1", "R2"]
    times = ["T1", "T2", "T3"]
    teacher_of = {"C1": "A", "C2": "A"}  # same teacher to force time separation
    teacher_available = {"A": ["T1", "T2", "T3"]}
    return Instance(courses, rooms, times, teacher_of, teacher_available)

def demo_and_solve() -> None:
    inst = small_demo_instance()
    cnf = encode(inst)
    sat, model = dpll(cnf)
    if not sat:
        print("UNSAT")
        return
    print("SAT")
    schedule = decode(inst, model)
    for (c, r, t) in schedule:
        print(f"{c} -> {r} @ {t}")

# --- Generator for S/M/L ---
def generate_instance(n_courses: int, n_rooms: int, n_times: int,
                      n_teachers: int = 2,
                      unavailable_prob: float = 0.0,
                      seed: Optional[int] = 0) -> Instance:
    """
    Create a pseudo-random instance.
    Each teacher has each timeslot available independently with prob (1 - unavailable_prob),
    but we ensure at least one slot remains available.
    """
    rnd = random.Random(seed)
    courses: List[str] = [f"C{i+1}" for i in range(n_courses)]
    rooms: List[str]   = [f"R{j+1}" for j in range(n_rooms)]
    times: List[str]   = [f"T{k+1}" for k in range(n_times)]
    teachers: List[str]= [f"P{p+1}" for p in range(n_teachers)]

    teacher_of: Dict[str, str] = {c: rnd.choice(teachers) for c in courses}

    teacher_available: Dict[str, List[str]] = {}
    for t in teachers:
        allowed: List[str] = [tt for tt in times if rnd.random() > unavailable_prob]
        if not allowed:
            allowed = [rnd.choice(times)]
        teacher_available[t] = allowed

    return Instance(courses, rooms, times, teacher_of, teacher_available)
