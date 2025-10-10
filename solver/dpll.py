from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from .cnf import CNF, Clause, Literal

Assignment = Dict[int, bool]

@dataclass
class Event:
    kind: str           # "decide", "unit", "pure", "conflict", "backtrack", "sat"
    var: int | None = None
    val: bool | None = None
    note: str = ""

class Trace(List[Event]):
    pass

def _unit_propagate(clauses: List[Clause], assign: Assignment, trace: Optional[Trace]) -> Tuple[Optional[List[Clause]], bool]:
    changed = True
    while changed:
        changed = False
        units = [cl[0] for cl in clauses if len(cl) == 1]
        if not units:
            break
        for u in units:
            var, val = abs(u), (u > 0)
            if var in assign:
                if assign[var] != val:
                    if trace is not None:
                        trace.append(Event("conflict", var=var, val=val, note="unit contradicts previous"))
                    return None, True
                continue
            assign[var] = val
            if trace is not None:
                trace.append(Event("unit", var=var, val=val))
            changed = True
            new_clauses: List[Clause] = []
            for cl in clauses:
                if u in cl:
                    continue
                if -u in cl:
                    new = [l for l in cl if l != -u]
                    if not new:
                        if trace is not None:
                            trace.append(Event("conflict", var=var, val=val, note="empty clause after unit"))
                        return None, True
                    new_clauses.append(new)
                else:
                    new_clauses.append(cl)
            clauses = new_clauses
    return clauses, False

def _pure_literal_elimination(clauses: List[Clause], assign: Assignment, trace: Optional[Trace]) -> Tuple[List[Clause], bool]:
    if not clauses:
        return clauses, False
    polarity = {}
    for cl in clauses:
        for l in cl:
            v = abs(l)
            pol = 1 if l > 0 else -1
            if v not in polarity:
                polarity[v] = pol
            elif polarity[v] != pol:
                polarity[v] = 0
    pures = [(v, polarity[v] == 1) for v in polarity if polarity[v] in (1, -1) and v not in assign]
    if not pures:
        return clauses, False
    satisfied = set()
    for v, val in pures:
        assign[v] = val
        satisfied.add(v if val else -v)
        if trace is not None:
            trace.append(Event("pure", var=v, val=val))
    new_clauses: List[Clause] = []
    for cl in clauses:
        if any(l in satisfied for l in cl):
            continue
        new_clauses.append(cl)
    return new_clauses, True

# ---------- (OPTIONNEL) Heuristique DLIS-lite ----------
def _dlis_lite_choice(clauses: List[Clause], assign: Assignment) -> Tuple[int, bool]:
    
    pos_count: Dict[int, int] = {}
    neg_count: Dict[int, int] = {}
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
        return 0, True
    # score = max(polarity count)
    best_v = 0
    best_pol_true = True
    best_score = -1
    keys = set(pos_count) | set(neg_count)
    for v in keys:
        pc = pos_count.get(v, 0)
        nc = neg_count.get(v, 0)
        if pc >= nc:
            if pc > best_score:
                best_score, best_v, best_pol_true = pc, v, True
        else:
            if nc > best_score:
                best_score, best_v, best_pol_true = nc, v, False
    return best_v, best_pol_true

def _choose_unassigned(clauses: List[Clause], assign: Assignment, use_heuristic: bool) -> Tuple[int, bool]:
    if use_heuristic:
        v, pol = _dlis_lite_choice(clauses, assign)
        if v != 0:
            return v, pol

    for cl in clauses:
        for l in cl:
            v = abs(l)
            if v not in assign:
                return v, True
    return 0, True
# ------------------------------------------------------

def dpll(cnf: CNF, trace: Optional[Trace] = None, use_heuristic: bool = True) -> Tuple[bool, Assignment]:
    clauses = [cl[:] for cl in cnf.clauses]
    assign: Assignment = {}
    sat, model = _dpll_rec(clauses, assign, trace, use_heuristic)
    return sat, model

def _dpll_rec(clauses: List[Clause], assign: Assignment, trace: Optional[Trace], use_heuristic: bool) -> Tuple[bool, Assignment]:
    while True:
        clauses, conflict = _unit_propagate(clauses, assign, trace)
        if conflict:
            return False, {}
        if clauses is None:
            return False, {}
        if not clauses:
            if trace is not None:
                trace.append(Event("sat"))
            return True, assign.copy()
        clauses, changed = _pure_literal_elimination(clauses, assign, trace)
        if not changed:
            break
    v, preferred = _choose_unassigned(clauses, assign, use_heuristic)
    if v == 0:
        if trace is not None:
            trace.append(Event("sat"))
        return True, assign.copy()
    
    for val in (preferred, not preferred):
        assign[v] = val
        if trace is not None:
            trace.append(Event("decide", var=v, val=val))
        pos = v if val else -v
        neg = -pos
        new_clauses: List[Clause] = []
        bad = False
        for cl in clauses:
            if pos in cl:
                continue
            if neg in cl:
                new = [l for l in cl if l != neg]
                if not new:
                    bad = True
                    if trace is not None:
                        trace.append(Event("conflict", var=v, val=val, note="empty clause after decide"))
                    break
                new_clauses.append(new)
            else:
                new_clauses.append(cl)
        if not bad:
            sat, model = _dpll_rec(new_clauses, assign, trace, use_heuristic)
            if sat:
                return True, model
        if trace is not None:
            trace.append(Event("backtrack", var=v, val=val))
        del assign[v]
    return False, {}
