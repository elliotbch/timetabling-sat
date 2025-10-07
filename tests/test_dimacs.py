from solver.cnf import parse_dimacs

def test_parse_and_emit_roundtrip():
    text = """
    c example
    p cnf 3 2
    1 -2 0
    -3 0
    """
    cnf = parse_dimacs(text)
    assert cnf.num_vars == 3
    assert len(cnf.clauses) == 2
    dim = cnf.to_dimacs()
    cnf2 = parse_dimacs(dim)
    assert cnf2.num_vars == cnf.num_vars
    assert cnf2.clauses == cnf.clauses