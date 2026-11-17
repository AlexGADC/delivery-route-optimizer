"""Brute force: try every possible order and keep the cheapest.

It always finds the best route, which makes it the reference that the other
algorithms are checked against. The number of orders is n! for n customers
(9 customers already give 362,880), so it only works for very small instances.
"""

from collections.abc import Mapping
from itertools import permutations
from typing import Any

from app.domain.evaluation import evaluate
from app.domain.instance import Instance
from app.domain.solvers.base import Progress, ProgressCallback, Solution, TracePoint

MAX_CUSTOMERS = 9


class BruteForceSolver:
    name = "brute-force"

    def solve(
        self,
        instance: Instance,
        params: Mapping[str, Any] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Solution:
        customers = instance.customers
        if len(customers) > MAX_CUSTOMERS:
            raise ValueError(
                f"brute force handles at most {MAX_CUSTOMERS} customers, "
                f"and this instance has {len(customers)}"
            )

        best_tour = None
        best = None
        trace = []

        # permutations() yields every possible order of the customers, one at a time.
        for iteration, tour in enumerate(permutations(customers), start=1):
            candidate = evaluate(instance, tour)

            if best is None or candidate.cost < best.cost:
                best_tour = tour
                best = candidate
                trace.append(TracePoint(iteration, candidate.cost))
                if on_progress is not None:
                    on_progress(Progress(iteration, candidate.cost, tour))

        return Solution(algorithm=self.name, tour=best_tour, evaluation=best, trace=tuple(trace))
