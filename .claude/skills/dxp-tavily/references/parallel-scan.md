# Scanning many providers in parallel (FR-4)

Checked 12 November 2026 against the Search best-practices page and the `tavily-python` 0.8.5 source. `AsyncTavilyClient` has the same methods and arguments as `TavilyClient`, uses `httpx`, and has an async `close()`.

```python
import asyncio
import os
from tavily import AsyncTavilyClient

async def scan_all(jobs: list[dict], concurrency: int = 5) -> list[dict]:
    """jobs: [{"domain": ..., "query": ..., "window": {"start_date": ...} or {"end_date": ...}}]"""
    client = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    sem = asyncio.Semaphore(concurrency)

    async def one(job: dict) -> dict:
        async with sem:
            for attempt in range(4):
                try:
                    data = await client.search(
                        query=job["query"],
                        include_domains=[job["domain"]],
                        include_domains_mode="restrict",
                        search_depth="basic",
                        max_results=10,
                        include_raw_content="text",
                        include_published_date=True,
                        include_usage=True,
                        timeout=30,
                        **job["window"],
                    )
                    return {"job": job, "ok": True, "data": data}
                except Exception as exc:
                    if attempt == 3:
                        return {"job": job, "ok": False, "error": str(exc)}
                    await asyncio.sleep(2 ** attempt)

    try:
        return await asyncio.gather(*(one(j) for j in jobs))
    finally:
        await client.close()

# results = asyncio.run(scan_all(jobs))
```

## Notes

- Each result carries `ok`, so the progress count in FR-4 (processed and failed) comes straight from the list. Retry only the failed jobs.
- Turn each `data["results"]` entry into a Source item with the same code as `scan_provider` in SKILL.md, including the `host_allowed` check. For the Held-back window, add `filter_by_published_date=True` to the call.
- Sizing: concurrency = (requests per minute / 60) x average latency in seconds. Free plan: 100 a minute, so 5 at 3 seconds of latency. Paid plans: 1,000 a minute.
- The rate limit is per account and shared by every key in it. Two people running batches on one account share the 100.
- On 429 the API may send a `Retry-After` header with the wait in seconds. The SDK raises `UsageLimitExceededError` and does not expose the header, so the code above backs off 1, 2 and 4 seconds.
- Sum `data["usage"]["credits"]` across results to see what the batch cost.
- Estimate, using the 3 seconds of latency in Tavily's own example: 36 providers at concurrency 5 take about 25 seconds. Measure it once before the demo.
