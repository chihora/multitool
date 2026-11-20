from typing import Literal

_LENGTH_IN_METERS = {
    "m": 1.0,
    "km": 1000.0,
    "ft": 0.3048,
    "mi": 1609.344,
}
_TEMPERATURE_UNITS = frozenset(("C", "F", "K"))


def convert(value: float, from_unit: str, to_unit: str) -> float:
    from_kind = _unit_kind(from_unit)
    to_kind = _unit_kind(to_unit)
    if from_kind != to_kind:
        raise ValueError("cannot convert between length and temperature")

    if from_kind == "length":
        meters = value * _LENGTH_IN_METERS[from_unit]
        return meters / _LENGTH_IN_METERS[to_unit]

    celsius = _to_celsius(value, from_unit)
    return _from_celsius(celsius, to_unit)


def _unit_kind(unit: str) -> Literal["length", "temperature"]:
    if unit in _LENGTH_IN_METERS:
        return "length"
    if unit in _TEMPERATURE_UNITS:
        return "temperature"
    raise ValueError(f"unknown unit: {unit}")


def _to_celsius(value: float, unit: str) -> float:
    if unit == "C":
        return value
    if unit == "F":
        return (value - 32.0) * 5.0 / 9.0
    return value - 273.15


def _from_celsius(value: float, unit: str) -> float:
    if unit == "C":
        return value
    if unit == "F":
        return value * 9.0 / 5.0 + 32.0
    return value + 273.15
