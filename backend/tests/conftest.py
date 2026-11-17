"""Shared test data. Nothing here needs Docker or the network."""

from pathlib import Path

import pytest

from app.domain.instance import Instance, Stop
from app.infrastructure.instance_files import load_instance

INSTANCES_DIR = Path(__file__).resolve().parents[2] / "data" / "instances"


@pytest.fixture
def brasov5_path() -> Path:
    return INSTANCES_DIR / "brasov-5.json"


@pytest.fixture
def brasov5(brasov5_path) -> Instance:
    """The depot and four customers in Brașov, with real driving times from OSRM."""
    return load_instance(brasov5_path)


@pytest.fixture
def tiny() -> Instance:
    """A depot and two customers, with numbers small enough to check by hand.

    Driving times in seconds (row = from, column = to):

                depot     A     B
        depot       0   100   200
        A         120     0    50
        B         220    70     0

    Windows: depot 0-3600, A 300-400, B 0-150.
    Service takes 10 seconds. One second of lateness costs 10.
    Distances are simply ten times the driving times.
    """
    durations = ((0, 100, 200), (120, 0, 50), (220, 70, 0))
    return Instance(
        name="tiny",
        stops=(
            Stop("depot", 0.0, 0.0, open_s=0, close_s=3600),
            Stop("A", 0.0, 0.0, open_s=300, close_s=400),
            Stop("B", 0.0, 0.0, open_s=0, close_s=150),
        ),
        durations_s=durations,
        distances_m=tuple(tuple(value * 10 for value in row) for row in durations),
        service_time_s=10,
        lateness_weight=10,
    )
