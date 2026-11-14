> Reference only. Do not copy this code into the project; it was written before the event.

# Fallback: the same three behaviours on plain Atlas collections

Use when `DXP_MEMORY_BACKEND=collections`: the Agent Engine memory runtime is not ready, the preview misbehaves, or there is no M10 cluster. It needs only `pymongo` and `MONGODB_URI`, and works on any Atlas tier including Free.

These collections exist in both modes. With Agent Engine memory they are the system of record (rule on/off flag, structured team state, canonical term list) and memory is the agent's recall layer. In fallback mode they are also the recall layer.

## What to say on camera in fallback mode

- Say: "the team's history is stored as episodic memory in MongoDB Atlas", "learned rules are procedural memory in an Atlas collection", "the term list is taxonomic memory in Atlas".
- Do not say "Atlas Agent Engine", "Agent Memory service" or "public preview": none of them is in use.
- Semantic recall in this mode needs Atlas Vector Search on the collection (see the Vector Search skill). Without it, recall is by exact key and recency, which is enough for the FR-28, FR-19 and FR-9 tests.

## Collections

| Collection | Memory type | Shape |
| --- | --- | --- |
| `team_profiles` | profile (system of record) | `{_id: team_id, intended_use, shortlist_ids, last_seen_at}` |
| `memory_episodes` | episodic | `{team_id, session_id, title, content, tags, ended_at}` |
| `memory_facts` | semantic | `{team_id, label, text, metadata, updated_at}`, unique on `(team_id, label)` |
| `learned_rules` | procedural (system of record) | `{rule_id, team_id, field, text, status: draft\|active\|off, source_rejection_id, created_at}` |
| `terms` | taxonomic (system of record) | `{domain, standard, definition, synonyms, synonyms_lc}` |

## Code

```python
# dxp/memory_collections.py
import os
from datetime import datetime, timezone
import pymongo
from pymongo import MongoClient

db = MongoClient(os.environ["MONGODB_URI"])["dxp"]
DOMAIN = "lung-cancer-diagnostics"

def ensure_indexes() -> None:
    db.memory_facts.create_index([("team_id", pymongo.ASCENDING), ("label", pymongo.ASCENDING)], unique=True)
    db.memory_episodes.create_index([("team_id", pymongo.ASCENDING), ("ended_at", pymongo.DESCENDING)])
    db.learned_rules.create_index("rule_id", unique=True)
    db.learned_rules.create_index([("field", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
    db.terms.create_index([("domain", pymongo.ASCENDING), ("standard", pymongo.ASCENDING)], unique=True)
    db.terms.create_index("synonyms_lc")

def _now() -> datetime:
    return datetime.now(timezone.utc)

# FR-28 episodic + semantic -------------------------------------------------
def end_session(team_id: str, session_id: str, intended_use: str, shortlist: list[dict], summary: str) -> None:
    now = _now()
    db.team_profiles.update_one(
        {"_id": team_id},
        {"$set": {"intended_use": intended_use, "shortlist_ids": [d["id"] for d in shortlist], "last_seen_at": now}},
        upsert=True,
    )
    for label, text in (
        ("intended-use", f"Current intended use: {intended_use}"),
        ("shortlist", "Shortlisted diagnostics: " + ", ".join(d["name"] for d in shortlist)),
    ):
        db.memory_facts.update_one(
            {"team_id": team_id, "label": label},
            {"$set": {"text": text, "updated_at": now}},
            upsert=True,
        )
    db.memory_episodes.insert_one({
        "team_id": team_id, "session_id": session_id, "title": f"DxP session {now.date().isoformat()}",
        "content": summary, "tags": ["dxp-session"], "ended_at": now,
    })

def resume(team_id: str) -> dict:
    profile = db.team_profiles.find_one({"_id": team_id}) or {}
    episodes = list(db.memory_episodes.find({"team_id": team_id}, sort={"ended_at": pymongo.DESCENDING}, limit=3))
    facts = list(db.memory_facts.find({"team_id": team_id}))
    lines = [f"- {f['text']}" for f in facts] + [f"- {e['title']}: {e['content']}" for e in episodes]
    return {
        "context_for_prompt": "What DxP remembers about this team:\n" + "\n".join(lines),
        "memories": [{"source": "semantic", "text": f["text"], "at": f["updated_at"]} for f in facts]
                  + [{"source": "episodic", "text": e["content"], "at": e["ended_at"]} for e in episodes],
        "recent_episodes": episodes,
        "profile": profile,                       # intended_use, shortlist_ids, last_seen_at
    }

# FR-19 procedural ------------------------------------------------------------
def draft_rule(rule: dict) -> None:
    db.learned_rules.insert_one({**rule, "status": "draft", "created_at": _now()})

def confirm_rule(rule: dict) -> None:
    db.learned_rules.update_one({"rule_id": rule["rule_id"]}, {"$set": {"status": "active", "confirmed_at": _now()}})

def switch_rule_off(rule_id: str) -> None:
    db.learned_rules.update_one({"rule_id": rule_id}, {"$set": {"status": "off"}})

def active_rule_ids() -> set[str]:
    return {r["rule_id"] for r in db.learned_rules.find({"status": "active"})}

def visible_flags(change: dict) -> list[dict]:
    """Flags are stored on the Proposed change as [{rule_id, rule_text}]; show only those whose rule is active."""
    active = active_rule_ids()
    return [f for f in change.get("flags", []) if f["rule_id"] in active]

def rules_for(change: dict, active_rule_ids: set[str] | None = None) -> list[dict]:
    """Active rules for the change's field. Caller asks Claude whether each is broken."""
    rules = db.learned_rules.find({"field": change["field"], "status": "active"})
    return [{"procedure": r["rule_id"], "content": r["text"], "score": 1.0} for r in rules]

# FR-9 taxonomic --------------------------------------------------------------
def seed_terms(terms: list[dict]) -> None:
    for t in terms:
        db.terms.update_one(
            {"domain": DOMAIN, "standard": t["standard"]},
            {"$set": {"definition": t["definition"], "synonyms": t["synonyms"],
                      "synonyms_lc": [s.lower() for s in t["synonyms"]] + [t["standard"].lower()]}},
            upsert=True,
        )

def resolve_term(text: str) -> str | None:
    hit = db.terms.find_one({"domain": DOMAIN, "synonyms_lc": text.strip().lower()})
    return hit["standard"] if hit else None        # None: unmatched, send to the Reviewer
```

Flags are filtered at read time instead of being deleted, so switching a rule off (FR-19) is one update and switching it back on restores the flags. `active_rule_ids()` and `visible_flags()` are used in both backends.

## Switching backends

Keep one module-level switch so call sites do not change:

```python
# dxp/memory_api.py
import os
if os.environ.get("DXP_MEMORY_BACKEND", "agent_engine") == "collections":
    from dxp.memory_collections import end_session, resume, confirm_rule, rules_for, seed_terms, resolve_term  # noqa: F401
else:
    from dxp.memory import end_session, resume, confirm_rule, rules_for, seed_terms, resolve_term
```

In `agent_engine` mode still write `team_profiles`, `learned_rules` and `terms` (the functions above minus the recall parts), because the rule on/off flag, the last-visit timestamp and the deterministic synonym match live there in both modes.

## Third option: LangGraph's MongoDB store

`langgraph-store-mongodb` 0.4.0 gives namespaced long-term memory with optional vector search, on any tier that supports Vector Search indexes:

```python
from langgraph.store.mongodb import MongoDBStore

with MongoDBStore.from_conn_string(conn_string=os.environ["MONGODB_URI"], db_name="dxp",
                                   collection_name="lg_store") as store:
    store.put(namespace=("team", team_id, "episodes"), key=session_id, value={"content": summary})
    items = store.search(("team", team_id, "episodes"), limit=3)      # filter-only search, no query
    store.delete(("team", team_id, "episodes"), session_id)
```

Semantic `store.search(..., query="...")` needs `index_config=create_vector_index_config(embed=..., dims=..., fields=[...])` at construction. On camera this is "the MongoDB Store for LangGraph", not Agent Memory. It has no built-in episodic, procedural or taxonomic types: those are namespaces you choose.
