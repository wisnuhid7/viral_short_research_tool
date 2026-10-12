"""JS-compatible JSON response.

`JSON.stringify` in Node never emits a trailing `.0` for integral numbers, so
`500.0` is written as `500` and `-0.0` as `0`. Python's `json` module emits
`500.0` verbatim, which produced byte-level differences against the TypeScript
server (e.g. `totalBudget` on campaign responses, where better-sqlite3 also
binds integral JS numbers as SQLite INTEGER).

Serializing integral floats as integers here mirrors JS number semantics for
every route, so the HTTP contract stays byte-identical.
"""
import json
import math
from typing import Any

from fastapi.responses import JSONResponse


def _js_numbers(value: Any) -> Any:
    if isinstance(value, float):
        # JSON.stringify emits `null` for NaN/Infinity and never a trailing
        # `.0`, so mirror both: non-finite -> None, finite integral -> int.
        if not math.isfinite(value):
            return None
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, dict):
        return {key: _js_numbers(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_js_numbers(item) for item in value]
    return value


class JsJSONResponse(JSONResponse):
    # Express `res.json()` emits `application/json; charset=utf-8`. Starlette's
    # default is bare `application/json`, so pin the charset for byte parity.
    media_type = "application/json; charset=utf-8"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            _js_numbers(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")
