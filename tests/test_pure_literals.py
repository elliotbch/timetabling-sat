from solver.cnf import CNF
from solver.dpll import dpll

def test_pure_literals_all_positive():
    # (x1 v x2) & (x1 v x3) & (x2 v x3)
    cnf = CNF(3, [[1, 2], [1, 3], [2, 3]])
    sat, model = dpll(cnf)
    assert sat
    assert any(model.get(v, False) for v in (1,2,3))

def test_pure_literal_negative():
    # (x1 v ¬x3) & (x2 v ¬x3)
    cnf = CNF(3, [[1, -3], [2, -3]])
    sat, model = dpll(cnf)
    assert sat
    assert model.get(3) is False
