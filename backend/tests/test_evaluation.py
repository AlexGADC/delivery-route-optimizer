"""Tests for evaluate. Every expected number was worked out by hand."""

from dataclasses import replace

import pytest

from app.domain.evaluation import evaluate
from app.domain.instance import Instance, Stop


def test_brasov_route_in_the_prototype_order(brasov5):
    """Leave at 08:00, visit stops 1-2-3-4, with 5 minutes of service at each."""
    result = evaluate(brasov5, (1, 2, 3, 4))

    # Driving: 391.5 + 566.0 + 404.9 + 532.8 + 394.6
    assert result.travel_time_s == pytest.approx(2289.8)
    # Distance: 2958.5 + 4454.0 + 3617.9 + 5254.8 + 3847.5
    assert result.distance_m == pytest.approx(20132.7)

    # Coresi Mall: arrives 08:06:31.5, its window opens at 09:00.
    coresi = result.visits[0]
    assert coresi.arrival_s == pytest.approx(8 * 3600 + 391.5)
    assert coresi.wait_s == pytest.approx(3208.5)
    assert coresi.start_s == 9 * 3600

    # Waiting at the four stops: 3208.5 + 2734.0 + 2895.1 + 2767.2
    assert result.waiting_s == pytest.approx(11604.8)

    # Nobody is reached late, so the cost is the driving time alone.
    assert result.late_stops == 0
    assert result.lateness_s == 0
    assert result.cost == pytest.approx(2289.8)

    # Leaves Astra at 12:05:00 and drives 394.6 s back: 12:11:34.6.
    assert result.return_s == pytest.approx(12 * 3600 + 11 * 60 + 34.6)


def test_early_arrival_waits_and_late_arrival_is_penalised(tiny):
    """Tour A then B.

    Leave 0. Arrive A at 100, wait 200 until it opens at 300, leave at 310.
    Drive 50, arrive B at 360. B closed at 150, so the courier is 210 late.
    Leave B at 370, drive 220 back, return at 590.
    """
    result = evaluate(tiny, (1, 2))

    assert result.travel_time_s == 100 + 50 + 220
    assert result.distance_m == 3700
    assert result.waiting_s == 200
    assert result.lateness_s == 210
    assert result.late_stops == 1
    assert result.return_s == 590
    assert result.cost == 370 + 10 * 210

    visit_a, visit_b = result.visits
    assert (visit_a.arrival_s, visit_a.wait_s, visit_a.start_s, visit_a.lateness_s) == (100, 200, 300, 0)
    assert (visit_b.arrival_s, visit_b.wait_s, visit_b.start_s, visit_b.lateness_s) == (360, 0, 360, 210)


def test_the_other_order_uses_the_other_direction_of_the_matrix(tiny):
    """Tour B then A.

    Leave 0. Arrive B at 200, which is 50 late. Leave at 210.
    Drive 70 (B to A, not the 50 of A to B), arrive A at 280, wait 20, leave at 310.
    Drive 120 back, return at 430.
    """
    result = evaluate(tiny, (2, 1))

    assert result.travel_time_s == 200 + 70 + 120
    assert result.waiting_s == 20
    assert result.lateness_s == 50
    assert result.late_stops == 1
    assert result.return_s == 430
    assert result.cost == 390 + 10 * 50


def test_arriving_exactly_when_the_window_closes_is_on_time(tiny):
    b_closes_at_200 = replace(tiny.stops[2], close_s=200)
    instance = replace(tiny, stops=(tiny.stops[0], tiny.stops[1], b_closes_at_200))

    result = evaluate(instance, (2, 1))  # arrives at B at exactly 200

    assert result.late_stops == 0
    assert result.lateness_s == 0
    assert result.cost == 390


def test_returning_after_the_depot_closes_adds_lateness(tiny):
    depot_closes_at_400 = replace(tiny.stops[0], close_s=400)
    instance = replace(tiny, stops=(depot_closes_at_400, tiny.stops[1], tiny.stops[2]))

    result = evaluate(instance, (2, 1))  # returns at 430, which is 30 late

    assert result.lateness_s == 50 + 30
    assert result.late_stops == 1  # counts customers only
    assert result.cost == 390 + 10 * 80


def test_an_instance_with_only_a_depot_has_an_empty_route():
    depot = Stop("depot", 0.0, 0.0, open_s=0, close_s=100)
    instance = Instance(name="empty", stops=(depot,), durations_s=((0,),), distances_m=((0,),))

    result = evaluate(instance, ())

    assert result.visits == ()
    assert result.cost == 0


@pytest.mark.parametrize(
    "tour",
    [
        (1,),  # misses a customer
        (1, 1),  # visits one twice
        (0, 1, 2),  # includes the depot
        (1, 3),  # names a stop that does not exist
    ],
)
def test_rejects_a_tour_that_is_not_every_customer_exactly_once(tiny, tour):
    with pytest.raises(ValueError, match="every customer exactly once"):
        evaluate(tiny, tour)
