"""Request-body validation helpers that mirror zod's error message style.

The TypeScript routes report `Input tidak valid: <joined issue messages>` where
the messages come from zod. Pydantic emits its own phrasing, so we translate the
common cases back to zod-like text to keep the API error strings close to parity.
"""
from typing import Any

import re

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from api.app.errors import ValidationError


def _type_name(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _zod_like(err: Any) -> str:
    etype = err.get("type", "")
    ctx = err.get("ctx") or {}
    inp = err.get("input")

    if etype == "missing":
        return "Required"
    if etype == "string_too_short" and "min_length" in ctx:
        return f"String must contain at least {ctx['min_length']} character(s)"
    if etype == "string_too_long" and "max_length" in ctx:
        return f"String must contain at most {ctx['max_length']} character(s)"
    if etype == "too_short" and "min_length" in ctx:
        return f"Array must contain at least {ctx['min_length']} element(s)"
    if etype == "too_long" and "max_length" in ctx:
        return f"Array must contain at most {ctx['max_length']} element(s)"
    if etype == "literal_error":
        raw = ctx.get("expected", "")
        tokens = re.findall(r"'[^']*'", raw)
        expected = " | ".join(tokens) if tokens else raw
        return f"Invalid enum value. Expected {expected}, received '{inp}'"
    if etype == "greater_than":
        return f"Number must be greater than {ctx.get('gt')}"
    if etype == "greater_than_equal":
        return f"Number must be greater than or equal to {ctx.get('ge')}"
    if etype == "less_than":
        return f"Number must be less than {ctx.get('lt')}"
    if etype == "less_than_equal":
        return f"Number must be less than or equal to {ctx.get('le')}"
    if etype in ("string_type",):
        return f"Expected string, received {_type_name(inp)}"
    if etype in ("int_type", "float_type", "int_parsing", "float_parsing"):
        return f"Expected number, received {_type_name(inp)}"
    if etype in ("bool_type", "bool_parsing"):
        return f"Expected boolean, received {_type_name(inp)}"
    if etype in ("list_type",):
        return f"Expected array, received {_type_name(inp)}"
    if etype in ("dict_type", "model_type", "model_attributes_type"):
        return f"Expected object, received {_type_name(inp)}"

    return err.get("msg", "Input tidak valid")


def parse_body(model: type[BaseModel], data) -> BaseModel:
    """Validate `data` against `model`, raising ValidationError (400) zod-style.

    Mirrors `schema.safeParse(undefined)` in zod: a missing/`null` body yields a
    single root-level "Required" issue, whereas `{}` yields one per required
    field. Passing `None` straight to Pydantic would report every required field.
    """
    if data is None:
        raise ValidationError("Input tidak valid: Required")
    try:
        return model.model_validate(data)
    except PydanticValidationError as exc:
        messages = [_zod_like(e) for e in exc.errors()]
        raise ValidationError(f"Input tidak valid: {', '.join(messages)}") from exc


def parse_body_campaign(model: type[BaseModel], data) -> BaseModel:
    """Campaign create uses a slightly different prefix in the TS route."""
    if data is None:
        raise ValidationError("Input campaign tidak valid: Required")
    try:
        return model.model_validate(data)
    except PydanticValidationError as exc:
        messages = [_zod_like(e) for e in exc.errors()]
        raise ValidationError(f"Input campaign tidak valid: {', '.join(messages)}") from exc
