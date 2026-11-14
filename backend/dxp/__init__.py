"""DxP backend.

Package layout and owners: architecture spine "Source tree". Imports follow the
AD-28 arrows: gate, runs and actions import nothing from memory, retrieval or
reports.
"""

from __future__ import annotations

import os

__all__ = ["feature_enabled"]


def feature_enabled(name: str) -> bool:
    """Backend feature flags from DXP_FEATURES (comma-separated names, V38).

    Flags: task_run (V38), revert and live_stream (V48), interview (V70). Every flag is off unless named;
    `task_run` stays off until I3b passes (V46);
    NEXT_PUBLIC_DXP_FEATURES only controls what the web app displays.
    """
    raw = os.environ.get("DXP_FEATURES", "")
    return name in {part.strip() for part in raw.split(",") if part.strip()}
