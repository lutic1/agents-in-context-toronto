> Reference only. Do not copy this code into the project; it was written before the event.

# `agent-engine-sdk-memory` API: signatures used by DxP

Source: the `agent_engine_sdk_memory.memory` API reference and the 0.11.14 wheel (checked 12 November 2026). All methods are synchronous. Import everything from the package root:

```python
from agent_engine_sdk_memory import (
    Memory, MemoryRequestContext, MemoryChunk, ContextResponse,
    SourceSpec, MemorySource, SearchSource, RetrievalMode, FormatStyle,
    MemoryAPIError, MemoryAuthError, MemoryBadRequestError, MemoryClientError,
    MemoryConnectionError, MemoryIdentityError, MemoryNotProvisionedError,
    MemoryNotSupportedError, MemoryRouteNotFoundError, MemoryServerError,
)
```

## Construction and identity

```python
Memory(*, service_account_token: str | None = None, base_url: str | None = None,
       project_id: str | None = None, api_key: str | None = None)   # api_key is deprecated
memory.bind(ctx: MemoryRequestContext) -> Memory     # new handle; original is not mutated
memory.close()                                        # Memory is also a context manager
MemoryRequestContext(user_id: str | None = None, agent_id: str | None = None, session_id: str | None = None)
```

- Hosted: `service_account_token` + `project_id`. Local: `base_url` only.
- Identity precedence per call: call argument, then bound context, then runtime context.
- A bound handle shares its parent's transport; closing either closes both.
- A service account may name any end user as `user_id`.

## Conversation turns and assembled context

```python
record_turn(*, role: str, content: str | None = None, session_id: str | None = None,
            tool_calls: list[dict] | None = None, tool_call_id: str | None = None,
            tool_name: str | None = None, is_error: bool = False, model_name: str | None = None,
            metadata: dict | None = None, idempotency_key: str | None = None) -> WriteTurnResult

build_context(query: str, user_id=None, session_id=None, visibility=None,
              metadata_filter: dict | None = None, enabled_sources: set[str] | None = None, *,
              max_tokens: int | None = None, format_style: FormatStyle | str | None = None,
              include_memories: bool = False) -> ContextResponse

build_context_from_sources(query: str, sources: Sequence[SourceSpec], *, user_id=None, session_id=None,
                           visibility=None, rerank: bool = False, max_tokens: int | None = None,
                           format_style=None, include_memories: bool = False,
                           collapse_duplicate_content: bool = True) -> ContextResponse

SourceSpec(source: MemorySource, mode: RetrievalMode = "semantic",
           metadata_filter: dict | None = None, top_k: int = 20)    # top_k 1..200
```

- `enabled_sources` values: `"stm"`, `"episodic"`, `"semantic"`, `"taxonomic"`, `"procedural"`. Default is episodic + semantic.
- `format_style`: `"openai"` (chat-message list), `"claude"` (XML string), `"jinja2"` (markdown string). Omitted: the server infers from its configured model.
- `RetrievalMode`: `"text"` (`$search`), `"semantic"` (`$vectorSearch`), `"hybrid"`. Docs recommend hybrid for text-bearing sources.
- An `stm` source in `build_context_from_sources` fails unless the project lists `short_term` in `metadata_partition_index`. Use plain `build_context(enabled_sources={"stm", ...})` for recent turns.
- `thread_id` is a deprecated alias for `session_id`.

## Semantic (labelled facts; default visibility `private`)

```python
save_semantic(*, text: str, label: str, user_id=None, source: str = "agent", visibility: str = "private",
              metadata: dict | None = None, upsert: bool = True, agent_id=None) -> CreateSemanticResult
search_semantic(query: str, user_id=None, visibility=None, top_k: int = 50) -> list[MemoryChunk]
get_semantic(label: str, user_id=None, visibility=None) -> Any | None
```

`upsert=True` replaces an existing memory with the same label. This is the only documented overwrite in the public API.

## Episodic (summarised episodes; default visibility `private`)

```python
save_episode(*, title: str, content: str, user_id=None, summary: str | None = None, session_id=None,
             participants: list[str] | None = None, tags: list[str] | None = None,
             visibility: str = "private", metadata: dict | None = None, agent_id=None) -> CreateEpisodicResult
search_episodes(query: str, user_id=None, visibility=None, session_id=None, top_k: int = 50) -> list[MemoryChunk]
list_episodes(user_id=None, visibility=None, session_id=None, limit: int = 20) -> list[Any]
```

`save_episode` raises `MemoryIdentityError` without both `user_id` and `session_id`. Reads never inherit a bound `session_id`.

## Procedural (reusable procedures; default visibility `private`)

```python
save_procedure(*, procedure: str, description: str, content: str, user_id=None,
               steps: list[dict] | None = None, resources: list[dict] | None = None,
               allowed_tools: list[str] | None = None, compatibility: str | None = None,
               license: str | None = None, trigger_conditions: list[str] | None = None,
               tags: list[str] | None = None, visibility: str = "private", agent_id=None,
               extraction_source=None, source_format=None, source_path=None,
               metadata: dict | None = None, update_existing: bool = False) -> CreateProceduralResult
discover_procedures(query: str, user_id=None, *, visibility=None, tags: list[str] | None = None,
                    top_k: int = 10, similarity_threshold: float = 0.0,
                    metadata_filter: dict | None = None) -> list[dict]
get_procedure(procedure_name: str, *, user_id=None, visibility=None, include_deleted: bool = False) -> Any | None
```

- `update_existing=True` works only for agents running on the platform; over HTTP it raises `MemoryNotSupportedError`.
- `discover_procedures` returns dicts with keys `id`, `timestamp`, `procedure`, `content`, `score`, plus the record's metadata keys (0.11.14 source).
- What happens when the same `procedure` name is saved twice over HTTP is UNVERIFIED. Use unique names.

## Taxonomic (domain terms; default visibility `org`)

```python
save_taxonomic(*, domain: str, term: str, definition: str, related_terms: list[str] | None = None,
               visibility: str = "org", user_id=None, metadata: dict | None = None) -> CreateTaxonomicResult
search_taxonomic(query: str, user_id=None, domain: str | None = None, visibility=None, top_k: int = 50) -> list[MemoryChunk]
get_taxonomic_term(domain: str, term: str, user_id=None, visibility=None) -> Any | None
list_domains(visibility: str | None = None) -> list[str]
```

`save_taxonomic` requires a resolvable `user_id` even though the record is org-visible. Taxonomic search is a ranked vector search, optionally filtered by `domain`. Whether `related_terms` are searchable is UNVERIFIED, which is why DxP also writes the synonyms into `definition`.

## Cross-type search

```python
search(query: str, *, sources=None, top_k: int = 10, user_id=None, visibility=None, session_id=None,
       domain=None, tags=None, similarity_threshold: float = 0.0, metadata_filter=None) -> list[MemoryChunk]
```

`sources` defaults to `["semantic", "episodic"]`; accepts `"semantic"`, `"episodic"`, `"taxonomic"`, `"procedural"`. It is a client-side fan-out merged by `similarity_score`.

## Custom memory types (not needed by DxP)

```python
save(memory_type: str, content: str, *, tags: Mapping | None = None, contextual_metadata: dict | None = None) -> CustomMemorySaveResult
retrieve(memory_type: str, query: str, *, tags: Mapping | None = None, top_k: int = 10) -> CustomMemoryRetrieveResult
```

Declared under `memory.custom_memory_types` in `project-config.yaml` (max 5; write-once). Hosted route is flag-gated; not available on the local stack.

## Models (0.11.14)

```python
MemoryChunk:      id: str, content: str, source: "stm"|"episodic"|"semantic"|"taxonomic"|"procedural",
                  timestamp: datetime, embedding: list[float] | None, similarity_score: float | None,
                  metadata: dict | None
ContextResponse:  formatted_context: str | list[dict], metadata: ContextMetadata,
                  selected_memories: list[MemoryChunk] | None      # only with include_memories=True
ContextMetadata:  token_count: int, memory_counts: dict[str, int], timing: dict[str, float],
                  ranking_strategy: str | None, source_outcomes: list[dict] | None
WriteTurnResult:  id, session_id, turn_seq, acknowledged, has_embedding
CreateSemanticResult:   id, label, has_embedding, acknowledged
CreateEpisodicResult:   id, title, has_embedding, acknowledged
CreateTaxonomicResult:  id, domain, term, has_embedding, acknowledged
CreateProceduralResult: id, procedure, has_embedding, acknowledged
```

- The dict passed as `metadata=` on a write comes back at `chunk.metadata["metadata"]`. An empty dict means no slot: read with `chunk.metadata.get("metadata", {})`.
- `similarity_score` is comparable only between chunks retrieved the same way.
- `has_embedding=False` on a write result means the record is stored but only findable by text or hybrid retrieval, not by `search_*` (vector only).
- `get_semantic`, `get_taxonomic_term`, `get_procedure` and `list_episodes` return raw JSON typed `Any`. Field names are UNVERIFIED: print one result before writing code that reads fields.

## Errors

| Error | Meaning |
| --- | --- |
| `MemoryIdentityError` (`ValueError`) | A required `user_id` or `session_id` could not be resolved. Not caught by `except MemoryClientError`. |
| `MemoryClientError` (`ValueError`) | Usage error raised before the network call. |
| `MemoryNotSupportedError` | Operation unavailable on this connection (for example `update_existing`, custom types locally). |
| `MemoryAuthError` | 401 or 403. Usually an expired token or a `project_id` that does not match the token's project. |
| `MemoryBadRequestError` | Other 4xx, including undeclared `metadata_filter` paths in `SourceSpec`. |
| `MemoryRouteNotFoundError` | 404 on a core route: set or unset `project_id`. Subclass of `MemoryBadRequestError`. |
| `MemoryNotProvisionedError` | The project's memory runtime is not reachable yet. |
| `MemoryServerError` | 5xx or an unparseable body. A context call returns 503 when every requested source failed. |
| `MemoryConnectionError` | Backend unreachable. |

All transport errors derive from `MemoryAPIError` and carry `status` and the response body. Extraction failures never surface through the SDK; the only sign is memories not appearing.

## TypeScript equivalent

`@mongodb-js/agent-engine-sdk-memory` uses camelCase and a single object argument: `new Memory({ serviceAccountToken, projectId })`, `memory.bind({ userId, sessionId })`, `saveSemantic({ label, text })`, `searchEpisodes({ query })`, `saveProcedure({ procedure, description, content })`, `getProcedure({ procedureName })`, `saveTaxonomic({ domain, term, definition })`, `searchTaxonomic({ query, domain })`, `buildContext({ query, enabledSources: new Set([...]) })`. Requires Node.js 24+ and ES modules. DxP calls memory from Python only.
