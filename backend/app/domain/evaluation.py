"""Judging a route.

``evaluate`` is the single source of truth for what a route costs. Every solver
calls it, and nothing else in the project computes travel time or lateness.

The rules it applies are the problem definition:

* The courier leaves the depot when it opens, visits the customers in the
  given order and drives back to the depot.
* Arriving before a window opens means waiting until it opens.
* Arriving after a window closes is allowed, but counts as late (a soft window).
* Service takes the same fixed time at every customer.
* Cost = total driving time + lateness_weight x total lateness.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.instance import Instance


@dataclass(frozen=True)
class Visit:
    """What happens at one customer. Times are seconds since midnight."""

    stop: int  # position of the stop in the instance
    arrival_s: float  # when the courier gets there
    wait_s: float  # time spent waiting for the window to open
    start_s: float  # when service starts
    lateness_s: float  # how long after the window closed the courier arrived (0 if on time)


@dataclass(frozen=True)
class Evaluation:
    """Everything known about one route."""

    visits: tuple[Visit, ...]  # one entry per customer, in visiting order
    return_s: float  # when the courier is back at the depot
    travel_time_s: float  # total driving time, including the way back
    distance_m: float  # total driving distance, including the way back
    waiting_s: float  # total time spent waiting for windows to open
    lateness_s: float  # total lateness, including a late return to the depot
    late_stops: int  # number of customers reached after their window closed
    cost: float  # the number solvers minimise


def evaluate(instance: Instance, tour: Sequence[int]) -> Evaluation:
    """Follow ``tour`` stop by stop and report what it costs.

    ``tour`` lists the customers in visiting order, as positions in
    ``instance.stops``. The depot is not part of it: every route starts and
    ends there.
    """
    check_tour(instance, tour)

    depot = instance.stops[instance.depot]
    clock = float(depot.open_s)  # the current time; the courier leaves when the depot opens
    position = instance.depot  # where the courier is now

    travel_time = 0.0
    distance = 0.0
    waiting = 0.0
    lateness = 0.0
    late_stops = 0
    visits = []

    for stop_position in tour:
        stop = instance.stops[stop_position]

        # 1. Drive from the current position to the stop.
        driving = instance.durations_s[position][stop_position]
        travel_time += driving
        distance += instance.distances_m[position][stop_position]
        arrival = clock + driving

        # 2. Too early: wait until the window opens.
        wait = max(0.0, stop.open_s - arrival)
        start = arrival + wait
        waiting += wait

        # 3. Too late: the visit still happens, but the delay is recorded.
        late = max(0.0, arrival - stop.close_s)
        lateness += late
        if late > 0:
            late_stops += 1

        visits.append(Visit(stop=stop_position, arrival_s=arrival, wait_s=wait, start_s=start, lateness_s=late))

        # 4. Serve the customer, then continue from here.
        clock = start + instance.service_time_s
        position = stop_position

    # Drive back to the depot. Returning after it closes is late as well.
    driving = instance.durations_s[position][instance.depot]
    travel_time += driving
    distance += instance.distances_m[position][instance.depot]
    return_time = clock + driving
    lateness += max(0.0, return_time - depot.close_s)

    return Evaluation(
        visits=tuple(visits),
        return_s=return_time,
        travel_time_s=travel_time,
        distance_m=distance,
        waiting_s=waiting,
        lateness_s=lateness,
        late_stops=late_stops,
        cost=travel_time + instance.lateness_weight * lateness,
    )


def check_tour(instance: Instance, tour: Sequence[int]) -> None:
    """Raise ``ValueError`` unless ``tour`` visits every customer exactly once."""
    if sorted(tour) != list(instance.customers):
        raise ValueError(
            "a tour must visit every customer exactly once and leave out the depot; "
            f"expected a reordering of {list(instance.customers)}, got {list(tour)}"
        )
