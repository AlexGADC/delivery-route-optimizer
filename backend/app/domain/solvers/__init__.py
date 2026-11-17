"""The list of available algorithms.

To add an algorithm: write it in its own file in this folder, then add it to
``_ALL_SOLVERS`` below. Everything else (the command line, later the API)
finds it through ``solver_names`` and ``get_solver``.
"""

from app.domain.solvers.base import Solver
from app.domain.solvers.brute_force import BruteForceSolver

_ALL_SOLVERS: tuple[Solver, ...] = (BruteForceSolver(),)

_BY_NAME: dict[str, Solver] = {solver.name: solver for solver in _ALL_SOLVERS}


def solver_names() -> list[str]:
    """The names of all available algorithms, in alphabetical order."""
    return sorted(_BY_NAME)


def get_solver(name: str) -> Solver:
    """Return the algorithm with this name, or explain which names exist."""
    if name not in _BY_NAME:
        raise ValueError(f"unknown algorithm '{name}'; available: {', '.join(solver_names())}")
    return _BY_NAME[name]
