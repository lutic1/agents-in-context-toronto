---
name: dxp-tavily
description: Tavily web search, extract, crawl and map for DxP's provider-website scans and discovery. Load when a task touches `tavily-python`, `TavilyClient`, `AsyncTavilyClient`, `langchain-tavily`, `TavilySearch`, `TavilyExtract`, `TAVILY_API_KEY`, `include_domains`, `start_date`, `raw_content`, web search, provider websites, or the Held-back set for web sources.
---

# Tavily for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Read its Precedence paragraph before copying an example from here.

## Verified

Checked 12 November 2026 against the pages in Links.

- `tavily-python` 0.8.5 (PyPI, released 6 October 2026; Python >= 3.8). Signatures read from the SDK source at that version.
- `langchain-tavily` 0.2.18 (PyPI, released 16 April 2026; Python >= 3.10, `langchain-core` >= 1.2.11, `langchain` >= 1.0.0).
- REST base URL `https://api.tavily.com`, endpoints `/search`, `/extract`, `/crawl`, `/map`, `/research`, `/usage`.
- Platform Terms of Service last updated 4 May 2026; Acceptable Use Policy last updated 21 October 2026.

## Read this first

1. **Tavily does not enforce "open data only".** Nothing in the docs or terms says it skips paywalled or licensed pages, the terms disclaim that returned content is non-infringing, and the crawl guide leaves robots.txt to the caller. DxP must enforce the rule itself with an allow-list of approved provider domains, checked in code on every URL (pattern 1).
2. **Do not route ClinicalTrials.gov, PubMed or FDA data through Tavily.** Those come from their own APIs, covered by other skills. Tavily is for provider websites and for discovering providers.
3. **`days` is gone from the API reference.** It survives only as an argument in the Python SDK. Use `start_date` and `end_date` (`YYYY-MM-DD`). `time_range="month"` is a calendar month back, not four weeks.
4. **Published dates are weak on provider websites.** Date filters match a page's publish date. Pages with no detectable date are kept unless `filter_by_published_date=True`, which then drops all of them. `published_date` is in beta and is "Tavily's best estimate of when the source was published or last updated". For FR-30, take the Held-back set mainly from the registry, literature and FDA sources, which carry authoritative dates. From Tavily, only pages with a detected date inside the window qualify.
5. **`topic="news"` is for mainstream media.** Keep `topic="general"` for provider websites.
6. **`raw_content` is cleaned text, not the page's HTML, and may come from Tavily's cache.** The FR-18 word-for-word check must run against the text DxP stored at fetch time, not against a fresh fetch.
7. **A missing key does not raise.** `TavilyClient()` with no key and no `TAVILY_API_KEY` silently switches to keyless mode, which is rate-limited and supports only search and extract. Read the key with `os.environ[...]` so that a missing key fails at start-up.
8. **The docs example `client.mapping(...)` is wrong.** The SDK method is `client.map(...)`.
9. **`langchain-tavily` is seven months behind the API.** Its `TavilySearch` has no `include_domains_mode`, `max_age_hours`, `language` or published-date fields. Use the Python SDK directly for the scheduled scan; use the LangChain tool only where an LLM chooses the query.

## What DxP uses it for

- FR-1: the scheduled and manual scan of provider websites (one of four approved Source types).
- FR-2 and the "open data only" constraint: results restricted to approved provider domains.
- FR-30: date windows for the Baseline load and the Held-back set, for web sources only.
- FR-5, FR-7, FR-18: the full page text and URL stored as the Source item that every quote is checked against.
- FR-4: provider pages fetched in parallel within the rate limit.
- Discovery of providers not yet on the allow-list. A discovered domain yields no Findings until someone adds it to the allow-list.

## Setup

```bash
pip install "tavily-python==0.8.5" "langchain-tavily==0.2.18"
```

- Python 3.10 or later (`langchain-tavily` requires it, and the code below uses `X | None`).
- Environment variable: `TAVILY_API_KEY` (read by both packages). Optional: `TAVILY_PROJECT` tags usage by project.
- Free "Researcher" plan: 1,000 credits a month, no card. Credits reset on the first day of each month.
- Check remaining credits before the demo: `GET https://api.tavily.com/usage` with `Authorization: Bearer <key>` returns `account.plan_usage` and `account.plan_limit`. That endpoint allows 10 requests per 10 minutes.

## Core patterns

### 1. Client and the allow-list (FR-2, open data only)

```python
import os
from urllib.parse import urlsplit
from tavily import TavilyClient

# Approved provider domains. Load from MongoDB in the real build.
APPROVED_PROVIDER_DOMAINS: set[str] = {"example-provider.com"}

def tavily_client() -> TavilyClient:
    return TavilyClient(api_key=os.environ["TAVILY_API_KEY"], project_id="dxp")

def host_allowed(url: str, allowed: set[str] = APPROVED_PROVIDER_DOMAINS) -> bool:
    host = (urlsplit(url).hostname or "").lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in allowed)
```

`include_domains` rules: maximum 300 entries (`exclude_domains` 150). The default `include_domains_mode="restrict"` is a hard filter. A domain matches itself and all subdomains; a subdomain matches only that host. Plain domains only: no wildcards, regex or paths. Extract has no domain filter at all, so call `host_allowed` before every extract and on every search result.

### 2. Scan one provider, with the Baseline or Held-back window (FR-1, FR-30)

```python
import hashlib
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

HELD_BACK_DAYS = 28

def date_window(kind: str, today: date | None = None) -> dict:
    cutoff = ((today or date.today()) - timedelta(days=HELD_BACK_DAYS)).isoformat()
    return {"end_date": cutoff} if kind == "baseline" else {"start_date": cutoff}

def _parse_date(value: str | None) -> datetime | None:
    try:
        return parsedate_to_datetime(value) if value else None
    except (TypeError, ValueError):
        return None

def scan_provider(client: TavilyClient, domain: str, query: str, kind: str) -> list[dict]:
    """kind is "baseline" or "held_back". Returns Source items ready to store."""
    resp = client.search(
        query=query,                      # keep under 1,500 characters
        search_depth="basic",             # 1 credit; "advanced" costs 2
        topic="general",
        max_results=10,                   # maximum 20
        include_domains=[domain],
        include_domains_mode="restrict",
        include_raw_content="text",       # full cleaned page text, no extra credits
        include_published_date=True,      # beta; reaches the API through **kwargs
        filter_by_published_date=(kind == "held_back"),  # drops undated pages
        include_usage=True,
        timeout=30,
        **date_window(kind),
    )
    items = []
    for r in resp["results"]:
        text = r.get("raw_content")
        if not text or not host_allowed(r["url"]):
            continue                      # no text: fetch it with pattern 3
        published = _parse_date(r.get("published_date"))
        items.append({
            "source_type": "provider_website",
            "url": r["url"],
            "title": r.get("title"),
            "text": text,
            "text_format": "text",
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "published_date": published,
            "published_date_origin": "tavily_estimate" if published else None,
            "fetched_at": datetime.now(timezone.utc),
            "fetched_via": "tavily.search",
            "tavily_request_id": resp.get("request_id"),
        })
    return items
```

Undated pages land in the Baseline load and never in the Held-back set. Have the extraction agent confirm the date from the page text before a web page produces an Alert. Deduplicate by URL across the two windows: whether the boundary dates are inclusive is UNVERIFIED.

### 3. Full text for known URLs (FR-5, FR-18)

```python
def extract_pages(client: TavilyClient, urls: list[str]) -> tuple[list[dict], list[dict]]:
    urls = [u for u in dict.fromkeys(urls) if host_allowed(u)]
    ok, failed = [], []
    for i in range(0, len(urls), 20):     # hard limit: 20 URLs per request
        resp = client.extract(urls=urls[i:i + 20], extract_depth="basic",
                              format="text", include_usage=True)
        ok += resp["results"]             # each: {"url", "raw_content"}
        failed += resp["failed_results"]  # each: {"url", "error"}; HTTP is still 200
    return ok, failed
```

Retry `failed` once with `extract_depth="advanced"` (tables, JavaScript-rendered pages; twice the cost). Never pass `query` or `chunks_per_source` here: they replace the full text with a few chunks joined by `[...]`. For the same reason, never treat a search result's `content` field as the Source item; it is snippets.

### 4. The word-for-word quote check (FR-18)

```python
import re
import unicodedata

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip()

def quote_in_source(quote: str, source_text: str) -> bool:
    q = _norm(quote)
    return bool(q) and q in _norm(source_text)
```

Run it against the stored `text` of the Source item. Store the text once, with its hash and `fetched_at`, and never overwrite it; a changed page becomes a new Source item. Give the extraction model the same stored text it will be checked against.

### 5. Many providers in parallel (FR-4)

Use `AsyncTavilyClient` (same method names and arguments, awaited) behind an `asyncio.Semaphore`, with a retry and backoff per job so that one 429 does not sink the batch. The complete `scan_all` function is in `references/parallel-scan.md`. Tavily's sizing rule: concurrency = (requests per minute / 60) x average latency in seconds. At 100 a minute and 3 seconds, that is 5.

### 6. An LLM-driven search tool (LangChain and LangGraph)

```python
from langchain.agents import create_agent
from langchain_tavily import TavilySearch

provider_search = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="basic",
    include_domains=sorted(APPROVED_PROVIDER_DOMAINS),
    include_raw_content=False,   # can only be set here, not at invocation
)
# model: a chat model instance, as set up in the Claude skill
agent = create_agent(model, tools=[provider_search],
                     system_prompt="Search approved provider websites only.")
```

The tool's name is `tavily_search`. It returns the API's response as a dict, and it returns an error message instead of raising when a search finds nothing. The other classes are `TavilyExtract`, `TavilyCrawl`, `TavilyMap`, `TavilyResearch` and `TavilyGetResearch`. In a LangGraph node that needs no model decision, call the SDK functions from patterns 2 and 3 directly.

### 7. Discovery of new providers

Search without `include_domains`, with `search_depth="advanced"` and `exclude_domains=["clinicaltrials.gov", "ncbi.nlm.nih.gov", "fda.gov"]`. Store only the candidate domain and URL. Ingest nothing until the domain is on the allow-list.

### Map and crawl

`client.map(url)` lists a site's URLs and `client.crawl(url)` returns the text of each page. They cost more than pattern 2, take up to 150 seconds, and their domain and path filters are regex patterns, unlike search. Read `references/map-and-crawl.md` before using either.

## Limits and costs

| Call | Credits |
| - | - |
| Search `basic`, `fast`, `ultra-fast` | 1 per request, raw content included |
| Search `advanced`, or `auto_parameters=True` | 2 per request |
| Extract `basic` / `advanced` | 1 / 2 per 5 successful URLs; failures are free |
| Map | 1 per 10 pages; 2 with `instructions` |
| Crawl | map cost plus extract cost: 3 per 10 pages basic, 5 advanced |
| Research | 4 to 110 (`mini`) or 15 to 250 (`pro`) per request: do not use |

- Plans: free 1,000 credits a month; pay-as-you-go $0.008 a credit; Project $30 for 4,000.
- Rate limits, per account and shared by all its keys since November 2026: free 100 requests a minute; paid 1,000 or more. `/crawl` and `/map` 100 a minute, `/research` 20, on every plan.
- Timeouts: SDK search 60 seconds by default; extract 30 (API range 1 to 60); crawl and map 10 to 150.
- Estimate for one scan of 36 provider websites:

| Approach | Credits per scan | Scans on the free plan |
| - | - | - |
| One basic search per provider with raw content (pattern 2) | 36 | 27 |
| Same, `advanced` | 72 | 13 |
| Baseline and Held-back windows, basic (two searches each) | 72 | 13 |
| Map 50 pages, then extract 10 pages per site | 252 | 3 |
| Crawl 50 pages per site, basic | 540 | 1 |

Use pattern 2. Development and testing draw on the same 1,000 credits, so cache responses while building. Each developer's own free account has its own credits and rate limit.

## Gotchas

- Errors: 429 raises `UsageLimitExceededError` (honour `Retry-After`); 432 (plan limit) and 433 (pay-as-you-go limit) raise `tavily.errors.ForbiddenError`; 401 `InvalidAPIKeyError`; 400 `BadRequestError`; a timeout raises `tavily.errors.TimeoutError`, not the built-in. Anything else is a `requests` or `httpx` HTTP error.
- `max_age_hours` (freshness of Tavily's cached copy; 0 forces a live fetch) is best-effort on the free plan and can return `434 Flex tier capacity exceeded`. Leave it unset during the demo.
- `include_domains_mode` without `include_domains` returns 400. `"prefer"` lets other domains through: never use it for ingestion.
- Results can be fewer than `max_results`, and a restricted search can return none. An empty list is not an error in the SDK.
- `include_answer` is an LLM summary with no quote. It cannot be Evidence.
- `max_results` defaults to 10 in the API and 5 in `TavilySearch`.
- The best-practices page still shows `include_domains` with a path (`linkedin.com/in`) and a wildcard (`*.com`). The August 2026 changelog says neither is supported. Use plain domains.
- `langchain-tavily`: both official pages say an argument passed at invocation overrides the one set at instantiation; the source does the opposite for `include_domains`. Do not depend on either. Filter every result with `host_allowed`.
- `langchain_community.tools.tavily_search` is deprecated. Use `langchain-tavily`.
- Terms: Tavily's terms neither restrict nor permit storing returned content, grant no rights in third-party pages, and let Tavily retain queries. Put nothing confidential in a query. Details in `references/terms-and-open-data.md`.
- UNVERIFIED: whether the API still honours `days`; whether `start_date` and `end_date` are inclusive; any size cap on `raw_content` (none is documented); whether Extract returns the final URL after a redirect, serves from cache, or honours robots.txt; keyless rate limits; whether `TavilySearch` passes extra keyword arguments such as `include_domains_mode` through at invocation.

## Fallback

1. Out of credits (432): switch to the other developer's key, or enable pay-as-you-go ($8 per 1,000 credits).
2. No working key: keyless mode. `TavilyClient()` with `TAVILY_API_KEY` unset still runs search and extract, at a lower, unpublished rate limit.
3. Tavily down or slow: read provider pages from the Source items already stored in MongoDB. Fetch and store them before the demo, and disclose that as prepared data under the event rules. The FR-18 check runs on stored text, so it is unaffected.
4. The Held-back demo does not depend on Tavily if the registry, literature and FDA sources supply the dated updates.

## Links

Every docs page is also served as Markdown: append `.md` to its URL. The index is https://docs.tavily.com/llms.txt.

- Search API reference: https://docs.tavily.com/documentation/api-reference/endpoint/search.md
- Python SDK reference: https://docs.tavily.com/sdk/python/reference.md
- Extract API reference: https://docs.tavily.com/documentation/api-reference/endpoint/extract.md
- Credits and pricing: https://docs.tavily.com/documentation/api-credits.md
- Rate limits: https://docs.tavily.com/documentation/rate-limits.md
- Search best practices (dates, domains, batching): https://docs.tavily.com/documentation/best-practices/best-practices-search.md
- Changelog: https://docs.tavily.com/changelog.md
- LangChain integration: https://docs.tavily.com/documentation/integrations/langchain.md
- Usage endpoint: https://docs.tavily.com/documentation/api-reference/endpoint/usage.md
- Keyless access: https://docs.tavily.com/documentation/keyless.md
- PyPI: https://pypi.org/project/tavily-python/ and https://pypi.org/project/langchain-tavily/
- SDK source: https://github.com/tavily-ai/tavily-python and https://github.com/tavily-ai/langchain-tavily
