from solver.cnf import CNF
from solver.dpll import dpll, Trace

def test_unsat_trace_nonempty():
    cnf = CNF(1, [[1], [-1]])
    tr = Trace()
    sat, _ = dpll(cnf, trace=tr)
    assert not sat
    assert any(e.kind == "conflict" for e in tr)
