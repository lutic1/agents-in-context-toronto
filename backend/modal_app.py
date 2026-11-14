"""The Modal app for DxP (Story 8.1, A04): the API and the run function, on the Atlas Sandbox.

Deploy configuration only; no API code lives here (D36). Only this module imports `dxp.api`,
and nothing imports this module (AD-12 import arrows).

- `run_pipeline(run_id)` wraps `pipeline.run` (A10) with a 3600-second timeout (AD-16).
- `api()` mounts the ASGI app from `create_app(run_pipeline)` (A01). The API starts a run with
  `.spawn()` on the function object it was handed, never `modal.Function.from_name`, so a
  `modal serve` API only ever starts its own run function, never production's (AD-16).

Environment at deploy or serve time (read on the laptop, see docs/deploy.md):

- `DXP_DB` is required and is passed to the containers with `modal.Secret.from_dict`:
  `dxp` for the production deploy, a developer's own database (for example `dxp_luis`) or
  `dxp_smoke` under `modal serve` (AD-24, D41). It is never defaulted.
- `MODAL_DEV_SUFFIX` (optional) gives a developer's app its own name, `dxp-<suffix>`; a suffixed
  app refuses `DXP_DB=dxp`.
- Every credential comes from the Modal secret named by `DXP_MODAL_SECRET` (default `dxp`),
  set by hand from `.env` and never written to a file (D48).
"""

from __future__ import annotations

import os
from pathlib import Path

import modal

BACKEND_DIR = Path(__file__).resolve().parent

# The secret every container reads. Its keys are set by hand (docs/deploy.md); none is in the repo.
SECRET_NAME = os.environ.get("DXP_MODAL_SECRET", "dxp")

# Keys the deploy refuses to start without. ELEVENLABS_API_KEY (OD3), HEYGEN_API_KEY (OD7) and
# VOYAGE_API_KEY (OD1, only if cleared) are optional: without them the media players say
# "unavailable" and retrieval follows DXP_EMBEDDING. DXP_FEATURES is optional too: absent means
# every backend flag is off (task_run, revert and live_stream stay off, V38, V46, V48).
REQUIRED_SECRET_KEYS = [
    "MONGODB_URI",
    "DXP_AGENT_KEY",
    "ANTHROPIC_API_KEY",
    "SLACK_WEBHOOK_URL",
    "DXP_BASE_URL",
    "DXP_ALLOWED_ORIGINS",
    "DXP_EMBEDDING",
]

RUN_TIMEOUT_SECONDS = 3600  # AD-16: one run is one call of the run function, up to an hour.

dev_suffix = os.environ.get("MODAL_DEV_SUFFIX", "").strip()
app_name = f"dxp-{dev_suffix}" if dev_suffix else "dxp"

db_name = os.environ.get("DXP_DB", "").strip()
if modal.is_local():
    if not db_name:
        raise RuntimeError(
            "DXP_DB is not set. Production: DXP_DB=dxp modal deploy modal_app.py; "
            "a developer: DXP_DB=dxp_<name> MODAL_DEV_SUFFIX=<name> modal serve modal_app.py"
        )
    if dev_suffix and db_name == "dxp":
        raise RuntimeError("A developer app (MODAL_DEV_SUFFIX set) never writes to DXP_DB=dxp.")

app = modal.App(app_name)

image = (
    modal.Image.debian_slim(python_version="3.13")
    # Dependencies exactly as pinned in backend/uv.lock (A01); no later PR edits either file.
    .uv_sync(str(BACKEND_DIR), frozen=True)
    .add_local_python_source("dxp")
)

secrets = [
    modal.Secret.from_name(SECRET_NAME, required_keys=REQUIRED_SECRET_KEYS),
    modal.Secret.from_dict({"DXP_DB": db_name or None}),
]


@app.function(image=image, secrets=secrets, timeout=RUN_TIMEOUT_SECONDS)
async def run_pipeline(run_id: str) -> None:
    """One run (discover, setup item or a task's run), started by the API with `.spawn()`."""
    from dxp import pipeline

    await pipeline.run(run_id)


@app.function(
    image=image,
    secrets=secrets,
    # One warm container: the startup hook (recovery, dispatch_next) runs once, and the demo
    # never waits on a cold start.
    min_containers=1,
    scaledown_window=900,
    timeout=900,
)
@modal.concurrent(max_inputs=64)
@modal.asgi_app(label=app_name)
def api():
    """The FastAPI app (A01), with every route under /api/v1."""
    from dxp.api.app import create_app

    return create_app(run_pipeline)
