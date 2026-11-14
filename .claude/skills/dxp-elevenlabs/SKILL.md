---
name: dxp-elevenlabs
description: ElevenLabs text to speech for the DxP alert audio briefing (FR-14), plus the ElevenAgents voice agent option for the ElevenLabs prize. Load when a task touches `elevenlabs`, `@elevenlabs/elevenlabs-js`, `@elevenlabs/react`, `ELEVENLABS_API_KEY`, `text_to_speech.convert`, `eleven_v4`, voice IDs, audio briefing, spoken alert, pronunciation of ctDNA/MRD/EGFR/NSCLC, or a conversational voice agent.
---

# ElevenLabs for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Event rule: everything in this skill is reference documentation. Do not copy code from it into the project; write new code during the event.
>
> Saturday scope is `_bmad-output/planning-artifacts/development-plan.md`. Baseline loading, PubMed, memory, Learned rules, Alerts, Tavily scans and the old three-minute recorded video (the 3-minute live demo is in scope) are deferred; ignore those parts of this skill.

## Verified

Checked 12 November 2026 against the official documentation.

- Python SDK `elevenlabs` 2.78.0 (PyPI, released 12 Nov 2026; Python >=3.8). A pre-release 3.0.0a1 exists: do not install it.
- TypeScript SDK `@elevenlabs/elevenlabs-js` 2.78.0 (Node >=18). Browser and React: `@elevenlabs/react` 1.22.0 (depends on `@elevenlabs/client` 1.36.0).
- REST: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` and `/stream`, header `xi-api-key`.
- Text to speech model IDs: `eleven_v4`, `eleven_v4_turbo`, `eleven_v3`, `eleven_multilingual_v2`, `eleven_flash_v2_5`, `eleven_flash_v2`.
- Pages: docs/overview/models, docs/eleven-api/quickstart, docs/api-reference/text-to-speech/convert, docs/eleven-api/guides/how-to/text-to-speech/streaming, docs/overview/capabilities/text-to-speech/best-practices, docs/eleven-api/resources/errors, elevenlabs.io/pricing, elevenlabs.io/pricing/api, elevenlabs.io/use-policy, help-centre pages on default voices, publishing and error 429. Full URLs under Links.
- MongoDB and Modal calls in the examples are the minimum needed. Follow the DxP MongoDB and Modal skills where they differ.

## Read this first

1. **The model line-up has changed.** `eleven_v4` is the flagship and the one the official quickstart uses. `eleven_turbo_v2_5` and `eleven_turbo_v2` are deprecated (use Flash). Always pass `model_id` explicitly: the API default is still `eleven_multilingual_v2`.
2. **Do not hard-code a well-known voice ID.** The old Default voices (George `JBFqnCBsd6RMkjVDRZzb`, Sarah, Adam and the rest, still used in the official samples) exist only on accounts created before March 2026 and are removed on 31 December 2026. List the voices the account really has (script under Setup) and put the chosen ID in `ELEVENLABS_VOICE_ID`.
3. **The free plan is a risk at a hackathon.** It has no commercial licence, requires attribution when the audio is published, cannot use Voice Library voices through the API, and its abuse detector disables free usage on shared or VPN IP addresses ("Unusual activity detected. Free Tier usage disabled"), which ElevenLabs says it cannot reverse. Paid plans are immune. Starter ($6 a month) removes all four problems. Tell the humans before the day.
4. **Eleven v4 and v3 do not support SSML.** `<break>` and `<phoneme>` tags do not work. Square brackets are read as audio tags (`[whispers]`) and text between two forward slashes is read as IPA. Strip both from briefing text.
5. **Product names moved.** "Conversational AI" is now ElevenAgents (`docs/eleven-agents`). The React hooks need a `ConversationProvider` ancestor. The npm package is `@elevenlabs/elevenlabs-js` with camelCase options (`modelId`, `outputFormat`); older guides import `elevenlabs` with snake_case.
6. The event page lists "Best Project Built with ElevenLabs: 3 months of ElevenLabs Scale Tier" and states **no judging criteria** for it (checked 12 Nov 2026).

## What DxP uses it for

- **FR-14** audio briefing on an Alert: one or two sentences on what changed for a Diagnostic and why it matters to the Team. Generated once, stored, replayed.
- **SM-6** the ElevenLabs prize: optional voice agent and other extras in `references/voice-agent.md`.
- Not used in the ingest fan-out (FR-4). Only Alerts get audio.
- PRD §5 and the ElevenLabs use policy agree: the briefing describes a change in the evidence. It gives no advice about a patient, diagnosis or treatment.

## Setup

```bash
pip install elevenlabs==2.78.0            # Python backend
npm install @elevenlabs/elevenlabs-js     # only if a Next.js route calls ElevenLabs directly
npm install @elevenlabs/react             # only for the voice agent
```

Environment variable names (values never go in code or the repository):

- `ELEVENLABS_API_KEY`: both SDKs read it by default. Server side only. Never prefix it `NEXT_PUBLIC_`.
- `ELEVENLABS_VOICE_ID`: chosen from the listing below.
- `ELEVENLABS_MODEL_ID`: optional, defaults to `eleven_v4` in the code below.
- `DXP_TTS_OFFLINE`: set to `1` during the recorded demo to forbid live calls (cache only).

Pick a voice once, by ear, and keep it for the whole build (the cache key includes it):

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs()  # reads ELEVENLABS_API_KEY
for v in client.voices.search().voices:
    print(v.voice_id, v.name, v.category, v.labels)
```

If the list is empty or every voice is refused on the free plan, create one in the dashboard with Voice Design or move to Starter. Which voices a new free account can use through the API is `UNVERIFIED`. The documentation names replacements for the retired voices, for example "Elara - Crisp Pro Narrator" `WQP7cQUF5aAS6Axh5yaa` and "Finley - Articulate Anchor" `fnYMz3F5gMEDGMWcH1ex`; whether a free API key may use them is `UNVERIFIED`.

## Core patterns

### Model choice

| Model ID | Use | Latency (median, model only) | Cost per 1K characters | Characters per request |
|---|---|---|---|---|
| `eleven_v4` | Default for the briefing: best quality, pre-generated and cached so latency does not matter | not published | $0.08 | 10,000 |
| `eleven_multilingual_v2` | Fallback if v4 sounds wrong: most stable, best at reading numbers | not published | $0.08 | 10,000 |
| `eleven_flash_v2_5` | Only if credits run short or audio must be live: half price, weak at numbers and dates | about 100 ms | $0.04 | 40,000 |
| `eleven_v4_turbo` | Real-time and voice agents | about 100 ms | $0.04 | not published |

Output format: `mp3_44100_128` (the default, allowed on every plan, plays in every browser's `<audio>` element). `mp3_44100_192` needs Creator or above; PCM and WAV at 44.1 kHz need Pro or above.

### 1. Generate once, cache in MongoDB, serve by key (Python, the simplest path)

Generate in the Python backend when the Alert is created. The MP3 for two sentences is about 150 to 250 KB, well inside a document. The cache key is a hash of everything that changes the audio, so a replayed demo or a re-run of the pipeline costs nothing.

```python
# briefing_audio.py
import hashlib
import os
import re
import time
from datetime import datetime, timezone

from elevenlabs.client import ElevenLabs
from elevenlabs.core import ApiError

MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_v4")
OUTPUT_FORMAT = "mp3_44100_128"
MAX_CHARS = 600  # a briefing is one or two sentences; refuse anything longer

# Spoken forms. Applied before the request, so they work on every model.
# Confirm each by ear with the chosen voice; add assay names as they appear.
SPOKEN = [
    (r"\bctDNA\b", "circulating tumour DNA"),
    (r"\bcfDNA\b", "cell-free DNA"),
    (r"\bNSCLC\b", "non-small cell lung cancer"),
    (r"\bSCLC\b", "small cell lung cancer"),
    (r"\bMRD\b", "M R D"),
    (r"\bEGFR\b", "E G F R"),
    (r"\bPD-L1\b", "P D L one"),
    (r"\bKRAS\b", "kay-rass"),
    (r"\bNGS\b", "N G S"),
    (r"\bCDx\b", "C D x"),
    (r"\bGuardant360\b", "Guardant three sixty"),
    (r"\bFoundationOne\b", "Foundation One"),
    (r"%", " percent"),
    (r"[\[\]]", ""),   # v4 and v3 read [..] as an audio tag
    (r"/", ", "),      # v4 reads /../ as IPA
]

_client = None


def _eleven() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    return _client


def to_spoken(text: str) -> str:
    for pattern, replacement in SPOKEN:
        text = re.sub(pattern, replacement, text)
    return re.sub(r"\s+", " ", text).strip()


def audio_key(spoken: str) -> str:
    voice_id = os.environ["ELEVENLABS_VOICE_ID"]
    raw = "|".join([MODEL_ID, voice_id, OUTPUT_FORMAT, spoken])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _synthesise(spoken: str) -> bytes:
    for attempt in range(4):
        try:
            chunks = _eleven().text_to_speech.convert(
                text=spoken,
                voice_id=os.environ["ELEVENLABS_VOICE_ID"],
                model_id=MODEL_ID,
                output_format=OUTPUT_FORMAT,
            )
            return b"".join(chunk for chunk in chunks if chunk)  # convert yields byte chunks
        except ApiError as err:
            if err.status_code in (429, 500, 503) and attempt < 3:
                time.sleep(2 ** attempt)
                continue
            raise
    raise RuntimeError("unreachable")


def get_or_create_briefing(coll, text: str) -> str:
    """Return the audio key for this briefing text, generating the MP3 only on a cache miss.

    `coll` is a PyMongo collection, for example db["audio_briefings"].
    Store the returned key on the Alert document as `audio_key`.
    """
    spoken = to_spoken(text)
    if not spoken or len(spoken) > MAX_CHARS:
        raise ValueError(f"briefing text must be 1 to {MAX_CHARS} characters")
    key = audio_key(spoken)
    if coll.find_one({"_id": key}, {"_id": 1}):
        return key
    if os.environ.get("DXP_TTS_OFFLINE") == "1":
        raise RuntimeError("TTS is offline and this text has no cached audio")
    audio = _synthesise(spoken)
    coll.update_one(
        {"_id": key},
        {"$set": {
            "audio": audio,
            "mime": "audio/mpeg",
            "text": text,
            "spoken": spoken,
            "model_id": MODEL_ID,
            "voice_id": os.environ["ELEVENLABS_VOICE_ID"],
            "characters": len(spoken),
            "created_at": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    return key
```

Serve it from the backend's FastAPI app:

```python
from fastapi import HTTPException, Response

@web_app.get("/audio/{key}")
def get_audio(key: str):
    doc = db["audio_briefings"].find_one({"_id": key})
    if doc is None:
        raise HTTPException(status_code=404, detail="no audio for this key")
    return Response(
        content=bytes(doc["audio"]),
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
```

On Modal, add `elevenlabs==2.78.0` to the image and attach the key as a secret (the secret name is a placeholder):

```python
image = modal.Image.debian_slim().pip_install("fastapi[standard]", "elevenlabs==2.78.0", "pymongo")

@app.function(image=image, secrets=[modal.Secret.from_name("dxp-elevenlabs")])
@modal.asgi_app()
def api():
    ...  # build and return web_app
```

Front end (Next.js). An `<audio>` element may load from another origin without CORS, and starts playing while the file is still arriving:

```tsx
"use client";

export function BriefingPlayer({ audioKey }: { audioKey?: string }) {
  if (!audioKey) return null; // an Alert "can" carry audio; absence is normal
  const src = `${process.env.NEXT_PUBLIC_DXP_API_URL}/audio/${audioKey}`; // use the project's backend URL variable
  return <audio controls preload="none" src={src} aria-label="Audio briefing (AI-generated voice)" />;
}
```

Browsers block `audio.play()` without a user gesture. Use the controls or a click handler; do not autoplay on page load.

### 2. Live streaming from a Next.js route (TypeScript)

Only if audio must be generated on request. It spends credits on every play. Complete route in `references/streaming-route.md`. The calls are `elevenlabs.textToSpeech.stream(voiceId, { text, modelId, outputFormat })` and `elevenlabs.textToSpeech.convert(voiceId, { ... })` on `new ElevenLabsClient()`.

### 3. Pronunciation

- Preferred: the `SPOKEN` table above. It is model-independent and costs nothing. Also tell Claude, in the prompt that writes the briefing, to write for the ear: no brackets, no slashes, no table fragments, numbers that read naturally ("91 percent").
- Pronunciation dictionaries (needed for the voice agent, where the LLM writes the text): alias rules work on every model; phoneme rules work only on `eleven_v4`, `eleven_v4_turbo`, `eleven_flash_v2` and `eleven_v3`. At most 3 dictionaries per request. Matching is case-sensitive. Code in `references/pronunciation-dictionary.md`.
- Inline `<phoneme>` SSML works only on `eleven_flash_v2`. On `eleven_v4`, IPA goes between forward slashes in the text and results vary by voice. Neither is worth the time on Saturday.

## Limits and costs

| | Free | Starter ($6/month) | Pro ($99) | Scale ($299) |
|---|---|---|---|---|
| Monthly credits (plans page) | about 10,000 | 30,000 | 600,000 | 1,800,000 |
| Concurrent requests: v4, v3, Multilingual v2 | 2 | 3 | 10 | 15 |
| Concurrent requests: Flash | 4 | 6 | 20 | 30 |
| Commercial licence | no | yes | yes | yes |
| Attribution when published | required | not required | not required | not required |

- One character is one credit on `eleven_v4`, `eleven_v3` and `eleven_multilingual_v2`; Flash and v4 Turbo cost half. A 250-character briefing uses about 250 credits ($0.02 at API rates). Free covers roughly 40 uncached briefings a month, so develop against the cache.
- The API pricing page quotes dollars ($0.08 or $0.04 per 1K characters) and the plans page quotes credits. The two do not obviously reconcile for Starter. Read the remaining balance in the dashboard, not from arithmetic.
- No requests-per-minute figure is published. The enforced limit is concurrency. Run briefing generation with at most 2 parallel calls.
- 429 codes: `concurrent_limit_exceeded` (the help centre calls it `too_many_concurrent_requests`), `rate_limit_exceeded`, `system_busy`. Retry with backoff. 402 `insufficient_credits` means the balance is gone: do not retry.
- Voices with a credit multiplier cost more per character. Check the voice before choosing it.
- Voice agents are billed by the minute. The API pricing page lists about 14 included minutes on Free for Realtime v1 Mini, and 4 concurrent calls. Billing for a classic (speech to text, LLM, text to speech) agent was not checked: `UNVERIFIED`.

## Gotchas

- Catch `ApiError` from `elevenlabs.core` (Python: `status_code`, `body`) and `ElevenLabsError` from `@elevenlabs/elevenlabs-js` (`statusCode`, `body`). The error body is `detail.type`, `detail.code`, `detail.message`, `detail.request_id`.
- `convert` in Python returns an iterator of byte chunks, and the HTTP request is made when it is consumed. Keep the `b"".join(...)` inside the `try`.
- 403 `voice_access_denied`, `model_access_denied` or `subscription_required` means the plan cannot use that voice or model. Change `ELEVENLABS_VOICE_ID` or `ELEVENLABS_MODEL_ID`; do not retry.
- `language_code` is not supported by `eleven_multilingual_v2`. Leave it out.
- `eleven_v4` has no Speed or Style setting and its documentation says behaviour may shift as training continues. Generate the demo audio before recording, then set `DXP_TTS_OFFLINE=1`.
- `seed` gives best-effort repeatability only. The cache is what makes replays identical.
- `optimize_streaming_latency` is deprecated. Do not use it.
- The Python `play()` and `stream()` helpers need MPV or ffmpeg on the machine. Do not call them in the backend.
- All generated audio carries an inaudible watermark. The use policy forbids removing it.

## Fallback

1. Before the demo, generate audio for every Alert the demo shows, confirm each `audio_key` resolves, and set `DXP_TTS_OFFLINE=1`. The demo then needs no call to ElevenLabs.
2. If the API fails on the day (credits, abuse flag, outage): generate the same sentences in the ElevenLabs web app, download the MP3s, and insert them into `audio_briefings` under the keys `audio_key(to_spoken(text))` returns. The player does not change.
3. If there is no audio at all: FR-14 says an Alert *can* carry audio. Hide the player and keep the one-line "why it matters" text. Say in the video that audio is generated with ElevenLabs only if it really is on screen.

## Prize and disclosure

- Options that strengthen the ElevenLabs entry, with effort, are in `references/voice-agent.md`. The strongest is a voice agent that answers questions about the open Diagnostic from its MongoDB Record (60 to 90 minutes).
- Disclosure for the public video: label the voice. Put "AI-generated voice (ElevenLabs)" on screen where the briefing plays and in the description. The use policy (updated 9 October 2026) requires clear disclosure when people interact with AI where silence would materially mislead, and forbids removing watermarks. On the free plan, published audio must also carry "elevenlabs.io" or "11.ai" in the title and may not be used commercially. Do not clone any real person's voice without their explicit consent. YouTube requires its "AI use" disclosure for realistic synthetic content that makes a real person appear to say something; a stock synthetic voice reading the team's own script is not among its required cases, but labelling costs nothing.

## Links

- Models, limits per model, concurrency table: https://elevenlabs.io/docs/overview/models
- Quickstart (Python, TypeScript): https://elevenlabs.io/docs/eleven-api/quickstart
- Create speech API reference: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
- Streaming guide with file and in-memory examples: https://elevenlabs.io/docs/eleven-api/guides/how-to/text-to-speech/streaming
- Best practices (pronunciation, normalisation, v4 tags): https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices
- Eleven v4 notes: https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4
- Errors: https://elevenlabs.io/docs/eleven-api/resources/errors
- Pricing: https://elevenlabs.io/pricing and https://elevenlabs.io/pricing/api
- Default voices retirement: https://elevenlabs.io/docs/help-center/product/voices/my-voices/what-are-default-voices
- Publishing and attribution: https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform
- Free tier abuse flag: https://elevenlabs.io/docs/help-center/account/general/what-does-unusual-activity-detected-free-tier-usage-disabled-if-you-are-using-proxy-vpn-you-might-need-to-purchase-a-paid-plan-to-not-trigger-our-abuse-detectors-mean
- Use policy: https://elevenlabs.io/use-policy
- Documentation index for agents: https://elevenlabs.io/docs/llms.txt
- Event page: https://cerebralvalley.ai/e/mongodb-toronto-hackathon
