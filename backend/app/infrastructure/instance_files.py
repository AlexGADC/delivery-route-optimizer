"""Reading problem instances from JSON files.

The file format is the one of ``data/instances/brasov-5.json``. Files use
readable values ("09:30"); this module converts them to the backend's units.
"""

import json
from pathlib import Path

from app.domain.instance import (
    DEFAULT_LATENESS_WEIGHT,
    DEFAULT_SERVICE_TIME_S,
    Instance,
    Matrix,
    Stop,
)


def load_instance(path: str | Path) -> Instance:
    """Read one instance file and return it as an ``Instance``."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    stops = tuple(
        Stop(
            name=entry["name"],
            lat=entry["lat"],
            lon=entry["lon"],
            open_s=parse_clock(entry["open"]),
            close_s=parse_clock(entry["close"]),
        )
        for entry in data["stops"]
    )

    depots = [position for position, entry in enumerate(data["stops"]) if entry.get("depot")]
    if len(depots) != 1:
        raise ValueError(f"{path}: exactly one stop must be marked as the depot, found {len(depots)}")

    return Instance(
        name=data["name"],
        stops=stops,
        durations_s=_matrix(data["durations_s"]),
        distances_m=_matrix(data["distances_m"]),
        depot=depots[0],
        service_time_s=data.get("service_time_s", DEFAULT_SERVICE_TIME_S),
        lateness_weight=data.get("lateness_weight", DEFAULT_LATENESS_WEIGHT),
    )


def parse_clock(text: str) -> int:
    """Turn a time of day such as "09:30" into seconds since midnight (34200)."""
    hours, minutes = text.split(":")
    return int(hours) * 3600 + int(minutes) * 60


def _matrix(rows: list[list[float]]) -> Matrix:
    """Copy a list of lists into tuples, so an instance cannot be changed by accident."""
    return tuple(tuple(float(value) for value in row) for row in rows)
