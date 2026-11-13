---
name: dxp-heygen
description: Produce the two short HeyGen presenter clips (intro and close) for the DxP three-minute demo video, through the HeyGen web app or the HeyGen API v3. Load when a task mentions HeyGen, avatar video, talking presenter, HEYGEN_API_KEY, api.heygen.com, /v3/videos, or the demo video intro and close.
---

# HeyGen for DxP

> **Architecture precedence.** `_bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md` overrides this skill wherever the two differ: collection names, ID formats, the review queue, how a batch runs, live updates and environment variable names. Read its Precedence paragraph before copying an example from here.

## Verified
Checked 12 November 2026 against official pages only. API **v3**, base URL `https://api.heygen.com`, auth header `X-Api-Key`. No SDK: the docs use plain HTTP. Pages: developers.heygen.com (`docs/quick-start`, `docs/api-key`, `endpoint-version-comparison`, `generate-avatar-video`, `models`, `docs/usage-limits`, `docs/error-codes`, `docs/for-ai-agents`, `reference/create-video`, `reference/get-video`, `reference/list-avatar-looks`, `reference/list-audio-voices`); heygen.com (`pricing`, `faq`, `moderation-policy`, `terms` last updated 16 Oct 2026); help.heygen.com articles 10060327 (API pricing), 15126059 (credits), 15125761 (plans), 9655503 (processing times), 12903996 (Quick Avatar Video), 11381771 (scripts), 11395771 (EU AI Act).

## Read this first
- **API v1 and v2 are gone.** They passed their sunset on 31 October 2026 and are being removed. Code from memory (`POST /v2/video/generate`, `GET /v1/video_status.get`, `GET /v2/avatars`, `GET /v2/voices`) fails or fails intermittently. Use only the v3 calls below.
- **The Free plan cannot be used for this video.** Free output is watermarked, limited to 3 videos a month (1 to 3 by region), 1 minute each, 720p, 1 render at a time at "Standard" speed, and the terms license it only for "personal, non-commercial, and internal evaluation purposes" and forbid redistribution. A public submission needs Creator (US$29 a month; paid plans own their output and may use it commercially) or a funded API wallet (from US$5).
- **There are no free API credits** (ended February 2026). API credits are a separate pay-as-you-go wallet; web plan credits do not pay for API-key calls.
- **Do not plan to render in the final hour.** The API docs say most videos finish in 1 to 5 minutes and the help centre says about 10 minutes per minute of video, "often much faster". The same help page says the regular queue averages "just under 24h" on weekdays (faster at weekends) and that higher tiers get priority. Both scripts are known in advance, so render both clips on Saturday morning and keep the MP4s. Use the last hour only for a re-render, with the fallback ready.
- HeyGen is outside the product. Nothing in the app, the agents or the data path may call it.

## What DxP uses it for
- No FR. It serves the submission: SM-1 (three-minute video) and SM-7 (the video opens with the one-line novelty claim from PRD §1).
- PRD §8 still applies: the avatar only opens and closes. It never stands in for the live memory write and read or the live Learned rule.

## Setup
Pick one route before Saturday and test it once end to end.
- **Web app, Quick Avatar Video** (default): needs a Creator plan and a browser. No code; avatar and voice are chosen by eye and ear.
- **API v3 script**: needs an API wallet of at least US$5 and `HEYGEN_API_KEY`. Use it only if the script has already produced one clip.
- API key: create at `https://platform.heygen.com/api-keys`, then `export HEYGEN_API_KEY=...` in the shell. Never paste it into chat or commit it.
- Script-local variables (not HeyGen names): `HEYGEN_AVATAR_ID` (a look `id`), optional `HEYGEN_VOICE_ID`, optional `HEYGEN_ENGINE` (`avatar_iii` or `avatar_iv`; must appear in the look's `supported_api_engines`). Install: `pip install requests`.

## Core patterns

### Web route (five minutes of clicking plus render time)
1. Apps → All Apps → Quick Avatar Video.
2. Choose an avatar under Public Avatars. Orientation: Landscape (16:9).
3. Add Script: paste the intro script with the respellings below already typed in (limit 2,520 characters).
4. Select a voice and play the preview.
5. Motion engine: Avatar III (lip-sync only, fastest, cheapest) or Avatar IV Digital Twin (gestures, about 8 times the credits).
6. Resolution 1080p → Generate Video. Repeat for the close with the same avatar and voice. Download both MP4s as soon as they complete (exact download control UNVERIFIED).

### API route
`python heygen_clips.py list` prints the balance, public avatars and English voices (no avatars: drop `avatar_type`; more pages: pass the response's `next_token` as `token`). Set `HEYGEN_AVATAR_ID`, then `python heygen_clips.py render` writes `intro.mp4` and `close.mp4`.

```python
"""DxP demo clips with the HeyGen API v3. Usage: python heygen_clips.py list | render"""
import os, sys, time, requests
BASE = "https://api.heygen.com"
H = {"X-Api-Key": os.environ["HEYGEN_API_KEY"]}
# Respellings typed into the script text. Order matters: DxProvida before DxP.
SAY = {"ctDNA": "see-tee-dee-en-ay", "MRD": "em-ar-dee",
       "DxProvida": "dee-ex pro-vee-da", "DxP": "dee-ex-pee"}
# Drafts (about 15 s and 10 s). The team confirms the wording against PRD sections 1 and 8.
CLIPS = {
    "intro": "This is DxProvida, an evidence analyst whose guardrails are written by its "
             "Reviewers. One rejection, with a reason, becomes a rule the agents follow from "
             "then on, and DxProvida remembers every Team between visits.",
    "close": "DxProvida: evidence on every value, guardrails written by its reviewers, and "
             "memory for every team, all on MongoDB Atlas. Thank you.",
}

def get(path, **params):
    r = requests.get(f"{BASE}{path}", headers=H, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def list_options():
    me = get("/v3/users/me")["data"]
    print("billing:", me["billing_type"], me.get(me["billing_type"]))
    for a in get("/v3/avatars/looks", avatar_type="studio_avatar", ownership="public", limit=50)["data"]:
        print("avatar", a["id"], a["name"], a.get("supported_api_engines"), a.get("preview_video_url"))
    for v in get("/v3/models/audio/voices", type="public", language="en", limit=50)["data"]:
        print("voice", v["voice_id"], v["name"], v.get("gender"), v.get("preview_audio_url"))

def submit(name, script):
    for term, said in SAY.items():
        script = script.replace(term, said)
    body = {"type": "avatar", "avatar_id": os.environ["HEYGEN_AVATAR_ID"], "script": script,
            "title": f"dxp-{name}", "resolution": "1080p", "aspect_ratio": "16:9"}
    if os.environ.get("HEYGEN_VOICE_ID"):   # omitted: the look's default voice
        body["voice_id"] = os.environ["HEYGEN_VOICE_ID"]
    if os.environ.get("HEYGEN_ENGINE"):     # omitted: avatar_iv; avatar_iii is cheaper
        body["engine"] = {"type": os.environ["HEYGEN_ENGINE"]}
    r = requests.post(f"{BASE}/v3/videos", headers=H, json=body, timeout=60)
    if not r.ok:
        sys.exit(f"{name}: HTTP {r.status_code} {r.text}")
    return r.json()["data"]["video_id"]

def wait_and_download(name, video_id, deadline):
    status = "unknown"
    while time.time() < deadline:
        v = get(f"/v3/videos/{video_id}")["data"]
        status = v["status"]                # pending | processing | completed | failed
        if status == "completed":
            with requests.get(v["video_url"], stream=True, timeout=120) as d:
                d.raise_for_status()
                with open(f"{name}.mp4", "wb") as f:
                    for chunk in d.iter_content(1 << 20):
                        f.write(chunk)
            print(f"{name}.mp4 saved, {v.get('duration')} s")
            return True
        if status == "failed":
            print(f"{name} FAILED: {v.get('failure_code')} {v.get('failure_message')}")
            return False
        time.sleep(10)
    print(f"{name} still {status} (video_id {video_id}). Switch to the fallback.")
    return False

if __name__ == "__main__":
    if sys.argv[1:] == ["list"]:
        list_options()
    elif sys.argv[1:] == ["render"]:
        ids = {name: submit(name, script) for name, script in CLIPS.items()}
        deadline = time.time() + 600
        sys.exit(0 if all([wait_and_download(n, i, deadline) for n, i in ids.items()]) else 1)
    else:
        sys.exit(__doc__)
```

### Script length and pronunciation
- HeyGen's own figures: about 2.5 words per second, or 14 characters per second (2,520 characters ≈ 3 minutes). Intro of 15 to 20 seconds: 38 to 50 words. Close of 10 to 15 seconds: 25 to 38 words. The finished video reports its real `duration`; trim in the editor instead of re-rendering. `voice_settings.speed` accepts 0.5 to 1.5.
- Respell terms in the script, hyphens between syllables: ctDNA → `see-tee-dee-en-ay`, MRD → `em-ar-dee`, DxP → `dee-ex-pee`, DxProvida → `dee-ex pro-vee-da` (a guess at the team's pronunciation: change it to match). Write numbers and dates as words. Listen to the voice preview before paying for a render. In the web Studio, double-click a word and choose Pronunciation to respell that one instance.
- Documented API alternative, not needed for two clips: a brand glossary (`POST /v3/brand-glossaries` with `terms: [{term, pronunciation}]`, then `brand_glossary_id` on the video; one per workspace, a second create returns 409).

## Limits and costs
- Per minute with a stock avatar, web plan credits / API price: Avatar III 4 / US$0.99; Avatar IV (API default) 31 / US$4.83; Avatar V 48 / US$7.20 (digital twin rate).
- Billed by seconds generated. Both clips are about 35 seconds: about 18 of Creator's 600 credits on Avatar IV, or about US$2.80 by API on Avatar IV (US$0.60 on Avatar III). A US$5 wallet covers 62 seconds of Avatar IV: one re-render at most. Failed or cancelled renders are not charged. Avatar 6 API pricing is not in the published table (UNVERIFIED).
- Output: MP4, 25 fps, 720p by default over the API (request `1080p`); aspect ratios `16:9`, `9:16`, `4:5`, `5:4`, `1:1`, `auto`. API script limit 5,000 characters.
- Concurrent renders: Free 1, Creator and Pro 3, Business 6, API pay-as-you-go 10. Status polling limit is 500 a minute.
- Watermark: Free is watermarked, Creator removes it. API output on a funded wallet is unwatermarked and commercially usable according to a HeyGen blog table only (UNVERIFIED in the API docs and terms): check the first test clip.

## Gotchas
- `avatar_id` is a **look** `id` from `GET /v3/avatars/looks`, not a group id from `GET /v3/avatars`.
- `motion_prompt` is rejected for video avatars on the default Avatar IV engine. `caption: true` fails validation (`caption` is an object on v3). Send neither; with inline respellings, captions would show the respelt words anyway. Add titles in the video editor.
- `video_url` is a presigned link that expires. Download at once, or call `GET /v3/videos/{video_id}` again for a fresh one.
- 402 `insufficient_credit`: top up the wallet. 402 `subscription_required`: the account cannot top up, so use the web route. 400 `content_policy_violation`: the script was refused. The moderation policy bans false health information, so say what the product does and make no clinical claims.

## Rules for a public hackathon video
- Use a stock public avatar and voice. A custom avatar of a real person, a teammate included, needs that person's explicit consent; a digital twin will not render until the person records webcam consent (`avatar_consent_required`), and it needs training time. Avatars of celebrities or public figures without consent are prohibited. Do not create one on the day.
- Disclosure: the terms forbid presenting output as entirely human-made and require disclosure where the law does; under the EU AI Act the visible label is the publisher's job, not HeyGen's. Put a line such as "AI-generated presenter (HeyGen)" on both clips and in the project description, which also satisfies PRD §8 on labelling synthetic material.

## Fallback
HeyGen's advice for a stuck render is to cancel and resubmit once or twice; do that only while there is time. If either clip is not on disk 30 minutes before the deadline, stop waiting. Make two title cards in the video editor (intro: product name and the novelty claim as text; close: the three behaviours and "Built on MongoDB Atlas") and lay a voice-over on them: record it on a laptop microphone, or generate it with ElevenLabs (see the `dxp-elevenlabs` skill if present). Five minutes, no render queue.

## Links
- https://developers.heygen.com/generate-avatar-video, https://developers.heygen.com/reference/create-video, https://developers.heygen.com/endpoint-version-comparison
- https://developers.heygen.com/docs/usage-limits, https://developers.heygen.com/docs/error-codes
- https://help.heygen.com/en/articles/10060327-heygen-api-pricing-explained, https://help.heygen.com/en/articles/9655503-heygen-video-processing-times, https://help.heygen.com/en/articles/12903996-quick-avatar-video
- https://www.heygen.com/pricing, https://www.heygen.com/terms
