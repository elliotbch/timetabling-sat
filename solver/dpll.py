from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from .cnf import CNF, Clause, Literal

Assignment = Dict[int, bool] 


def _unit_propagate(clauses: List[Clause], assign: Assignment) -> Tuple[Optional[List[Clause]], bool]:
    
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
                    return None, True
                continue
           
            assign[var] = val
            changed = True
            new_clauses: List[Clause] = []
            for cl in clauses:
                if u in cl:
                    continue  
                if -u in cl:
                    new = [l for l in cl if l != -u]
                    if not new:
                        return None, True  
                    new_clauses.append(new)
                else:
                    new_clauses.append(cl)
            clauses = new_clauses
    return clauses, False


def _choose_unassigned(clauses: List[Clause], assign: Assignment) -> int:

    for cl in clauses:
        for l in cl:
            v = abs(l)
            if v not in assign:
                return v
    return 0 


def dpll(cnf: CNF) -> Tuple[bool, Assignment]:
    clauses = [cl[:] for cl in cnf.clauses]
    assign: Assignment = {}
    sat, model = _dpll_rec(clauses, assign)
    return sat, model


def _dpll_rec(clauses: List[Clause], assign: Assignment) -> Tuple[bool, Assignment]:

    clauses, conflict = _unit_propagate(clauses, assign)
    if conflict:
        return False, {}
    if clauses is None:
        return False, {}
    if not clauses: 
        return True, assign.copy()


    v = _choose_unassigned(clauses, assign)
    if v == 0:
        return True, assign.copy()

    for val in (True, False):
        assign[v] = val
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
                    break
                new_clauses.append(new)
            else:
                new_clauses.append(cl)
        if not bad:
            sat, model = _dpll_rec(new_clauses, assign)
            if sat:
                return True, model
        del assign[v]

    return False, {}
