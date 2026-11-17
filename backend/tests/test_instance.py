import json

import pytest

from app.domain.instance import Instance, Stop
from app.infrastructure.instance_files import load_instance, parse_clock


def test_loads_the_brasov_instance(brasov5):
    assert brasov5.name == "brasov-5"
    assert len(brasov5.stops) == 5
    assert brasov5.depot == 0
    assert brasov5.customers == (1, 2, 3, 4)


def test_file_times_become_seconds_since_midnight(brasov5):
    coresi = brasov5.stops[1]
    assert coresi.name == "Coresi Mall"
    assert coresi.open_s == 9 * 3600
    assert coresi.close_s == 10 * 3600 + 30 * 60


def test_matrix_keeps_both_directions(brasov5):
    # Depot -> Gara and Gara -> depot differ because of one-way streets.
    assert brasov5.durations_s[0][2] == 359.6
    assert brasov5.durations_s[2][0] == 187.3


def test_parse_clock():
    assert parse_clock("00:00") == 0
    assert parse_clock("09:30") == 34200


def test_rejects_a_matrix_of_the_wrong_size(tiny):
    with pytest.raises(ValueError, match="one row and one column per stop"):
        Instance(name="bad", stops=tiny.stops, durations_s=((0, 1), (1, 0)), distances_m=tiny.distances_m)


def test_rejects_a_window_that_closes_before_it_opens():
    backwards = Stop("backwards", 0.0, 0.0, open_s=500, close_s=100)
    with pytest.raises(ValueError, match="closes before it opens"):
        Instance(name="bad", stops=(backwards,), durations_s=((0,),), distances_m=((0,),))


def test_file_must_mark_exactly_one_depot(tmp_path):
    content = {
        "name": "no-depot",
        "stops": [{"name": "a", "lat": 0, "lon": 0, "open": "08:00", "close": "09:00"}],
        "durations_s": [[0]],
        "distances_m": [[0]],
    }
    file = tmp_path / "no-depot.json"
    file.write_text(json.dumps(content), encoding="utf-8")

    with pytest.raises(ValueError, match="exactly one stop must be marked as the depot"):
        load_instance(file)
