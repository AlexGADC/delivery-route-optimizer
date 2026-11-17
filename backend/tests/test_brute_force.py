from itertools import permutations

import pytest

from app.domain.evaluation import evaluate
from app.domain.instance import Instance, Stop
from app.domain.solvers import get_solver, solver_names
from app.domain.solvers.brute_force import MAX_CUSTOMERS, BruteForceSolver


def test_is_available_by_name():
    assert "brute-force" in solver_names()
    assert isinstance(get_solver("brute-force"), BruteForceSolver)


def test_an_unknown_name_lists_the_available_algorithms():
    with pytest.raises(ValueError, match="available: .*brute-force"):
        get_solver("magic")


def test_picks_the_cheaper_order_on_the_tiny_instance(tiny):
    # The two possible orders cost 2470 (A then B) and 890 (B then A); see test_evaluation.py.
    solution = BruteForceSolver().solve(tiny)

    assert solution.algorithm == "brute-force"
    assert solution.tour == (2, 1)
    assert solution.evaluation.cost == 890


def test_no_order_is_cheaper_on_the_brasov_instance(brasov5):
    solution = BruteForceSolver().solve(brasov5)

    # Visits every customer exactly once.
    assert sorted(solution.tour) == [1, 2, 3, 4]
    # The reported evaluation really belongs to the reported tour.
    assert solution.evaluation == evaluate(brasov5, solution.tour)
    # Nothing beats it.
    cheapest = min(evaluate(brasov5, order).cost for order in permutations(brasov5.customers))
    assert solution.evaluation.cost == cheapest


def test_the_same_input_gives_the_same_solution(brasov5):
    assert BruteForceSolver().solve(brasov5) == BruteForceSolver().solve(brasov5)


def test_trace_and_progress_report_every_improvement(tiny):
    reports = []

    solution = BruteForceSolver().solve(tiny, on_progress=reports.append)

    # Orders are tried as (A, B) then (B, A): first 2470, then the better 890.
    assert [(point.iteration, point.cost) for point in solution.trace] == [(1, 2470), (2, 890)]
    assert [(r.iteration, r.best_cost, r.best_tour) for r in reports] == [(1, 2470, (1, 2)), (2, 890, (2, 1))]


def test_refuses_an_instance_that_is_too_large():
    count = MAX_CUSTOMERS + 2  # the depot plus one customer too many
    zeros = tuple(tuple(0 for _ in range(count)) for _ in range(count))
    stops = tuple(Stop(f"stop {number}", 0.0, 0.0, open_s=0, close_s=100) for number in range(count))
    instance = Instance(name="large", stops=stops, durations_s=zeros, distances_m=zeros)

    with pytest.raises(ValueError, match="at most"):
        BruteForceSolver().solve(instance)
