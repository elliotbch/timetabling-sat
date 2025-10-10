from solver.cnf import CNF
from solver.dpll import dpll

def test_unit_clause():
    # (x1)
    cnf = CNF(1, [[1]])
    sat, model = dpll(cnf)
    assert sat and model[1] is True

def test_simple_sat():
    # (x1) & (x1 v ¬x2) & (x2 v x3)
    cnf = CNF(3, [[1], [1, -2], [2, 3]])
    sat, _ = dpll(cnf)
    assert sat

def test_unsat_contradiction():
    # (x1) & (¬x1)
    cnf = CNF(1, [[1], [-1]])
    sat, _ = dpll(cnf)
    assert not sat
