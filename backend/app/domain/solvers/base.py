"""What every solver has in common: its interface and what it returns."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.evaluation import Evaluation
from app.domain.instance import Instance


@dataclass(frozen=True)
class TracePoint:
    """A moment when a solver found a better route than any before."""

    iteration: int  # how many steps the solver had taken by then
    cost: float  # the cost of the new best route


@dataclass(frozen=True)
class Solution:
    """What a solver returns."""

    algorithm: str
    tour: tuple[int, ...]  # the customers in visiting order
    evaluation: Evaluation  # the full judgement of that tour
    trace: tuple[TracePoint, ...]  # every improvement in order; drawn, it is the convergence curve


@dataclass(frozen=True)
class Progress:
    """Sent to the caller while a solver runs, each time it finds a better route."""

    iteration: int
    best_cost: float
    best_tour: tuple[int, ...]


ProgressCallback = Callable[[Progress], None]


class Solver(Protocol):
    """The shape every algorithm must have."""

    name: str

    def solve(
        self,
        instance: Instance,
        params: Mapping[str, Any] | None = None,
        on_progress: ProgressCallback | None = None,
    ) -> Solution:
        """Find a good route for ``instance``.

        ``params`` holds the algorithm's own settings, such as ``seed``.
        ``on_progress``, if given, is called on every improvement.

        A solver must not read files, use the network or keep state between
        calls, and the same instance, params and seed must give the same result.
        """
        ...
