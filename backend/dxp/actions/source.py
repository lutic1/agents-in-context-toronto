"""`record_source_result`: the `search_source` action's status and result (AD-19, AD-20, D24).

Luis's ruling: nothing outside `runs`, `gate` and `actions` writes those collections, so A05's
scan (`discovery/scan.py`) is the sender but records its action through here.

- `status="dispatching"` claims it: `queued` -> `dispatching` with `claimed_at`; `result` must
  be None. Only the caller whose claim matched sends the request.
- `status="delivered"` or `"failed"` records what was observed: `dispatching` -> that status
  with `result { http_status, cursor_from, cursor_to, source_refs, count }` and `observed_at`.
  `search_source` is a read, so a timeout is `failed`, never `unknown` (AD-19).

Each step is one update conditional on the current status and on `kind: search_source`, so a
repeat or a slow worker changes nothing; a change emits `action_status_changed`. Returns True
when the update matched. On False, read the action (`records.get` or the `actions` collection)
to see its current state; reading is not writing.
"""

from __future__ import annotations

from typing import Any, Literal

from dxp.actions import records
from dxp.api.models import SearchSourceResult

KIND = "search_source"
_FROM = {"dispatching": "queued", "delivered": "dispatching", "failed": "dispatching"}


async def record_source_result(
    action_id: str,
    *,
    status: Literal["dispatching", "delivered", "failed"],
    result: dict[str, Any] | SearchSourceResult | None,
) -> bool:
    """Move a `search_source` action one step, conditional on its current status (D24)."""
    if status not in _FROM:
        raise ValueError(f"a search_source action moves to dispatching, delivered or failed, not {status!r}")
    if status == "dispatching":
        if result is not None:
            raise ValueError("claiming (dispatching) records no result")
        fields: dict[str, Any] = {"claimed_at": records.now()}
    else:
        if result is None:
            raise ValueError(f"{status} needs the observed result")
        checked = result if isinstance(result, SearchSourceResult) else SearchSourceResult.model_validate(result)
        fields = {"result": checked.model_dump(mode="python"), "observed_at": records.now()}
    return await records.transition(action_id, _FROM[status], status, fields, kind=KIND)
