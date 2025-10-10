from solver.cnf import CNF
from solver.dpll import dpll, _dlis_lite_choice

def test_dlis_choice_prefers_positive_when_more_positive():
    clauses = [[1, 1, -2], [1], [3, -2]]
    assign = {}
    v, pol = _dlis_lite_choice(clauses, assign)
    assert v == 1 and pol is True

def test_dlis_choice_prefers_negative_when_more_negative():
    clauses = [[-2, -2, 1], [-2], [3, 1]]
    assign = {}
    v, pol = _dlis_lite_choice(clauses, assign)
    assert v == 2 and pol is False

def test_dpll_with_heuristic_still_solves():
    cnf = CNF(3, [[1], [1, -2], [2, 3]])
    sat, model = dpll(cnf, use_heuristic=True)
    assert sat and model
