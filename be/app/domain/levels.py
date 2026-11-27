"""Levels and attributes (docs/domain/pet-rules.md, "Levels and attributes").

Experience is the sum of `points_event` rows. Points are append-only and always positive, so the
level never goes down; fainting never removes levels or attributes. Reaching level N grants N
attribute points, which the user spends permanently on one of five attributes. In the MVP the
attributes are display only. Nothing here uses body data, calories or meal judgement.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum

from app.domain.config import DEFAULT_RULES, PetRulesConfig
from app.domain.pet import PetEvent


class Attribute(StrEnum):
    STRENGTH = "strength"
    SPEED = "speed"
    SKILL = "skill"
    ENDURANCE = "endurance"
    INTELLIGENCE = "intelligence"


@dataclass(frozen=True, slots=True)
class Attributes:
    """Points spent on each attribute. All start at 0 and never go down in the MVP."""

    strength: int = 0
    speed: int = 0
    skill: int = 0
    endurance: int = 0
    intelligence: int = 0

    def __post_init__(self) -> None:
        for attribute in Attribute:
            if getattr(self, attribute.value) < 0:
                raise ValueError("attributes must not be negative")

    def get(self, attribute: Attribute) -> int:
        value: int = getattr(self, attribute.value)
        return value

    @property
    def total(self) -> int:
        return sum(self.get(attribute) for attribute in Attribute)

    def as_dict(self) -> dict[str, int]:
        return {attribute.value: self.get(attribute) for attribute in Attribute}


@dataclass(frozen=True, slots=True)
class LevelProgress:
    """Experience points and the point totals where the current and next level start."""

    points: int
    current_level_at: int
    next_level_at: int


class NotEnoughAttributePointsError(ValueError):
    """The allocation asks for more points than the pet has unspent."""


def level_for_points(points: int, config: PetRulesConfig = DEFAULT_RULES) -> int:
    """Level 1 at 0 points, then one level per `points_per_level` points."""
    if points < 0:
        raise ValueError("points are never negative")
    return points // config.points_per_level + 1


def level_progress(points: int, config: PetRulesConfig = DEFAULT_RULES) -> LevelProgress:
    level = level_for_points(points, config)
    return LevelProgress(
        points=points,
        current_level_at=(level - 1) * config.points_per_level,
        next_level_at=level * config.points_per_level,
    )


def attribute_points_granted(level: int) -> int:
    """Total attribute points granted up to `level`: reaching level N grants N points."""
    if level < 1:
        raise ValueError("level starts at 1")
    return level * (level + 1) // 2


def unspent_attribute_points(level: int, attributes: Attributes) -> int:
    return max(0, attribute_points_granted(level) - attributes.total)


def spend_attribute_points(
    attributes: Attributes, allocations: Mapping[Attribute, int], level: int
) -> Attributes:
    """Add `allocations` to `attributes`, all or nothing.

    Every amount must be a positive integer and at least one attribute must be chosen. Raises
    `NotEnoughAttributePointsError` when the total exceeds the unspent points for `level`.
    """
    if not allocations:
        raise ValueError("choose at least one attribute")
    if any(amount <= 0 for amount in allocations.values()):
        raise ValueError("allocations must be positive")
    if sum(allocations.values()) > unspent_attribute_points(level, attributes):
        raise NotEnoughAttributePointsError("not enough attribute points")
    changes = {
        attribute.value: attributes.get(attribute) + amount
        for attribute, amount in allocations.items()
    }
    return replace(attributes, **changes)


def level_events(last_seen_level: int | None, current_level: int) -> tuple[PetEvent, ...]:
    """`level_up` when the level rose since the client last saw it (unknown last level: none)."""
    if last_seen_level is not None and current_level > last_seen_level:
        return (PetEvent.LEVEL_UP,)
    return ()
