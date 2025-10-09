
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Iterable

Literal = int   
Clause  = List[int]

@dataclass
class CNF:
    num_vars: int
    clauses: List[Clause] = field(default_factory=list)

    def add_clause(self, clause: Iterable[int]) -> None:
        cl = [int(l) for l in clause if int(l) != 0]
        assert all(abs(l) >= 1 for l in cl), "Literals must be nonzero ints"
        self.clauses.append(cl)
        if cl:
            self.num_vars = max(self.num_vars, *(abs(l) for l in cl))

    def to_dimacs(self) -> str:
        lines = [f"p cnf {self.num_vars} {len(self.clauses)}"]
        for cl in self.clauses:
            lines.append(" ".join(str(l) for l in cl) + " 0")
        return "\n".join(lines) + "\n"

def parse_dimacs(text: str) -> CNF:
    num_vars = 0
    clauses: List[Clause] = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith('c'):
            continue
        if s.startswith('p'):
            parts = s.split()
            assert parts[1] == 'cnf', "Only CNF supported"
            num_vars = int(parts[2])
            continue
        lits = [int(x) for x in s.split() if x != '0']
        if lits:
            clauses.append(lits)
            for l in lits:
                num_vars = max(num_vars, abs(l))
    return CNF(num_vars=num_vars, clauses=clauses)

def parse_dimacs_file(path: str) -> CNF:
    with open(path, "r", encoding="utf-8") as f:
        return parse_dimacs(f.read())
