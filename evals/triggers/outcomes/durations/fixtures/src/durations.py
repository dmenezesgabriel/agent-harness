"""Converts a duration with a unit into whole seconds."""


def to_seconds(amount: int, unit: str) -> int:
    if unit == "s":
        return amount
    elif unit == "min":
        return amount * 60
    elif unit == "h":
        return amount * 3600
    else:
        raise ValueError("unknown unit: " + unit)
