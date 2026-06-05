"""Real-world ↔ model unit conversion."""

from __future__ import annotations

METERS_PER_MODEL_UNIT = 0.1
MODEL_UNITS_PER_METER = 10.0


def meters_to_model(value: float) -> float:
    return value * MODEL_UNITS_PER_METER


def model_to_meters(value: float) -> float:
    return value * METERS_PER_MODEL_UNIT
