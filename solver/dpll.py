"""
--------------------------------------------------------
 DPLL SAT Solver — Elliot Bouchy
--------------------------------------------------------
A minimalist implementation of the DPLL (Davis–Putnam–
Logemann–Loveland) algorithm for SAT solving.

Features:
 - Unit propagation
 - Pure literal elimination
 - Basic backtracking
 - Simple DLIS-lite variable selection heuristic
 - Optional tracing and statistics

--------------------------------------------------------
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

# ---------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------
Assignment = Dict[int, bool]   # variable ID → Boolean value

# ---------------------------------------------------------------------
# Data structures for tracing and statistics
# ---------------------------------------------------------------------

@dataclass
class Event:
    """
    Represents a single event during solving, useful for
    producing an execution trace (e.g., for UNSAT explanations).
    """
    kind: str           # "decide", "unit", "pure", "conflict", "backtrack", "sat"
    var: int | None = None
    val: bool | None = None
    note: str = ""      # optional explanation


class Trace(List[Event]):
    """Simple list subclass to store chronological events."""
    pass


@dataclass
class Stats:
    """Counters for runtime statistics."""
    decisions: int = 0
    propagations: int = 0
    backtracks: int = 0


# ---------------------------------------------------------------------
# Unit propagation
# ---------------------------------------------------------------------
def _unit_propagate(
    clauses: List[Clause], assign: Assignment, 
    trace: Optional[Trace], stats: Optional[Stats]
) -> Tuple[Optional[List[Clause]], bool]:
    """
    Simplify the formula by repeatedly applying unit clauses.
    - If a clause becomes empty ⇒ conflict.
    - Otherwise, assign forced literals and simplify clauses.
    Returns: (simplified_clauses, conflict_occurred)
    """
    changed = True
    while changed:
        changed = False
        # Find all current unit clauses (one literal only)
        units = [cl[0] for cl in clauses if len(cl) == 1]
        if not units:
            break

        for u in units:
            var, val = abs(u), (u > 0)

            # If variable already assigned inconsistently ⇒ conflict
            if var in assign:
                if assign[var] != val:
                    if trace is not None:
                        trace.append(Event("conflict", var=var, val=val, note="unit contradicts previous"))
                    return None, True
                continue

            # Assign the literal
            assign[var] = val
            if stats: stats.propagations += 1
            if trace: trace.append(Event("unit", var=var, val=val))
            changed = True

            # Simplify clauses based on this assignment
            new_clauses: List[Clause] = []
            for cl in clauses:
                if u in cl:           # clause satisfied
                    continue
                if -u in cl:          # remove falsified literal
                    new = [l for l in cl if l != -u]
                    if not new:       # empty clause ⇒ conflict
                        if trace:
                            trace.append(Event("conflict", var=var, val=val, note="empty clause after unit"))
                        return None, True
                    new_clauses.append(new)
                else:
                    new_clauses.append(cl)
            clauses = new_clauses
    return clauses, False


# ---------------------------------------------------------------------
# Pure literal elimination
# ---------------------------------------------------------------------
def _pure_literal_elimination(
    clauses: List[Clause], assign: Assignment,
    trace: Optional[Trace], stats: Optional[Stats]
) -> Tuple[List[Clause], bool]:
    """
    Simplify the formula by assigning pure literals (variables
    that appear only with one polarity).
    """
    if not clauses:
        return clauses, False

    # Compute polarity of each literal
    polarity: Dict[int, int] = {}
    for cl in clauses:
        for l in cl:
            v = abs(l)
            pol = 1 if l > 0 else -1
            if v not in polarity:
                polarity[v] = pol
            elif polarity[v] != pol:
                polarity[v] = 0  # variable appears both positive and negative

    # Collect all pure literals
    pures = [(v, polarity[v] == 1) for v in polarity if polarity[v] in (1, -1) and v not in assign]
    if not pures:
        return clauses, False

    satisfied = set()
    for v, val in pures:
        assign[v] = val
        satisfied.add(v if val else -v)
        if stats: stats.propagations += 1
        if trace: trace.append(Event("pure", var=v, val=val))

    # Remove all clauses satisfied by pure literals
    new_clauses: List[Clause] = [cl for cl in clauses if not any(l in satisfied for l in cl)]
    return new_clauses, True


# ---------------------------------------------------------------------
# Variable selection heuristic: DLIS-lite
# ---------------------------------------------------------------------
def _dlis_lite_choice(clauses: List[Clause], assign: Assignment) -> Tuple[int, bool]:
    """
    Count the number of positive/negative occurrences of each
    unassigned variable and pick the most frequent literal.
    This mimics a simplified version of the DLIS heuristic.
    """
    pos_count: Dict[int, int] = {}
    neg_count: Dict[int, int] = {}

    # Count literal occurrences
    for cl in clauses:
        for l in cl:
            v = abs(l)
            if v in assign:
                continue
            if l > 0:
                pos_count[v] = pos_count.get(v, 0) + 1
            else:
                neg_count[v] = neg_count.get(v, 0) + 1

    if not pos_count and not neg_count:
        return 0, True  # all assigned

    best_v, best_pol_true, best_score = 0, True, -1
    keys = set(pos_count) | set(neg_count)
    for v in keys:
        pc, nc = pos_count.get(v, 0), neg_count.get(v, 0)
        # choose polarity with highest count
        if pc >= nc and pc > best_score:
            best_v, best_pol_true, best_score = v, True, pc
        elif nc > best_score:
            best_v, best_pol_true, best_score = v, False, nc

    return best_v, best_pol_true


def _choose_unassigned(clauses: List[Clause], assign: Assignment, use_heuristic: bool) -> Tuple[int, bool]:
    """
    Choose the next variable to assign.
    If heuristic enabled → use DLIS-lite.
    Otherwise → pick the first unassigned variable found.
    """
    if use_heuristic:
        v, pol = _dlis_lite_choice(clauses, assign)
        if v != 0:
            return v, pol

    # Fallback: first unassigned variable
    for cl in clauses:
        for l in cl:
            v = abs(l)
            if v not in assign:
                return v, True
    return 0, True


# ---------------------------------------------------------------------
# Main DPLL recursive solver
# ---------------------------------------------------------------------
def dpll(
    cnf: CNF, trace: Optional[Trace] = None, use_heuristic: bool = True,
    stats: Optional[Stats] = None
) -> Tuple[bool, Assignment]:
    """
    Entry point for the DPLL solver.
    Copies the CNF clauses and launches recursive search.
    Returns (is_satisfiable, model)
    """
    clauses = [cl[:] for cl in cnf.clauses]
    assign: Assignment = {}
    if stats is None:
        stats = Stats()
    sat, model = _dpll_rec(clauses, assign, trace, use_heuristic, stats)
    return sat, model


def _dpll_rec(
    clauses: List[Clause], assign: Assignment, trace: Optional[Trace],
    use_heuristic: bool, stats: Stats
) -> Tuple[bool, Assignment]:
    """
    Recursive DPLL procedure with:
      - Unit propagation
      - Pure literal elimination
      - Decision and backtracking
    """
    while True:
        # Step 1: unit propagation
        clauses, conflict = _unit_propagate(clauses, assign, trace, stats)
        if conflict or clauses is None:
            return False, {}

        # Step 2: if no clauses left → formula satisfied
        if not clauses:
            if trace: trace.append(Event("sat"))
            return True, assign.copy()

        # Step 3: pure literal elimination
        clauses, changed = _pure_literal_elimination(clauses, assign, trace, stats)
        if not changed:
            break  # no more simplification possible

    # Step 4: pick a variable to branch on
    v, preferred = _choose_unassigned(clauses, assign, use_heuristic)
    if v == 0:
        if trace: trace.append(Event("sat"))
        return True, assign.copy()

    # Step 5: try the preferred polarity first, then its negation
    for val in (preferred, not preferred):
        assign[v] = val
        if stats: stats.decisions += 1
        if trace: trace.append(Event("decide", var=v, val=val))

        pos = v if val else -v
        neg = -pos

        # Simplify clauses under this decision
        new_clauses: List[Clause] = []
        bad = False
        for cl in clauses:
            if pos in cl:
                continue  # satisfied clause
            if neg in cl:
                new = [l for l in cl if l != neg]
                if not new:
                    bad = True
                    if trace:
                        trace.append(Event("conflict", var=v, val=val, note="empty clause after decide"))
                    break
                new_clauses.append(new)
            else:
                new_clauses.append(cl)

        # Recurse with the simplified formula
        if not bad:
            sat, model = _dpll_rec(new_clauses, assign, trace, use_heuristic, stats)
            if sat:
                return True, model

        # If this branch failed → backtrack
        if stats: stats.backtracks += 1
        if trace: trace.append(Event("backtrack", var=v, val=val))
        del assign[v]

    # Both polarities failed → UNSAT
    return False, {}
