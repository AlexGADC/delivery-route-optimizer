"""Command line: solve one instance file and print the route.

Run from the backend folder:

    uv run python -m app.cli algorithms
    uv run python -m app.cli solve ../data/instances/brasov-5.json --algorithm brute-force
"""

import argparse
import sys
import time
from dataclasses import replace

from app.domain.instance import Instance, Stop
from app.domain.solvers import get_solver, solver_names
from app.domain.solvers.base import Solution
from app.infrastructure.instance_files import load_instance


def main(argv: list[str] | None = None) -> int:
    # Stop names contain Romanian letters. Without this, printing them fails on
    # Windows when the output goes to a file or to another program.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = _parse_arguments(argv)

    if args.command == "algorithms":
        print("\n".join(solver_names()))
        return 0

    instance = load_instance(args.instance)
    if args.service_minutes is not None:
        instance = replace(instance, service_time_s=args.service_minutes * 60)
    if args.lateness_weight is not None:
        instance = replace(instance, lateness_weight=args.lateness_weight)

    started = time.perf_counter()
    solution = get_solver(args.algorithm).solve(instance, {"seed": args.seed})
    elapsed_s = time.perf_counter() - started

    print(format_report(instance, solution, elapsed_s))
    return 0


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="Delivery route optimizer")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("algorithms", help="list the available algorithms")

    solve = commands.add_parser("solve", help="solve one instance file")
    solve.add_argument("instance", help="path to an instance JSON file")
    solve.add_argument("--algorithm", required=True, choices=solver_names())
    solve.add_argument("--seed", type=int, default=0, help="seed for algorithms that use randomness")
    solve.add_argument(
        "--service-minutes",
        type=float,
        help="time spent at each customer (default: the file's value, else 5)",
    )
    solve.add_argument(
        "--lateness-weight",
        type=float,
        help="what one second of lateness costs, in seconds of driving (default: the file's value, else 10)",
    )
    return parser.parse_args(argv)


def format_report(instance: Instance, solution: Solution, elapsed_s: float) -> str:
    """Turn a solution into the text shown on screen, in minutes, kilometres and HH:MM."""
    result = solution.evaluation
    depot = instance.stops[instance.depot]
    order = [instance.depot, *solution.tour, instance.depot]

    lines = [
        f"Instance      {instance.name} ({len(instance.customers)} customers)",
        f"Algorithm     {solution.algorithm} (ran in {elapsed_s * 1000:.1f} ms)",
        f"Route         {' -> '.join(str(position) for position in order)}",
        "",
        f"{'#':>2}  {'Stop':<20} {'Window':<13} {'Arrives':<8} {'Waits':>7} {'Late':>7}",
        f"{0:>2}  {depot.name:<20} {_window(depot):<13} leaves {_clock(depot.open_s)}",
    ]
    for number, visit in enumerate(result.visits, start=1):
        stop = instance.stops[visit.stop]
        lines.append(
            f"{number:>2}  {stop.name:<20} {_window(stop):<13} {_clock(visit.arrival_s):<8} "
            f"{_minutes(visit.wait_s):>7} {_minutes(visit.lateness_s):>7}"
        )
    lines.append(f"{'':>2}  {depot.name:<20} {'':<13} {_clock(result.return_s)}")

    lines += [
        "",
        f"Driving time  {result.travel_time_s / 60:.1f} min",
        f"Distance      {result.distance_m / 1000:.2f} km",
        f"Waiting       {result.waiting_s / 60:.1f} min",
        f"Late stops    {result.late_stops} of {len(result.visits)}",
        f"Lateness      {result.lateness_s / 60:.1f} min",
        f"Cost          {result.cost:.1f}",
    ]
    return "\n".join(lines)


def _clock(seconds: float) -> str:
    """Seconds since midnight as HH:MM, for example 29191.5 -> "08:06"."""
    minutes = int(seconds) // 60
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _window(stop: Stop) -> str:
    return f"{_clock(stop.open_s)}-{_clock(stop.close_s)}"


def _minutes(seconds: float) -> str:
    """A duration in whole minutes, or a dash when there is none."""
    return f"{seconds / 60:.0f} min" if seconds > 0 else "-"


if __name__ == "__main__":
    raise SystemExit(main())
