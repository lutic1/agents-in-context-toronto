# Tavily Map and Crawl

Checked 12 November 2026 against the Crawl and Map API references and the `tavily-python` 0.8.5 source. DxP's default is one search per provider (pattern 2 in SKILL.md), which costs far less. Use map or crawl only when a provider's site has to be walked page by page.

## Calls

```python
import os
from tavily import TavilyClient

client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

site_map = client.map(
    "https://example-provider.com",
    max_depth=2,
    limit=50,
    select_paths=[r"/products/.*", r"/news/.*"],   # regex
    allow_external=False,
    include_usage=True,
)
urls = site_map["results"]                         # list[str]

crawl = client.crawl(
    "https://example-provider.com",
    max_depth=1,
    limit=20,
    select_paths=[r"/products/.*"],
    allow_external=False,
    extract_depth="basic",
    format="text",
    include_usage=True,
)
pages = crawl["results"]                           # each: {"url", "raw_content"}
```

The method is `map`. The `client.mapping(...)` call shown in the SDK reference does not exist in 0.8.5.

## Parameters (both calls unless noted)

| Parameter | Default | Notes |
| - | - | - |
| `url` | required | Root URL |
| `max_depth` | 1 | 1 to 5 |
| `max_breadth` | 20 | Links followed per page, 1 to 500 |
| `limit` | 50 | Total links processed |
| `instructions` | none | Natural language; doubles the mapping cost |
| `select_paths`, `exclude_paths` | none | Regex on the path |
| `select_domains`, `exclude_domains` | none | Regex on the host, for example `^docs\.example\.com$` |
| `allow_external` | `True` | Set `False` so the walk stays on the provider's domain |
| `timeout` | 150 | Seconds, 10 to 150 |
| `extract_depth`, `format` | `basic`, `markdown` | Crawl only |
| `chunks_per_source` | 3 | Crawl only, and only with `instructions`; returns chunks, not full text |
| `include_usage` | `False` | Adds `usage.credits` to the response |

## Costs and limits

- Map: 1 credit per 10 pages returned, 2 with `instructions`. A failed request is free.
- Crawl: the map cost plus the extract cost. Ten pages cost 3 credits at basic depth and 5 at advanced.
- 100 requests a minute for each of `/crawl` and `/map`, on every plan.
- Both need an API key. Keyless mode raises `KeylessUnsupportedEndpointError`.
- Both are synchronous and can take the full 150 seconds. Do not call them inside the three-minute demo.

## Rules for DxP

- Check every returned URL with `host_allowed` before storing or extracting it. `allow_external=True` returns links to other sites.
- `select_domains` and `exclude_domains` are regex here. In search, `include_domains` and `exclude_domains` are plain domain names. Do not copy a list from one call to the other.
- With `instructions`, crawl returns ranked chunks joined by `[...]`. That text cannot serve as a Source item for the word-for-word quote check. Leave `instructions` out when the page text will be stored.
- The cheapest walk: `map` to list URLs, filter them in code, then `extract` the few that matter (pattern 3).
