"""The only MongoDB client (AD-14 conventions: "Only store creates a client").

- `db()` (alias `get_db()`) returns the database named by `DXP_DB` on the client for `MONGODB_URI`;
  `collection(name)` returns one collection.
- `ensure_indexes()` creates every collection's regular indexes and applies A03's
  `$jsonSchema` validators (`store/schemas/`) with validationLevel strict and
  validationAction error. It runs at API startup and is safe to run again.
- `emit_event()` is the only writer of `events` (AD-10).
"""

from __future__ import annotations

from dxp.store.client import close, collection, db, get_client, get_db
from dxp.store.events import emit_event
from dxp.store.indexes import COLLECTIONS, INDEXES, ensure_indexes

__all__ = ["COLLECTIONS", "INDEXES", "close", "collection", "db", "emit_event", "ensure_indexes", "get_client", "get_db"]
