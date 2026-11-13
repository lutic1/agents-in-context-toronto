# Hosted memory-only project: one-time setup

Source: https://www.mongodb.com/docs/agentengine/add-features/memory-only/ (checked 12 November 2026). Do this before the hackathon day. It needs a browser sign-in and interactive secret prompts, so a human runs it, not an unattended agent.

## Prerequisites

- An Atlas account. New and existing Atlas customers sign in at `https://agentengine.mongodb.com`.
- An Atlas cluster of tier **M10 or larger**. Free and shared tiers cannot hold the Atlas Search and Vector Search indexes that memory creates.
- Your Atlas user has the **Project Owner** role on the Atlas project, assigned explicitly (Organization Owner alone is not enough). Note the organization id and project id.
- A database user with the `readWriteAnyDatabase` role. Memory creates its own databases, so a user scoped to one database fails.
- A percent-encoded connection string that includes that user's name and password.
- A Voyage AI API key (embeddings) and an LLM provider API key (background extraction; Anthropic is supported).
- `agentengine` CLI >= 0.1.120, Python >= 3.11, `curl`, `jq`. Docker is needed only for the local stack.

## 1. Install the CLI

Sign in at `https://agentengine.mongodb.com`, open `https://agentengine.mongodb.com/download-cli`, download the binary for your platform and note the SHA-256 shown.

```bash
shasum -a 256 agentengine          # must match the value on the download page
chmod +x agentengine
mkdir -p ~/.local/bin && mv agentengine ~/.local/bin/agentengine
agentengine version
```

## 2. IP access list

Memory reaches your cluster from the Agent Engine network. In Atlas, Security > Database & Network Access > IP Access List, add both entries and wait until both are active:

| CIDR | Description |
| --- | --- |
| `44.214.209.237/32` | Atlas Agent Engine Atlas access |
| `52.44.27.64/32` | Atlas Agent Engine Atlas access |

Skipping this leaves memory stuck at the `orchestration_engine` status. The docs say not to add `0.0.0.0/0`. (DxP's own backend on Modal still needs its own access rule for `MONGODB_URI`; that is a separate matter.)

## 3. Sign in and create a context

```bash
export PLATFORM_URL='https://agentengine.mongodb.com'
export ORG_ID='<atlas-organization-id>'
export PROJECT_ID='<atlas-project-id>'
export MEMORY_CONTEXT='dxp'

agentengine auth login --base-url "$PLATFORM_URL"
agentengine project list --org-id "$ORG_ID" --base-url "$PLATFORM_URL"
agentengine context create "$MEMORY_CONTEXT" --org-id "$ORG_ID" --project-id "$PROJECT_ID" --base-url "$PLATFORM_URL"
```

## 4. Scaffold the memory-only project

```bash
agentengine create --memory-only --name "DxP" --llm anthropic --yes
```

This writes a directory containing only `project-config.yaml`. Its `memory:` block should look like this. For DxP, keep background extraction to the types you want filled automatically; direct `save_*` writes work for every type regardless of this list.

```yaml
memory_only: true

memory:
  voyage:
    model: "voyage-4-large"
    dimension: 1024

  extraction_llm:
    provider: anthropic
    api_key_secret: LLM_API_KEY

  background_extraction:
    snapshot:
      max_messages: 20
      stale_minutes: 1

  extraction:
    enabled:
      - semantic
      - episodic
```

Notes:
- `extraction.enabled: []` extracts nothing. Removing the `enabled` line entirely re-enables **all** types (valid values listed in the docs: semantic, episodic, taxonomic, entity, preferences, procedural).
- The memory server needs both the Voyage key and an LLM key to become ready, even with extraction off.
- Decide now whether you want `metadata_partition_key` entries or custom memory types: both are write-once. DxP does not need either.
- Embedding model or dimension changes later require re-embedding everything.

## 5. Upload project secrets

Each command prompts for the value. Do not pass values with `--value` or as an argument (deprecated; leaks to other processes). Use `--stdin` from a script.

```bash
agentengine secret set MONGODB_URI   --context "$MEMORY_CONTEXT" --project-scope
agentengine secret set VOYAGE_API_KEY --context "$MEMORY_CONTEXT" --project-scope
agentengine secret set LLM_API_KEY    --context "$MEMORY_CONTEXT" --project-scope
agentengine secret list --context "$MEMORY_CONTEXT" --project-scope
```

The LLM key must be uploaded under the name in `api_key_secret` (`LLM_API_KEY`), not `ANTHROPIC_API_KEY`.

## 6. Start memory and wait for ready

```bash
agentengine memory configure ./project-config.yaml --context "$MEMORY_CONTEXT"
agentengine memory apply --wait --context "$MEMORY_CONTEXT"      # waits up to 5 minutes
agentengine memory status --context "$MEMORY_CONTEXT"            # state: ready
```

On a new project the first `apply` can fail with `memory-server deployment not found` while provisioning continues in the background. Do not re-run `apply`; poll `status` every minute until `state` is `ready`. If `blocked_on` persists, that is a MongoDB Support matter: switch to the fallback.

In the UI, a memory-only project's memory appears on the project's Memory page under Manage, not under Workspaces.

## 7. Service account for the DxP backend

```bash
agentengine service-account create dxp-backend \
  --context "$MEMORY_CONTEXT" \
  --role PROJECT_OWNER \
  --enable-atlas-pairing
```

Save the client id (`ae_sa_id_...`) and client secret (`ae_sa_sk_...`) immediately; the secret is shown once and expires after 2,160 hours by default. Store them as `AGENTENGINE_SA_CLIENT_ID` and `AGENTENGINE_SA_CLIENT_SECRET` in the backend's secret store (Modal secret), never in the repo.

Token exchange, as the DxP client does it in code:

```bash
export ACCESS_TOKEN=$(curl --fail-with-body --silent --show-error \
  --user "$MEMORY_CLIENT_ID" \
  --data grant_type=client_credentials \
  "$PLATFORM_URL/api/v1/oauth/token" | jq -er .access_token)
```

The response is `{"access_token": "...", "token_type": "Bearer", "expires_in": 3600}`.

## 8. Smoke test

```python
import os, uuid
from agent_engine_sdk_memory import Memory, MemoryRequestContext

run = uuid.uuid4().hex
with Memory(
    base_url="https://agentengine.mongodb.com",
    project_id=os.environ["AGENTIC_MEMORY_PROJECT_ID"],
    service_account_token=os.environ["ACCESS_TOKEN"],
) as memory:
    chat = memory.bind(MemoryRequestContext(user_id=f"smoke-{run}", session_id=f"smoke-{run}"))
    chat.record_turn(role="user", content="My home airport is Boston Logan.")
    chat.record_turn(role="assistant", content="Understood, I noted your home airport as Boston Logan.")
    ctx = chat.build_context(query="What is my home airport?", enabled_sources={"stm"}, max_tokens=2048)
    assert "Boston Logan" in str(ctx.formatted_context)

    chat.save_taxonomic(domain="smoke", term="ctDNA", definition="Circulating tumour DNA.")
    print(chat.get_taxonomic_term("smoke", "ctDNA"))     # print once to learn the raw shape
    print(chat.list_domains())
```

## Changing configuration or rotating a key

```bash
agentengine memory configure ./project-config.yaml --context "$MEMORY_CONTEXT"
agentengine memory apply --wait --context "$MEMORY_CONTEXT"
agentengine secret set LLM_API_KEY --context "$MEMORY_CONTEXT" --project-scope --sync   # rotate a secret
```

`memory apply` does not reload secrets; `--sync` (or `agentengine secret sync`) does. A future release will remove `agentengine memory configure` in favour of the UI.

## Local stack (development without a paid cluster)

```bash
agentengine create --memory-only --name "DxP"
# .env in that directory: VOYAGE_API_KEY and, if extraction is enabled, ANTHROPIC_API_KEY
agentengine dev up          # starts mongodb, memory-server and oe containers; copy the oe URL it prints
agentengine dev status | logs | stop | clean
```

```python
memory = Memory(base_url="http://localhost:<oe-port>")   # no project_id, no token
```

Run `unset AGENTIC_MEMORY_PROJECT_ID` first, or every call fails with `MemoryRouteNotFoundError`. Custom memory types are not available locally. A Modal-hosted backend cannot reach this stack.

## Optional: memory as an MCP server for the coding agents

`https://agentengine.mongodb.com/api/v1/projects/<project_id>/mcp` over Streamable HTTP with `Authorization: Bearer <access-token>`. It exposes three tools only: `record_turn`, `build_context`, `search_memories`. The token expires hourly, so this is not worth wiring up for a six-hour build.
