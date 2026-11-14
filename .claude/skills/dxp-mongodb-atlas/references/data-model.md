> Reference only. Do not copy this code into the project; it was written before the event.

# DxP data model and write patterns (FR-3, FR-4, FR-11, FR-15, FR-16, FR-17)

Operators and methods used here were checked on 12 November 2026 against the MongoDB manual and the PyMongo 4.19 API reference. The shape itself is a proposal for architecture to confirm.

## Collections and unique keys

| Collection | Unique index | Why |
| --- | --- | --- |
| `diagnostics` | `match_key` | one Record per Diagnostic (FR-3) |
| `source_items` | `(source, source_item_id)` | processing a batch twice changes nothing |
| `proposed_changes` | `(diagnostic_id, field, finding_id)` | one Proposed change per Finding per field |
| `graph_links` | `_id` built from the two node ids | one link per pair |

Create the indexes before the first ingest. A unique index built after duplicates exist fails.

## Record document

```python
{
  "_id": ObjectId(),
  "match_key": "guardant360 cdx|guardant health",   # normalised by the application; set in architecture
  "name": "Guardant360 CDx",
  "synonyms": ["g360 cdx"],
  "version": 7,                                     # optimistic lock, +1 on every write
  "early_research": False,                          # FR-2
  "fields": {                                       # single-valued fields (FR-5, FR-17)
    "regulatory_status": {
      "value": "FDA approved",
      "status": "accepted",                         # "unreviewed" | "accepted" | "manual"
      "confidence": 0.93,
      "check": {"quote_in_source": True, "supports_value": True},   # FR-18
      "evidence": {"source_item_id": "...", "source_type": "fda_cdx_list", "url": "...",
                   "quote": "...", "study_context": None},
      "change_id": ObjectId(), "accepted_by": "reviewer@team", "accepted_at": datetime,
      "history": [                                  # oldest first; appended on every change
        {"value": "PMA submitted", "status": "accepted", "evidence": {...}, "change_id": ...,
         "accepted_by": "...", "accepted_at": datetime, "replaced_at": datetime}
      ]
    }
  },
  "lifecycle": { ...same shape as one field... },    # FR-11: history gives every earlier stage and date
  "lists": {                                        # list-valued fields only grow (FR-15)
    "trials": [
      {"key": "NCT01234567", "value": {"title": "...", "phase": "3"}, "status": "accepted",
       "evidence": {...}, "change_id": ..., "accepted_by": "...", "added_at": datetime}
    ],
    "study_results": [], "linked_drugs": []
  },
  "facets": {"modality": "ctDNA NGS", "tumour_type": ["NSCLC"], "tumour_stage": ["III", "IV"],
             "sample_type": "plasma", "clinical_use": "companion diagnostic",
             "regulatory_status": "FDA approved"},  # copies of current values for filters
  "search_text": "Guardant360 CDx ... ",            # the autoEmbed path
  "created_at": datetime, "updated_at": datetime
}
```

Rules that follow from the PRD:

- FR-7: the read path drops any field or list entry with no `evidence.quote`, and any whose `check` failed (FR-18). Enforce it in one serialiser, not per view.
- `facets` and `search_text` are derived. Rebuild them in the same update that changes a field. They are for retrieval only and are never displayed.
- Keep `history` on the field. One Record with ten fields and a few changes each stays far below the 16 MB document limit.

## Match before create (FR-3)

```python
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

async def get_or_create_diagnostic(db, match_key: str, new_doc: dict) -> tuple[dict, bool]:
    """new_doc must NOT contain match_key or _id. Returns (record, created)."""
    for _ in range(3):
        try:
            res = await db.diagnostics.update_one(
                {"match_key": match_key},            # equality on the unique key and nothing else
                {"$setOnInsert": {**new_doc, "version": 1,
                                  "created_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
            rec = await db.diagnostics.find_one({"match_key": match_key})
            return rec, res.upserted_id is not None
        except DuplicateKeyError:                    # lost the race; the next loop finds the winner
            continue
    raise RuntimeError(f"could not upsert {match_key}")
```

Why this is safe: with a unique index, exactly one concurrent upsert inserts. The server lets the others fall through to an update only when the filter is equality on exactly the unique-index fields and the update does not touch those fields. Break either condition and the losers raise `DuplicateKeyError`.

New Records carry `"status": "unreviewed"` on every value (FR-16). When `created` is false, do not write to the Record: draft a Proposed change.

Source items, same idea, so a re-run is a no-op:

```python
res = await db.source_items.update_one(
    {"source": "clinicaltrials", "source_item_id": nct_id},
    {"$setOnInsert": {"fetched_at": now, "status": "new"}}, upsert=True)
first_time = res.upserted_id is not None
```

## Proposed change

```python
{"_id": ObjectId(), "diagnostic_id": ..., "finding_id": ..., "field": "regulatory_status",
 "kind": "set",                     # or "add" with "list": "trials", "entry_key": "NCT..."
 "current_value": "PMA submitted", "new_value": "FDA approved",
 "evidence": {...}, "confidence": 0.93, "check": {...},
 "status": "pending",               # pending | applying | accepted | edited | rejected
 "rule_flags": [{"rule_id": ..., "rule_name": "..."}],   # FR-19: flags, never withdrawals
 "decided_by": None, "decided_at": None, "reason": None, "created_at": datetime}
```

Insert with `insert_one` and treat `DuplicateKeyError` as "already drafted".

## Accept a single-valued change (FR-16, FR-17)

```python
from pymongo import ReturnDocument

SNAPSHOT = ("value", "status", "confidence", "check", "evidence",
            "change_id", "accepted_by", "accepted_at")

async def accept_set_change(db, change_id, reviewer: str, edited_value=None) -> bool:
    now = datetime.now(timezone.utc)
    ch = await db.proposed_changes.find_one_and_update(      # claim it: blocks a double accept
        {"_id": change_id, "status": "pending"},
        {"$set": {"status": "applying", "decided_by": reviewer, "decided_at": now}},
        return_document=ReturnDocument.AFTER)
    if ch is None:
        return False
    f = ch["field"]
    value = ch["new_value"] if edited_value is None else edited_value
    for _ in range(5):
        rec = await db.diagnostics.find_one({"_id": ch["diagnostic_id"]})
        cur = rec["fields"].get(f)
        update = {
            "$set": {f"fields.{f}.value": value, f"fields.{f}.status": "accepted",
                     f"fields.{f}.evidence": ch["evidence"], f"fields.{f}.confidence": ch["confidence"],
                     f"fields.{f}.check": ch["check"], f"fields.{f}.change_id": change_id,
                     f"fields.{f}.accepted_by": reviewer, f"fields.{f}.accepted_at": now,
                     "updated_at": now},
            "$inc": {"version": 1},
        }
        if cur is not None:                                   # keep the prior value and its Evidence
            update["$push"] = {f"fields.{f}.history":
                               {**{k: cur.get(k) for k in SNAPSHOT}, "replaced_at": now}}
        res = await db.diagnostics.update_one(
            {"_id": rec["_id"], "version": rec["version"]}, update)   # lost update guard
        if res.modified_count == 1:
            await db.proposed_changes.update_one(
                {"_id": change_id},
                {"$set": {"status": "edited" if edited_value is not None else "accepted"}})
            return True
    return False
```

Also set `facets.<f>` (and `lifecycle`, `early_research` when the field is the Lifecycle stage) in the same `$set`. Never `$set` the whole `fields.<f>` object together with the `$push`: the paths conflict.

## Add to a list-valued field (FR-15)

```python
async def add_list_entry(db, diagnostic_id, list_name: str, entry: dict) -> bool:
    """entry has a stable 'key' (NCT id, PMID, drug name). Returns False if already present."""
    now = datetime.now(timezone.utc)
    res = await db.diagnostics.update_one(
        {"_id": diagnostic_id, f"lists.{list_name}.key": {"$ne": entry["key"]}},
        {"$push": {f"lists.{list_name}": {**entry, "added_at": now}},
         "$inc": {"version": 1}, "$set": {"updated_at": now}})
    return res.modified_count == 1
```

One atomic update: the entry is appended, nothing is overwritten, and two workers adding the same trial leave one entry. `$addToSet` would not do this, because two entries for the same trial differ in Evidence or time and count as different documents.

## Rejecting, and the audit trail

Reject is one update on `proposed_changes`: `{"_id": id, "status": "pending"}` to `{"status": "rejected", "decided_by", "decided_at", "reason"}`. The Record is not touched. `proposed_changes` is the log of Reviewer actions that FR-16 tests against: every changed value in a Record carries the `change_id` that points to it.

## Batch progress (FR-4)

```python
await db.batch_runs.update_one(
    {"_id": run_id},
    {"$inc": {"processed": 1, "failed": int(failed), "early_research": int(is_early)}})
```

`$inc` is atomic, so parallel workers cannot lose counts. The front end reads the one `batch_runs` document, by polling or through the change stream.

## Many writes at once

```python
from pymongo import UpdateOne
ops = [UpdateOne({"source": s, "source_item_id": i}, {"$setOnInsert": {...}}, upsert=True)
       for s, i in items]
result = await db.source_items.bulk_write(ops, ordered=False)
```

`ordered=False` attempts every operation and reports failures at the end as `BulkWriteError`. The default `ordered=True` stops at the first error.
