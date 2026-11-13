---
name: dxp-atlas-agent-memory
description: Agent memory for DxP on MongoDB Atlas Agent Engine (public preview) - semantic, episodic, procedural and taxonomic memory through the `agent-engine-sdk-memory` Python SDK, plus how it relates to `langgraph-checkpoint-mongodb` (MongoDBSaver) and `langgraph-store-mongodb` (MongoDBStore). Load when a task mentions Atlas Agent Memory, Agent Engine, agentengine CLI, team memory or resume (FR-28), learned rules (FR-19), ontology or synonyms in memory (FR-9), `save_episode`, `save_procedure`, `save_taxonomic`, `build_context`, or naming a MongoDB memory capability in the demo.
---

# MongoDB Atlas Agent Engine memory for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Read its Precedence paragraph before copying an example from here.

## Verified

Checked 12 November 2026 against official MongoDB pages and PyPI.

| Item | Version / fact |
| --- | --- |
| Product | **MongoDB Atlas Agent Engine**, Public Preview since 29 Sep 2026. Memory docs page is titled "Agent Memory". |
| Python SDK | `agent-engine-sdk-memory` 0.11.14 on PyPI (11 Nov 2026), Python >= 3.11, depends only on `httpx` and `pydantic`. The hosted guide pins 0.11.8. |
| CLI | `agentengine` v0.1.125 (11 Nov 2026). Memory-only projects need >= 0.1.120. |
| TypeScript SDK | `@mongodb-js/agent-engine-sdk-memory`, Node.js 24+, ES modules. |
| LangGraph packages | `langgraph-checkpoint-mongodb` 0.5.1, `langgraph-store-mongodb` 0.4.0, `langgraph` 1.2.21, `pymongo` 4.20.0 |
| API contract | `2026-09-20-preview` |

Pages used: `mongodb.com/docs/agentengine/` (memory-types, memory, memory-only, memory-extraction, memory-mcp, sdk/python/packages/agent-engine-sdk-memory and its API reference and capability matrix, reference/limitations, build/install-authenticate, api-keys-service-accounts, deploy/atlas-setup), `mongodb.com/products/platform/atlas-agent-engine`, the 29 Sep 2026 press release, `mongodb.com/docs/atlas/ai-integrations/langgraph/`, the `langchain-ai/langchain-mongodb` changelogs, and the 0.11.14 wheel source for model fields.

## Read this first

1. **The product is real and "taxonomic" is a real memory type.** The four built-in long-term types are semantic, episodic, procedural, taxonomic. The earlier doubt is resolved.
2. **Say the name correctly on camera.** The product is "MongoDB Atlas Agent Engine"; the feature is "Agent Memory" or "Atlas Agent Engine memory". "Atlas Agent Memory" appears only in the press release as a billing line item. Preferred wording: "episodic memory in MongoDB Atlas Agent Engine, in public preview".
3. **It is not a switch on an Atlas cluster.** It is a separate platform at `agentengine.mongodb.com` that runs a memory server for you and writes into your own cluster. Setup needs: the `agentengine` CLI (a binary downloaded after sign-in, not pip or brew), a Voyage AI API key, an LLM API key for extraction, a service account, and two IP access list entries. **Provision on Friday, not Saturday.** Steps: `references/hosted-setup.md`.
4. **No free tier.** Atlas Free (M0) clusters are not supported. The standalone guide requires **M10 or larger**; the agent guide says Flex is the minimum. Use M10.
5. **The public SDK cannot delete or update a memory.** There are no delete methods, and `save_procedure(update_existing=True)` raises `MemoryNotSupportedError` over HTTP. So "switch a Learned rule off" (FR-19) must be a flag in a DxP collection, not a memory deletion.
6. **Background extraction is asynchronous (a minute or more) and never fires on a lone user turn.** For the live demo use direct writes (`save_episode`, `save_procedure`, `save_taxonomic`), not `record_turn` plus waiting.
7. **Memory is scoped to a "user", not a team.** Bind `user_id` to the DxP team id. Semantic, episodic and procedural default to `private`; taxonomic defaults to `org` (shared across the project).
8. **Taxonomic memory is a glossary, not an ontology engine**: `domain`, `term`, `definition`, `related_terms`. Lookup is exact by (domain, term) or ranked vector search. FR-9's test needs a deterministic synonym match, so the canonical term list stays in a DxP collection and is mirrored into taxonomic memory.
9. **Do not use `agent-engine-sdk-langgraph`.** It is for agents deployed on the Agent Engine runtime. DxP runs LangGraph on Modal, so it uses `agent-engine-sdk-memory` (standalone memory service) plus `langgraph-checkpoint-mongodb`.

## What DxP uses it for

- **FR-28 Resume** - episodic memory (`save_episode`, `list_episodes`, `build_context`) plus semantic facts keyed by label. Structured state (Intended use, Shortlist ids, last visit time) also lives in the `team_profiles` collection.
- **FR-19 Learned rule** - procedural memory (`save_procedure`, `discover_procedures`, `get_procedure`). The `learned_rules` collection is the system of record and holds the on/off flag.
- **FR-9 Standard terms and synonyms** - taxonomic memory (`save_taxonomic`, `search_taxonomic`, `get_taxonomic_term`), mirrored from the `terms` collection.
- **LangGraph run state and Reviewer interrupts (FR-15, FR-16)** - `MongoDBSaver`, which is the LangGraph checkpointer, not Agent Engine memory.
- **Section 8 "Real behaviour on camera"** - one live memory write and read, one live Learned rule.

## Setup

```bash
pip install 'agent-engine-sdk-memory==0.11.14' 'langgraph-checkpoint-mongodb==0.5.1' httpx pymongo
```

If a call fails against the hosted server with 0.11.14, try `0.11.8`, the version the hosted guide pins. Install from PyPI only; the platform's own package registry serves an older SDK.

Environment variables (names only):

| Name | Read by | Purpose |
| --- | --- | --- |
| `AGENTIC_MEMORY_PROJECT_ID` | SDK | Atlas project id. Set for hosted; must be **unset** for the local Docker stack. |
| `AGENTIC_MEMORY_SERVICE_ACCOUNT_TOKEN` | SDK | Access token. Expires after one hour, so DxP mints it in code instead. |
| `AGENTIC_MEMORY_BASE_URL` | SDK | Only for the local stack (the `oe` URL printed by `agentengine dev up`). |
| `AGENTENGINE_SA_CLIENT_ID`, `AGENTENGINE_SA_CLIENT_SECRET` | DxP code (names chosen by DxP) | Service account credentials used to mint tokens. |
| `MONGODB_URI` | DxP code | The same Atlas cluster, for DxP collections and the checkpointer. |
| `DXP_MEMORY_BACKEND` | DxP code | `agent_engine` or `collections` (the fallback). |

Project secrets uploaded once with the CLI (not app env): `MONGODB_URI`, `VOYAGE_API_KEY`, `LLM_API_KEY`.

## Core patterns

### Client with token refresh

The SDK is synchronous. In async LangGraph nodes or FastAPI handlers, wrap calls in `asyncio.to_thread`.

```python
# dxp/memory.py
import os, threading, time
import httpx
from agent_engine_sdk_memory import Memory, MemoryRequestContext

TOKEN_URL = "https://agentengine.mongodb.com/api/v1/oauth/token"
ONTOLOGY_USER = "dxp-ontology"          # owner identity for shared writes
DOMAIN = "lung-cancer-diagnostics"

_lock = threading.Lock()
_memory: Memory | None = None
_expires_at = 0.0

def memory() -> Memory:
    """Unbound handle. Re-mints the one-hour token five minutes before expiry."""
    global _memory, _expires_at
    with _lock:
        if _memory is None or time.time() > _expires_at - 300:
            r = httpx.post(
                TOKEN_URL,
                auth=(os.environ["AGENTENGINE_SA_CLIENT_ID"], os.environ["AGENTENGINE_SA_CLIENT_SECRET"]),
                data={"grant_type": "client_credentials"},
                timeout=30,
            )
            r.raise_for_status()
            body = r.json()                      # access_token, token_type, expires_in (3600)
            _memory = Memory(
                service_account_token=body["access_token"],
                project_id=os.environ["AGENTIC_MEMORY_PROJECT_ID"],
            )
            _expires_at = time.time() + int(body.get("expires_in", 3600))
        return _memory

def team(team_id: str, session_id: str | None = None) -> Memory:
    """Handle scoped to one team. Ids: letters, digits, '_' and '-' only."""
    return memory().bind(MemoryRequestContext(user_id=team_id, session_id=session_id))
```

### FR-28: resume a team's context (episodic + semantic)

```python
from datetime import datetime, timezone

def end_session(team_id: str, session_id: str, intended_use: str, shortlist: list[dict], summary: str) -> None:
    m = team(team_id, session_id)                       # save_episode needs user_id AND session_id
    now = datetime.now(timezone.utc).isoformat()
    m.save_semantic(label="intended-use", text=f"Current intended use: {intended_use}")   # upsert by label
    m.save_semantic(label="shortlist",
                    text="Shortlisted diagnostics: " + ", ".join(d["name"] for d in shortlist),
                    metadata={"diagnostic_ids": [d["id"] for d in shortlist]})
    m.save_episode(title=f"DxP session {now[:10]}", content=summary,
                   tags=["dxp-session"], metadata={"ended_at": now, "session_id": session_id})

def resume(team_id: str) -> dict:
    m = team(team_id)                                   # no session: episodes are stored session-unscoped
    ctx = m.build_context(
        query="What was this team working on, and what did they decide or shortlist?",
        enabled_sources={"episodic", "semantic"},
        max_tokens=2000,                                # must be well above the 500-token reserve
        format_style="claude",                          # XML string for a Claude prompt
        include_memories=True,
    )
    return {
        "context_for_prompt": ctx.formatted_context,
        "memories": [{"source": c.source, "text": c.content, "at": c.timestamp} for c in (ctx.selected_memories or [])],
        "recent_episodes": m.list_episodes(limit=3),    # raw JSON; field names UNVERIFIED, print once
    }
```

"What changed since the last visit" is not a memory query: read `last_seen_at` from `team_profiles` and query the change log with it. Keep Intended use and Shortlist ids in `team_profiles` as well, so the UI restore is deterministic.

### FR-19: Learned rule (procedural)

`learned_rules` (DxP collection) holds `{rule_id, field, text, status: draft|active|off, team_id, source_rejection_id}`. Write to memory only when the Reviewer confirms.

```python
def confirm_rule(rule: dict) -> None:
    team(rule["team_id"]).save_procedure(
        procedure=rule["rule_id"],                      # create-only: never reuse a name; new id per revision
        description=f"Review rule for field '{rule['field']}'",
        content=rule["text"],
        trigger_conditions=[f"a proposed change to the field {rule['field']}"],
        tags=["dxp-learned-rule", rule["field"]],
        visibility="org",                               # every reviewer in the project sees it
        metadata={"rule_id": rule["rule_id"], "field": rule["field"]},
    )

def rules_for(change: dict, active_rule_ids: set[str]) -> list[dict]:
    """Candidate rules for one Proposed change. Caller asks Claude whether each is broken."""
    hits = memory().discover_procedures(                # unbound + org: shared rules from any owner
        f"proposed change to {change['field']}: {change['new_value']}",
        visibility="org", tags=["dxp-learned-rule"], top_k=5,
    )
    # each hit: {"id", "timestamp", "procedure", "content", "score", ...your metadata keys}
    return [h for h in hits if h["procedure"] in active_rule_ids]
```

Switching a rule off: set `status: "off"` in `learned_rules` and show only flags whose rule is active (`visible_flags` in the fallback reference). The memory record stays; the `active_rule_ids` filter stops it applying. `get_procedure(rule_id, visibility="org")` reads one rule back by name for the on-camera "read".

### FR-9: ontology and synonyms (taxonomic)

```python
def seed_terms(terms: list[dict]) -> None:
    """terms: [{"standard": "ctDNA", "definition": "...", "synonyms": ["liquid biopsy", "cfDNA assay"]}]"""
    m = memory().bind(MemoryRequestContext(user_id=ONTOLOGY_USER))   # save_taxonomic requires a user_id
    for t in terms:
        if m.get_taxonomic_term(DOMAIN, t["standard"]) is None:      # duplicate behaviour UNVERIFIED: seed once
            m.save_taxonomic(
                domain=DOMAIN, term=t["standard"],
                definition=f"{t['definition']} Also called: {', '.join(t['synonyms'])}.",
                related_terms=t["synonyms"],
                metadata={"standard": t["standard"]},                # visibility defaults to "org"
            )

def resolve_term(text: str, terms_coll) -> str | None:
    hit = terms_coll.find_one({"synonyms_lc": text.strip().lower()})  # deterministic path first
    if hit:
        return hit["standard"]
    chunks = memory().search_taxonomic(text, domain=DOMAIN, visibility="org", top_k=3)
    if chunks and (chunks[0].similarity_score or 0) >= 0.75:          # threshold is a guess: calibrate
        return ((chunks[0].metadata or {}).get("metadata") or {}).get("standard")
    return None                                                       # unmatched: send to the Reviewer
```

To put definitions into an agent prompt: `build_context(query, enabled_sources={"taxonomic", "semantic"})` (taxonomic and procedural are opt-in sources).

### LangGraph run state

```python
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

checkpointer = MongoDBSaver(MongoClient(os.environ["MONGODB_URI"]), db_name="dxp")
graph = builder.compile(checkpointer=checkpointer)
graph.invoke(inputs, {"configurable": {"thread_id": f"{team_id}-{session_id}"}})   # thread_id must be a str
```

This writes the `checkpoints` and `checkpoint_writes` collections. Call it "the MongoDB checkpointer for LangGraph", never "Agent Memory". `MongoDBStore` (`langgraph-store-mongodb`) is LangGraph's own long-term store; DxP does not need it alongside Agent Engine memory.

## Limits and costs

- **Preview pricing (subject to change):** $0.25 per 1,000 long-term memory docs stored; $0.50 per 1,000 memory docs retrieved. `search_semantic`, `search_episodes` and `search_taxonomic` default to `top_k=50`: always pass a small `top_k`.
- **Throughput:** a project's Orchestration Engine, which hosted memory calls are proxied through, serves up to 50 concurrent requests per second. No memory-specific rate limit is documented. For the 300 to 500 item batch, fetch active rules and terms once per batch and cache them; do not call memory per item at full parallelism.
- **Token:** one hour. Requesting tokens too often returns `429`.
- **SDK transport (0.11.14 source):** 30 s timeout, 3 attempts.
- **Extraction:** a snapshot forms at `max_messages: 20` or after `stale_minutes` idle (default 3; the memory-only scaffold sets 1). Docs say long-term memories take "a minute or two" to appear.
- **Index lag:** Atlas Search indexes writes asynchronously, so a search straight after a write can miss it. `get_*` by label or name is the safer on-camera read; retry searches for a few seconds.
- **Caps:** 5 custom memory types, 10 tags per type, 10 metadata partition keys, `SourceSpec.top_k` 1 to 200.
- **No SLA or SLO in preview.** Breaking changes are expected.

## Gotchas

- Read scoping is **AND**, never OR. `team(t).search_semantic(q, visibility="org")` returns only org-visible records that team owns. For shared plus private, make two calls and merge. Passing `user_id=None` does not widen a bound handle; use the unbound `memory()`.
- `search_episodes`, `list_episodes` and the episodic leg of `search()` ignore the bound `session_id`. Pass `session_id=` explicitly only if you want one session.
- `build_context` defaults to episodic and semantic only. `stm`, `taxonomic` and `procedural` must be listed in `enabled_sources`.
- `max_tokens` at or below 500 returns nothing: the server reserves 500 tokens for formatting.
- `metadata_filter` only works on keys declared under `metadata_partition_key` in `project-config.yaml`, written as `metadata.<name>`. Partition keys cannot be removed or retyped later. Avoid them on Saturday; filter in Python.
- `record_turn` takes no `user_id`: bind first. A user turn with no assistant turn after it is never extracted.
- `MemoryRouteNotFoundError` (404): `AGENTIC_MEMORY_PROJECT_ID` is set against a local stack, or unset against hosted.
- `MemoryNotProvisionedError`: the memory runtime is not ready. Run `agentengine memory status`; on a new project the first `apply` can fail with `memory-server deployment not found` while provisioning continues. Poll status; do not re-run apply.
- `MemoryIdentityError` subclasses `ValueError`, not `MemoryClientError`.
- `api_key` / `AGENTIC_MEMORY_API_KEY` are deprecated; visibility `"shared"` is deprecated (use `"org"`).
- `agentengine memory configure` stores config; only `agentengine memory apply` restarts the server so it takes effect.
- Never put the service account secret or token in the Next.js front end. Call memory from the Python backend.
- Stored data lives in your cluster in database `mdb_memory_<project-id>` by default. Collection names and document schema are UNVERIFIED (not documented): do not query them directly in product code.

## Fallback

If the memory runtime is not `ready` by 10:00 on Saturday, or it fails during the day, set `DXP_MEMORY_BACKEND=collections` and use the same function names backed by plain Atlas collections: `references/plain-collections-fallback.md`. On camera, then say "memory stored in MongoDB Atlas collections, organised as episodic, procedural and taxonomic memory" and do not name Agent Engine. A halfway option that needs no cluster: the local Docker stack (`agentengine dev up`), reachable only from the same machine.

## Links

- Agent Memory concepts and the four types: https://www.mongodb.com/docs/agentengine/add-features/memory-types/
- Standalone memory service (the DxP path): https://www.mongodb.com/docs/agentengine/add-features/memory-only/
- Python SDK guide: https://www.mongodb.com/docs/agentengine/sdk/python/packages/agent-engine-sdk-memory/
- `Memory` API reference: https://www.mongodb.com/docs/agentengine/sdk/python/packages/agent-engine-sdk-memory/docs/api/memory/
- Capability matrix: https://www.mongodb.com/docs/agentengine/sdk/python/packages/agent-engine-sdk-memory/docs/capability-matrix/
- Memory extraction: https://www.mongodb.com/docs/agentengine/add-features/memory-extraction/
- Limitations: https://www.mongodb.com/docs/agentengine/reference/limitations/
- Service accounts and tokens: https://www.mongodb.com/docs/agentengine/api-keys-service-accounts/
- Product page and pricing: https://www.mongodb.com/products/platform/atlas-agent-engine
- MongoDB with LangGraph (checkpointer and store): https://www.mongodb.com/docs/atlas/ai-integrations/langgraph/
- Docs index for agents: https://www.mongodb.com/docs/agentengine/llms.txt (append `.md` to any docs URL for Markdown)
- Local references: `references/hosted-setup.md`, `references/api-signatures.md`, `references/plain-collections-fallback.md`
