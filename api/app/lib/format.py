"""Numeric formatting helpers that reproduce JavaScript semantics.

`Math.round` rounds half away from zero (toward +Infinity for positives),
whereas Python's built-in round() uses banker's rounding. `Number.prototype.
toLocaleString('id-ID')` and `Number` -> String conversion also differ from
Python defaults. These helpers are used wherever output must match the TS
backend byte-for-byte.
"""
import math


def js_round(value: float) -> int:
    """Math.round for non-negative values (all call sites are non-negative)."""
    return math.floor(value + 0.5)


def to_id_string(value: int | float) -> str:
    """Best-effort `Number.toLocaleString('id-ID')` for integers.

    id-ID uses '.' as the thousands separator and ',' as the decimal separator.
    """
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        sign = "-" if value < 0 else ""
        digits = str(abs(value))
        grouped = ""
        while len(digits) > 3:
            grouped = "." + digits[-3:] + grouped
            digits = digits[:-3]
        return sign + digits + grouped
    # Non-integer fallback: group integer part, ',' decimal part.
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    int_part, _, dec_part = text.partition(".")
    grouped = to_id_string(int(int_part)) if int_part not in ("", "-") else int_part
    return f"{grouped},{dec_part}" if dec_part else grouped


def js_number_to_string(value: int | float) -> str:
    """Approximate JS `String(number)` for the value ranges we use."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return repr(value)
    return str(value)