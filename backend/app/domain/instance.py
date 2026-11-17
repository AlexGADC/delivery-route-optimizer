"""The problem to solve: the stops, their time windows and the driving times between them.

Everything here is plain data in the backend's standard units: seconds for
durations, metres for distances, seconds since midnight for times of day.
"""

from dataclasses import dataclass

# A square table of numbers: matrix[i][j] is the value FROM stop i TO stop j.
Matrix = tuple[tuple[float, ...], ...]

# The two numbers of the problem definition that are a matter of choice.
DEFAULT_SERVICE_TIME_S = 300.0  # time spent at each customer: 5 minutes
DEFAULT_LATENESS_WEIGHT = 10.0  # one second of lateness costs like 10 seconds of driving


@dataclass(frozen=True)
class Stop:
    """A place the courier visits: the depot or a customer."""

    name: str
    lat: float
    lon: float
    open_s: int  # the time window opens (seconds since midnight)
    close_s: int  # the time window closes; arriving after this is late


@dataclass(frozen=True)
class Instance:
    """One complete problem: where to go, when each stop accepts a visit, and how a route is judged.

    A stop is identified by its position in ``stops``, and the matrices use the
    same positions. ``durations_s[i][j]`` is the driving time from stop ``i`` to
    stop ``j``. The matrices are not symmetric: one-way streets make the two
    directions differ.
    """

    name: str
    stops: tuple[Stop, ...]
    durations_s: Matrix
    distances_m: Matrix
    depot: int = 0
    service_time_s: float = DEFAULT_SERVICE_TIME_S
    lateness_weight: float = DEFAULT_LATENESS_WEIGHT

    def __post_init__(self) -> None:
        """Refuse data that would make every later calculation silently wrong."""
        count = len(self.stops)
        if count == 0:
            raise ValueError("an instance needs at least one stop, the depot")
        if not 0 <= self.depot < count:
            raise ValueError(f"depot must be a position between 0 and {count - 1}, got {self.depot}")

        for label, matrix in (("durations_s", self.durations_s), ("distances_m", self.distances_m)):
            if len(matrix) != count or any(len(row) != count for row in matrix):
                raise ValueError(f"{label} must have one row and one column per stop ({count}x{count})")
            if any(value < 0 for row in matrix for value in row):
                raise ValueError(f"{label} cannot contain negative values")

        for stop in self.stops:
            if stop.open_s > stop.close_s:
                raise ValueError(f"the time window of '{stop.name}' closes before it opens")

        if self.service_time_s < 0 or self.lateness_weight < 0:
            raise ValueError("service_time_s and lateness_weight cannot be negative")

    @property
    def customers(self) -> tuple[int, ...]:
        """Positions of every stop except the depot: the stops a route must visit."""
        return tuple(position for position in range(len(self.stops)) if position != self.depot)
