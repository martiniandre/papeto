"""Levels and attributes: level from points, points granted, spending and the level_up event."""

from __future__ import annotations

import pytest

from app.domain import (
    Attribute,
    Attributes,
    LevelProgress,
    NotEnoughAttributePointsError,
    PetEvent,
    PetRulesConfig,
    attribute_points_granted,
    level_events,
    level_for_points,
    level_progress,
    spend_attribute_points,
    unspent_attribute_points,
)
from tests.unit.fakes import SAO_PAULO, FakeClock, FakeUser, at


@pytest.mark.parametrize(
    ("points", "level"),
    [(0, 1), (5, 1), (99, 1), (100, 2), (199, 2), (200, 3), (1000, 11)],
)
def test_level_for_points(points: int, level: int) -> None:
    assert level_for_points(points) == level


def test_level_threshold_is_tunable() -> None:
    config = PetRulesConfig(points_per_level=50)
    assert level_for_points(49, config) == 1
    assert level_for_points(50, config) == 2


def test_points_per_level_must_be_positive() -> None:
    with pytest.raises(ValueError, match="points_per_level"):
        PetRulesConfig(points_per_level=0)


def test_negative_points_are_rejected() -> None:
    with pytest.raises(ValueError, match="never negative"):
        level_for_points(-1)


def test_level_progress() -> None:
    assert level_progress(0) == LevelProgress(points=0, current_level_at=0, next_level_at=100)
    assert level_progress(150) == LevelProgress(points=150, current_level_at=100, next_level_at=200)
    assert level_progress(200) == LevelProgress(points=200, current_level_at=200, next_level_at=300)


@pytest.mark.parametrize(("level", "granted"), [(1, 1), (2, 3), (3, 6), (4, 10), (10, 55)])
def test_attribute_points_granted(level: int, granted: int) -> None:
    assert attribute_points_granted(level) == granted


def test_level_starts_at_one() -> None:
    with pytest.raises(ValueError, match="starts at 1"):
        attribute_points_granted(0)


def test_new_pet_is_level_1_with_one_point_to_spend() -> None:
    attributes = Attributes()
    assert attributes.as_dict() == {
        "strength": 0,
        "speed": 0,
        "skill": 0,
        "endurance": 0,
        "intelligence": 0,
    }
    assert level_for_points(0) == 1
    assert unspent_attribute_points(1, attributes) == 1


def test_attributes_never_negative() -> None:
    with pytest.raises(ValueError, match="negative"):
        Attributes(speed=-1)


def test_spend_adds_points_and_reduces_unspent() -> None:
    spent = spend_attribute_points(Attributes(), {Attribute.STRENGTH: 2, Attribute.SKILL: 1}, 2)
    assert spent == Attributes(strength=2, skill=1)
    assert unspent_attribute_points(2, spent) == 0


def test_spend_more_than_unspent_is_rejected_and_changes_nothing() -> None:
    start = Attributes(speed=1)
    with pytest.raises(NotEnoughAttributePointsError):
        spend_attribute_points(start, {Attribute.SPEED: 2, Attribute.ENDURANCE: 1}, 2)
    assert start == Attributes(speed=1)


@pytest.mark.parametrize("amount", [0, -1])
def test_spend_rejects_non_positive_amounts(amount: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        spend_attribute_points(Attributes(), {Attribute.INTELLIGENCE: amount}, 3)


def test_spend_rejects_empty_allocation() -> None:
    with pytest.raises(ValueError, match="at least one"):
        spend_attribute_points(Attributes(), {}, 3)


def test_not_enough_points_is_a_distinct_error() -> None:
    assert issubclass(NotEnoughAttributePointsError, ValueError)


@pytest.mark.parametrize(
    ("last_seen", "current", "expected"),
    [
        (None, 3, ()),
        (1, 1, ()),
        (1, 2, (PetEvent.LEVEL_UP,)),
        (1, 4, (PetEvent.LEVEL_UP,)),  # several levels at once: one event
        (3, 2, ()),  # cannot happen (points never drop); never an event
    ],
)
def test_level_events(last_seen: int | None, current: int, expected: tuple[PetEvent, ...]) -> None:
    assert level_events(last_seen, current) == expected


def test_crossing_several_levels_in_one_log() -> None:
    config = PetRulesConfig(points_per_level=5)
    user = FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2)), SAO_PAULO, config)
    before = level_for_points(user.total_points(), config)
    user.log()  # +10 points crosses two thresholds of 5
    after = level_for_points(user.total_points(), config)
    assert (before, after) == (1, 3)
    assert level_events(before, after) == (PetEvent.LEVEL_UP,)
    assert unspent_attribute_points(after, Attributes()) == 6


def test_level_and_attributes_never_decrease_after_fainting() -> None:
    config = PetRulesConfig(points_per_level=10)
    user = FakeUser(FakeClock(at(SAO_PAULO, 2026, 3, 2)), SAO_PAULO, config)
    user.log()
    level = level_for_points(user.total_points(), config)
    attributes = spend_attribute_points(Attributes(), {Attribute.STRENGTH: 3}, level)
    user.next_day(3)  # two missed days: fainted
    assert user.read().lives == 0
    assert level_for_points(user.total_points(), config) == level == 2
    assert unspent_attribute_points(level, attributes) == 0
    assert attributes == Attributes(strength=3)
    user.log()  # wake up: +10 and +5 points, the level only goes up
    assert level_for_points(user.total_points(), config) == 3
