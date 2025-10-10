from solver.cnf import CNF, formula_satisfied
from solver.dpll import dpll

def test_model_satisfies_when_sat():
    cnf = CNF(3, [[1], [1, -2], [2, 3]])
    sat, model = dpll(cnf)
    assert sat
    assert formula_satisfied(cnf, model)

def test_model_checker_unsat_returns_false_if_forced():
    cnf = CNF(1, [[1], [-1]])
    sat, _ = dpll(cnf)
    assert not sat
    fake_model = {1: True}
    assert not formula_satisfied(cnf, fake_model)
