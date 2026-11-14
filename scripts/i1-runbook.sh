#!/usr/bin/env bash
# ============================================================================
# UNVERIFIED DRAFT: two independent checkers are still reviewing this file.
# Do NOT run it against dxp. It will be replaced on this branch by the
# verified copy (this banner removed) once the checks pass.
# ============================================================================
echo "UNVERIFIED DRAFT: do not run against dxp" >&2; exit 1
# I1 runbook (DxP): Modal redeploy, data on the Atlas Sandbox, M1 + snapshot, then the discovery loop.
#
# Luis runs this on his laptop from the repo root (this container cannot reach Atlas):
#     bash i1-runbook.sh               whole run, sections 0 to 7 in order
#     FROM=6.2 bash i1-runbook.sh      resume at section 6.2 (section 0's read-only checks always run)
#
# Order (Luis, 14 Nov), all against DXP_DB=dxp:
#   1 redeploy Modal from main (#53 one container, #55 schema fix) + smoke   2 gate.seed (adds sam@v2)
#   3 A13: fda_cdx then ledger.seed   4 A05/A10: setup item + prior collection (cursor stays 2026-11-11)
#   5 indexes with DXP_EMBEDDING=none (text search) until OD1 passes   6 setup run, M1 by Sam, snapshot
#   7 discovery loop and every I1 assertion (development-plan.md:182)
#
# ALREADY DONE by Luis; section 0 only RE-CHECKS them, read-only, and never redoes them:
#   dxp_app authenticates; Modal and Vercel deployed and /api/dxp/whoami is 200 as Sam;
#   grants sam@v1, lbdx@v1, seed@v1 seeded; CI MONGODB_URI secret updated; OD6 reset round trip passed.
#
# No test or smoke run belongs in this script. DXP_DB=dxp is never exported: it is given per command, only on the
# deploy (1.2), the helper `dxpdb` (2-5, 7.1), the snapshot (6.3) and the assertion reader (7.2). The integrator smoke test runs separately with DXP_DB=dxp_smoke (development-plan.md:208, D41);
# tests/conftest.py:53 forces dxp_test_<hex> anyway.
#
# MANUAL lines are browser steps; the script pauses there (read -r). Every check stops the script on failure
# (set -euo pipefail plus explicit asserts). Expected output is in the "# expect:" comments.
set -euo pipefail
# Refuse xtrace BEFORE .env is sourced: `bash -x` would print MONGODB_URI and every key during `set -a; . .env`.
case $- in *x*) echo "refusing: xtrace is on (run without -x)"; exit 1;; esac
set +x

# Section keys: "6.2" -> 62, "6" -> 60. FROM selects the first section to run.
skey() { local a="${1%%.*}" b=0; case "$1" in *.*) b="${1#*.}";; esac; echo $((10#$a * 10 + 10#$b)); }
FROM_KEY="$(skey "${FROM:-0}")"
at() { [ "$(skey "$1")" -ge "$FROM_KEY" ]; }
pause() { read -r -p "$1 -- press Enter when done " _ </dev/tty; }
fail() { echo "FAIL: $*" >&2; exit 1; }
STATE="${DXP_I1_STATE:-$HOME/.dxp-i1}"   # run ids, deployed sha, pre-discover counts (no secrets)
(umask 077; mkdir -p "$STATE")

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# ============================================================================
# 0. Preconditions and read-only re-checks of what is already done | owner: Luis
# ============================================================================
# 0.1 Checkout. Dirty-tree check FIRST, then checkout/pull: the Modal deploy builds from this checkout (modal_app.py:65-70).
[ -z "$(git status --porcelain)" ] || fail "dirty tree: commit or stash first"   # expect: no output
git checkout main && git pull --ff-only
for sha in 0b48ad1 30e3faf; do   # 0b48ad1 = #53 one API container; 30e3faf = #55 required:[] fix
  git merge-base --is-ancestor "$sha" HEAD || fail "main does not contain $sha"
done
grep -q 'max_containers=1' backend/modal_app.py || fail "#53 (one API container) missing from this checkout"   # modal_app.py:94
grep -q 'if required:' backend/dxp/store/schemas/_common.py || fail "#55 (omit empty required) missing"         # _common.py:118
grep -q '"_id": "sam@v2"' backend/dxp/gate/seed_data/grants.json || fail "#54 (sam@v2) missing"
grep -q '^async def main' backend/dxp/sources/fda_cdx.py || fail "A13 not in this checkout"   # never a silent stub
git rev-parse --short HEAD   # expect: 30e3faf or later
DEPLOY_SHA="$(git rev-parse HEAD)"; DEPLOY_SHORT="$(git rev-parse --short HEAD)"

# 0.2 Environment. .env is sourced (never printed); only the keys each step needs are passed on.
[ -f .env ] || fail "no .env at repo root"
set -a; . ./.env; set +a
unset DXP_DB MODAL_DEV_SUFFIX   # DXP_DB only via dxpdb below; modal_app.py:60-61 refuses DXP_DB=dxp with MODAL_DEV_SUFFIX
export DXP_EMBEDDING=none       # Luis: text search until OD1 passes. Overrides .env. Not auto, not voyage.
: "${MONGODB_URI:?set in .env}"
: "${DXP_AGENT_KEY:?set in .env}"
: "${DXP_API_KEY:?set in .env}"
: "${DXP_SEED_KEY:?set in .env}"
: "${ANTHROPIC_API_KEY:?set in .env}"
: "${SLACK_WEBHOOK_URL:?set in .env}"
: "${DXP_BASE_URL:?Vercel production URL, no trailing slash}"
: "${DXP_ALLOWED_ORIGINS:?Vercel production URL, no trailing slash}"
: "${DXP_MODAL_URL:?https://<workspace>--dxp.modal.run (modal_app.py:99 label dxp; = Vercel NEXT_PUBLIC_API_URL), no /api/v1}"
# gate/seed.py:98-99 requires three different keys.
if [ "$DXP_SEED_KEY" = "$DXP_AGENT_KEY" ] || [ "$DXP_SEED_KEY" = "$DXP_API_KEY" ] || [ "$DXP_AGENT_KEY" = "$DXP_API_KEY" ]; then fail "keys must differ"; fi
case "$DXP_API_KEY" in *[\"\\]*|*$'\n'*) fail "DXP_API_KEY has a quote, backslash or newline: the curl -K helper cannot carry it";; esac
# Flags task_run, revert, live_stream and interview stay OFF (V38, V46, V48, V70). DXP_FEATURES is never put in the
# Modal secret (section 1), so every backend flag is off there (dxp/__init__.py:16-23); refuse a local .env that names them.
case ",${DXP_FEATURES:-}," in *task_run*|*revert*|*live_stream*|*interview*) fail "DXP_FEATURES in .env names a flag that must stay off";; esac
API="$DXP_MODAL_URL/api/v1"
ANCHOR_NCT=NCT04712877; SETUP_NCT=NCT05715229; SCOPE=scope_plasma_ctdna_nsclc; CURSOR=2026-11-11
echo "env ok"   # expect: env ok

# Keyed requests: the X-DxP-Key header (api/auth.py:24) goes to curl on stdin (`-K -`), never in argv. Never echo a key.
dxpk() { printf 'header = "X-DxP-Key: %s"\n' "$DXP_API_KEY" | curl -sS -K - "$@"; }
# jget a.b.0.c : read one field from JSON on stdin (non-secret responses only).
jget() { python3 -c 'import json,sys
d=json.load(sys.stdin)
for k in sys.argv[1].split("."):
    d = d[int(k)] if isinstance(d, list) else (d.get(k) if isinstance(d, dict) else None)
print("" if d is None else (json.dumps(d) if isinstance(d, (dict, list)) else d))' "$1"; }
# The ONLY place DXP_DB=dxp is set: commands that must write or read the demo database. Never pytest, never smoke.
dxpdb() { (cd "$ROOT/backend" && DXP_DB=dxp uv run "$@"); }
# Read-only DB state used before and after steps 2-6 (counts, grants, the scope cursor). Prints JSON; no secrets.
dbstate() { dxpdb python - <<'EOF'
import json, os, pymongo
db = pymongo.MongoClient(os.environ["MONGODB_URI"], serverSelectionTimeoutMS=15000)["dxp"]
sc = db["research_scopes"].find_one({"_id": "scope_plasma_ctdna_nsclc"}) or {}
cur = sc.get("cursor") or {}
out = {
  "grants": sorted(g["_id"] for g in db["grants"].find({}, {"_id": 1})),
  "policies": db["policies"].count_documents({}), "policy_sets": db["policy_sets"].count_documents({}),
  "cursor": str(cur.get("last_update_post_date")), "cursor_set_by_run_id": cur.get("set_by_run_id"),
  "scope_version": sc.get("version"), "priority_refs": sc.get("priority_refs"),
  "teams": db["teams"].count_documents({}), "diagnostics": db["diagnostics"].count_documents({}),
  "fda_items": db["source_items"].count_documents({"source": "fda_cdx_list"}),
  "prior_items": db["source_items"].count_documents({"window": "prior"}),
  "setup_items": db["source_items"].count_documents({"window": "setup"}),
  "prior_findings": db["findings"].count_documents({"window": "prior"}),
  "proposals": db["proposals"].count_documents({}), "memories": db["memories"].count_documents({}),
  "runs": db["runs"].count_documents({}), "discover_runs": db["runs"].count_documents({"kind": "discover"}),
}
print(json.dumps(out, sort_keys=True))
EOF
}
cursor_unmoved() {   # the scope cursor is still the seeded one (OD2): 2026-11-11, set by no run
  local s; s="$(dbstate)"
  [ "$(printf '%s' "$s" | jget cursor)" = "$CURSOR" ] || fail "cursor is not $CURSOR: $s"
  [ -z "$(printf '%s' "$s" | jget cursor_set_by_run_id)" ] || fail "cursor was set by a run: $s"
  echo "cursor $CURSOR, set by no run"
}

# 0.3 Read-only re-checks of the done steps (nothing here writes).
(cd backend && uv run python -c $'import os,sys,pymongo as p\ntry: p.MongoClient(os.environ["MONGODB_URI"],serverSelectionTimeoutMS=10000).admin.command("ping"); print("ok")\nexcept Exception as e: print(type(e).__name__); sys.exit(1)')
# expect: ok   (dxp_app authenticates; OperationFailure = auth, ServerSelectionTimeoutError = network / IP access list)
S0="$(dbstate)"; echo "$S0"
for g in lbdx@v1 sam@v1 seed@v1; do printf '%s' "$S0" | jget grants | grep -q "\"$g\"" || fail "grant $g not seeded"; done
# expect: grants include lbdx@v1, sam@v1, seed@v1; discover_runs 0; cursor 2026-11-11, cursor_set_by_run_id null
[ "$(printf '%s' "$S0" | jget discover_runs)" = 0 ] || fail "a discover run already exists in dxp: restore the snapshot or stop"
printf '%s\n' "$S0" > "$STATE/state_0.json"
code="$(curl -sS -o "$STATE/whoami_vercel.json" -w '%{http_code}' "$DXP_BASE_URL/api/dxp/whoami")"
[ "$code" = 200 ] && [ "$(jget id < "$STATE/whoami_vercel.json")" = sam ] || fail "Vercel /api/dxp/whoami: $code"
echo "vercel whoami 200 sam"   # expect: vercel whoami 200 sam
command -v mongodump >/dev/null && command -v mongorestore >/dev/null || fail "mongodump/mongorestore missing (needed in 6.3; OD6)"
if command -v gh >/dev/null; then gh secret list | grep -q '^MONGODB_URI' && echo "CI secret MONGODB_URI present (name only)"; fi
# CHECK (by eye, not redone): OD6 passed on this laptop (docs/deploy.md, #55). Vercel production is not redeployed
#        by this runbook (Luis's order); it must already be built from a main that has B04 #39.

# ============================================================================
# 1. Redeploy Modal from current main + smoke | owner: Luis | needs #53 (one container) and #55 (schema fix)
# ============================================================================
if at 1; then
# 1.1 The secret is recreated because the containers must read DXP_EMBEDDING=none (the deployed one may hold auto,
# and a secret's values cannot be read back). It holds ONLY the 7 REQUIRED_SECRET_KEYS (modal_app.py:38-46), written
# from the environment into a mode-600 temp file (umask 077, removed by trap): never KEY=VALUE in argv, never the
# whole .env (that would carry DXP_SEED_KEY and DXP_API_KEY). --force replaces the whole secret.
# FLAGS: DXP_FEATURES is deliberately NOT in the secret: task_run, revert, live_stream and interview stay off
#        (dxp/__init__.py:16-23: a flag is on only if named). DXP_DB is not in it either (modal_app.py:74 passes it).
# Left out while their flags are off: ELEVENLABS_API_KEY (OD3), LIVEAVATAR_API_KEY (+_AVATAR_ID, _VOICE_ID; briefing/
# avatar.py:62; never HEYGEN_API_KEY), VOYAGE_API_KEY. To add one, add its name to `keys`: --force replaces everything.
SECRET_JSON="$(umask 077; mktemp "${TMPDIR:-/tmp}/dxp-secret.XXXXXX")"
trap 'rm -f "$SECRET_JSON"' EXIT
(umask 077; python3 - "$SECRET_JSON" <<'EOF'
import json, os, sys
keys = ["MONGODB_URI", "DXP_AGENT_KEY", "ANTHROPIC_API_KEY", "SLACK_WEBHOOK_URL",
        "DXP_BASE_URL", "DXP_ALLOWED_ORIGINS", "DXP_EMBEDDING"]
missing = [k for k in keys if not os.environ.get(k, "").strip()]
if missing:
    sys.exit(f"empty: {missing}")
if os.environ["DXP_EMBEDDING"] != "none":
    sys.exit("DXP_EMBEDDING must be none until OD1 passes")
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump({k: os.environ[k] for k in keys}, f)
print(f"{len(keys)} keys, DXP_EMBEDDING=none, no DXP_FEATURES")
EOF
)
# expect: 7 keys, DXP_EMBEDDING=none, no DXP_FEATURES
(cd backend && uv run modal secret create dxp --force --from-json "$SECRET_JSON" >/dev/null)   # modal 1.6.4 cli/secret.py:92-139
rm -f "$SECRET_JSON"; trap - EXIT
echo "secret dxp written"   # expect: secret dxp written

# 1.2 Deploy (DXP_DB=dxp only here and in dxpdb). --tag records the commit in the app history.
(cd backend && DXP_DB=dxp uv run modal deploy --tag "$DEPLOY_SHORT" modal_app.py)
# expect: "App deployed", web endpoint for api at $DXP_MODAL_URL, function run_pipeline
printf '%s\n' "$DEPLOY_SHA" > "$STATE/deployed_sha"
(cd backend && uv run modal app history dxp | head -6)   # expect: the newest row carries tag $DEPLOY_SHORT
# fail: "Authentication failed" or "not authorized ... collMod" in `modal app logs dxp` (startup hook, api/app.py:172-183:
#       store.ensure_indexes :176, retrieval.ensure_indexes :178 with DXP_EMBEDDING=none -> ts_* and tx_* only)

# 1.3 Smoke (read-only). Wait for the one warm container.
for _ in $(seq 1 30); do [ "$(curl -sS -o /dev/null -w '%{http_code}' "$API/schema" || true)" = 200 ] && break; sleep 10; done
curl -sS "$API/schema" | head -c 160; echo   # expect: {"fields":[{"key":"modality",...   (api/app.py:115, no key)
[ "$(curl -sS -o /dev/null -w '%{http_code}' "$DXP_MODAL_URL/openapi.json")" = 200 ] || fail "openapi.json"
dxpk -o "$STATE/whoami_modal.json" "$API/whoami"
[ "$(jget id < "$STATE/whoami_modal.json")" = sam ] || fail "Modal /whoami is not sam"   # routes_grants.py:58
curl -sS -o "$STATE/whoami_vercel.json" "$DXP_BASE_URL/api/dxp/whoami"
[ "$(jget id < "$STATE/whoami_vercel.json")" = sam ] || fail "Vercel /api/dxp/whoami is not sam after the redeploy"
[ "$(curl -sS -o /dev/null -w '%{http_code}' "$DXP_BASE_URL/")" = 200 ] || fail "Vercel home"
echo "smoke ok"   # expect: smoke ok
fi

# ============================================================================
# 2. A03 gate.seed: add sam@v2 | owner: Luis | PR: #54
# ============================================================================
if at 2; then
B="$(dbstate)"
dxpdb python -m dxp.gate.seed
# expect (exit 0): sam@v2: inserted
#                  lbdx@v1, sam@v1, seed@v1, evidence_quote_supported@v1, claim_performed_or_results@v1,
#                  claim_planned@v1, claim_preclinical@v1, scope_plasma_ctdna_nsclc: unchanged
#                  policy set ps_xxxx… (4 policies): <the 4 policy ids>   (gate/seed.py:303-305)
# The scope keeps its cursor: the seed never rewrites cursor or version (gate/seed.py:232-234).
# fail: "seed refused: ..." exit 1 (gate/seed.py:300; e.g. DXP_SEED_KEY does not match seed@v1, or a grant differs)
A="$(dbstate)"
python3 - "$B" "$A" <<'EOF'
import json, sys
b, a = json.loads(sys.argv[1]), json.loads(sys.argv[2])
assert set(a["grants"]) - set(b["grants"]) <= {"sam@v2"} and "sam@v2" in a["grants"], ("grants", b["grants"], a["grants"])
assert set(b["grants"]) <= set(a["grants"]), "a grant disappeared"
for k in b:
    if k != "grants":
        assert a[k] == b[k], (k, b[k], a[k])
print("sam@v2 present; nothing else changed; cursor", a["cursor"])
EOF
# expect: sam@v2 present; nothing else changed; cursor 2026-11-11
cursor_unmoved   # expect: cursor 2026-11-11, set by no run
dxpk -o "$STATE/whoami_modal.json" "$API/whoami"
grep -q '"answer_question"' "$STATE/whoami_modal.json" || fail "whoami does not show sam@v2's answer_question"
echo "whoami sam on sam@v2"   # expect: whoami sam on sam@v2 (answer_question needs the interview flag, which stays off)
fi

# ============================================================================
# 3. A13: FDA list, then the ledger seed | owner: Luis | PR: A13 #26
# ============================================================================
if at 3; then
dxpdb python -m dxp.sources.fda_cdx --dry-run
# expect: FDA list (current as of <date>): 76 lung rows, <T> trade names, then the names   (fda_cdx.py:437-440; writes nothing)
dxpdb python -m dxp.sources.fda_cdx
# expect: source_items: 76 inserted, 0 already present   (fda_cdx.py:450; a rerun: 0 inserted, 76 already present)
# fail: a fetch or parse error -> fallback: --html <page saved by hand, NOT under data/> (fda_cdx.py:416-420)
dxpdb python -m dxp.ledger.seed
# expect (exit 0): FDA seed: 76 rows, <T> Diagnostics, <V> values filed, 0 already filed, 0 blocked; Teams: 3 inserted, 0 already present
# fail: exit 2 "seed refused: ..." (ledger/seed.py:420; seed key); exit 1 with "  blocked: <name>: field=value" lines (:429-430)
S3="$(dbstate)"; echo "$S3"
[ "$(printf '%s' "$S3" | jget teams)" = 3 ] || fail "teams != 3"
[ "$(printf '%s' "$S3" | jget diagnostics)" -gt 0 ] || fail "no diagnostics"
cursor_unmoved
fi

# ============================================================================
# 4. A05/A10: the setup item and the prior collection (full, with extraction) | owner: Luis | PR: A05 #27, A08 #14
# ============================================================================
if at 4; then
# 4.1 The setup item NCT05715229 (window "setup"): the prior load excludes it (load.py:285-286) and the setup run in
#     section 6 fails source_item_missing without it (pipeline/item.py:239). A05 card, development-plan.md:400.
dxpdb python -m dxp.sources.load --nct "$SETUP_NCT"
# expect: NCT05715229 setup: sv_... (new version|unchanged, last update <date>)   (sources/load.py:337)
# 4.2 The prior collection, ONCE, after section 3: extraction reads the seeded trade names (prior.py:143) and
#     file_prior calls load_prior itself (prior.py:141). Needs DXP_SEED_KEY (seed@v1) and ANTHROPIC_API_KEY.
dxpdb python -m dxp.pipeline.prior
# expect: one "NCT... loaded sv_... (<date>)" line per trial, NCT04712877 "left for the discovery scan", NCT05715229 "excluded"
# expect: prior collection for scope_plasma_ctdna_nsclc, cursor 2026-11-11: ~18 loaded, 1 left for the scan, 1 excluded, 0 failed; 20 of 20 in the manifest
# expect: baseline filing: ~18 extracted, 0 already filed, 0 not relevant, 0 failed; <n> trial-level findings, <d> Diagnostic findings not filed (V54), <k> evidence-collection entries filed (...)
# fail: exit 2 "the prior collection is loaded only before the first scan" (cursor moved) or PermissionError (seed key) (prior.py:202-204);
#       exit 1 = an NCT FAILED or an extraction failed: rerun (idempotent: "already filed" for the done ones)
S4="$(dbstate)"; echo "$S4"
[ "$(printf '%s' "$S4" | jget setup_items)" = 1 ] || fail "setup item missing"
[ "$(printf '%s' "$S4" | jget prior_items)" -gt 0 ] || fail "no prior items"
cursor_unmoved   # expect: cursor 2026-11-11, set by no run  (the prior load never moves it)
fi

# ============================================================================
# 5. Indexes and embeddings with DXP_EMBEDDING=none (text search) | owner: Luis | PR: A19+A20 #19
# ============================================================================
if at 5; then
# none = no embeddings and no vector index: index_definitions("none") is ts_* ($search) + tx_* ($text) only
# (retrieval/indexes.py:110-118). Retrieval then never tries $vectorSearch (related.py:3-8). Any vs_* left from an
# earlier auto deploy is ignored in this mode. Until OD1 passes, related evidence is labelled honestly:
#   report page "Related by text search (Vector Search unavailable)" (web/components/report/related-evidence.tsx:92),
#   retrieval.method / related[].retrieval_method = "text_search" (api/models.py:91, 379).
# After OD1 passes (not in this run): DXP_EMBEDDING=auto in the secret, redeploy, rerun this section, then a new snapshot.
dxpdb python - <<'EOF'
import asyncio, logging
logging.basicConfig(level=logging.INFO)
from dxp import store
from dxp.retrieval import indexes as ix
async def main():
    assert ix.embedding_mode() == "none", ix.embedding_mode()
    await ix.ensure_indexes()
    print(await ix.index_status())
    ok = await ix.wait_until_queryable(timeout_s=900, poll_s=15)
    print(await ix.index_status()); print("ALL QUERYABLE (text search)" if ok else "NOT QUERYABLE")
    await store.close(); return 0 if ok else 1
raise SystemExit(asyncio.run(main()))
EOF
# expect: {'ts_source_items': True, 'ts_findings': True, 'ts_memories': True}, then ALL QUERYABLE (text search)
# fail: "not built: OperationFailure" warning = role lacks createSearchIndexes on dxp; NOT QUERYABLE after 900 s = stop
fi

# ============================================================================
# 6. Setup run on NCT05715229, M1 by Sam, snapshot | owner: Luis (Sam in the browser)
#    Needs deployed (development-plan.md:181): step 1 + A07+A11 #30, A09 #25, A10 #24, A21+A22 #18, A24 #29, B04 #39.
# ============================================================================
if at 6.1; then
# 6.1 The setup run. Key = DXP_API_KEY (sam); agent key -> 403 not_startable_by_caller (runs/__init__.py:120);
#     seed key -> 403 seed_key_not_accepted. RunCreate requires grant_id (models.py:1117-1121).
SETUP_RUN_ID="$(dxpk -X POST "$API/runs" -H 'Content-Type: application/json' \
  -d "{\"grant_id\":\"lbdx\",\"set\":\"nct:$SETUP_NCT\"}" | jget id)"
[ -n "$SETUP_RUN_ID" ] || fail "POST /runs returned no id (409 run_active = another run is running)"
printf '%s\n' "$SETUP_RUN_ID" > "$STATE/setup_run_id"
# expect: Run kind "items", status "running", initiated_by "sam", agent "dxp-curator"
s=""; for _ in $(seq 1 80); do s="$(dxpk "$API/runs/$SETUP_RUN_ID" | jget status)"; case "$s" in running|stopping) sleep 15;; *) break;; esac; done
echo "setup run $SETUP_RUN_ID: $s"   # expect: done
[ "$s" = done ] || { dxpk "$API/runs/$SETUP_RUN_ID"; echo; fail "setup run not done"; }
dxpk "$API/runs/$SETUP_RUN_ID"; echo             # expect: counts total 1 done 1 reports 1, failures []
dxpk "$API/reports?run_id=$SETUP_RUN_ID"; echo   # expect: 1 item, status pending, NCT05715229, script non-empty
dxpk "$API/actions?run_id=$SETUP_RUN_ID"; echo   # expect: 1 notify_slack delivered, link_urls.report_url=$DXP_BASE_URL/reports/<id> (actions/slack.py:146-155)
# fail: failures[] "notify: SenderNotConfigured" = SLACK_WEBHOOK_URL or DXP_BASE_URL missing from the Modal secret
cursor_unmoved   # an nct: run never moves the scope cursor
fi

if at 6.2; then
SETUP_RUN_ID="${SETUP_RUN_ID:-$(cat "$STATE/setup_run_id")}"
SETUP_REP="$(cd backend && uv run python -c "from dxp import identity; print(identity.derive('rep_', '$SETUP_RUN_ID', 'clinicaltrials.gov:$SETUP_NCT'))")"
printf '%s\n' "$SETUP_REP" > "$STATE/setup_report_id"
echo "Sam: open $DXP_BASE_URL/reports/$SETUP_REP"
# MANUAL: Sam (signed in as Sam) chooses "Reject", note "Terminated trial with no posted results: describe its status; do not state outcomes"
# MANUAL: Sam MUST set "What is this correction about?" to "Outcome or result stated without posted results"
#         = claim_kind claim_performed_or_results (web/components/report-decision/decision-form.tsx:22,116). The default
#         "Not specified" gives an untagged M1 that the anchor run does not retrieve (V61, ARCHITECTURE-SPINE.md:772).
#   expect toast: "Rejected. Memory saved (mem_...)."   (web/components/report-decision/index.tsx:125)
pause "MANUAL: Sam rejected the setup report with the note and claim_performed_or_results"
# Check M1: author Sam, its source decision, its tag (development-plan.md:181). Key read from the environment, not argv.
(cd backend && SETUP_RUN_ID="$SETUP_RUN_ID" SETUP_REP="$SETUP_REP" uv run python - <<'EOF'
import json, os, sys, urllib.request
from dxp import identity
API = os.environ["DXP_MODAL_URL"] + "/api/v1"
def get(path):
    req = urllib.request.Request(API + path, headers={"X-DxP-Key": os.environ["DXP_API_KEY"]})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)
bad = []
def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond: bad.append(what)
team = get(f"/runs/{os.environ['SETUP_RUN_ID']}")["team_id"]
mems = get(f"/memories?team_id={team}")["items"]
ok(len(mems) == 1, f"exactly 1 memory for {team} (got {len(mems)})")
m = mems[0] if mems else {}
src = m.get("source") or {}
ok(m.get("status") == "active" and m.get("author") == "sam" and m.get("version") == 1, "M1 active, author sam, version 1")
ok((m.get("tags") or {}).get("claim_kind") == "claim_performed_or_results", "M1 tags.claim_kind = claim_performed_or_results")
ok(src.get("report_id") == os.environ["SETUP_REP"], "M1 source.report_id = the setup report")
ok(bool(src.get("decision_id")), "M1 source.decision_id set")
if src.get("decision_id"):
    ok(m.get("id") == identity.derive("mem_", team, src["decision_id"]), "M1 id = derive('mem_', team_id, source.decision_id)")
    d = get(f"/decisions/{src['decision_id']}")
    ok(d.get("kind") == "decide_report" and d.get("outcome") == "allowed", "source decision is an allowed decide_report")
    ok((d.get("target") or {}).get("report_id") == os.environ["SETUP_REP"], "source decision targets the setup report")
    ok(d.get("initiated_by") == "sam", "source decision initiated_by sam")
print("M1", m.get("id"))
sys.exit(1 if bad else 0)
EOF
)
# expect: all PASS, then M1 mem_...
fi

if at 6.3; then
# 6.3 Snapshot, BEFORE section 7. Never --allow-no-memory or --allow-runs (reset_demo.py:280-281 refuse without
#     an active memory or after a discover run). --db is required (reset_demo.py:276).
S6="$(dbstate)"; echo "$S6"
[ "$(printf '%s' "$S6" | jget memories)" = 1 ] || fail "dxp must hold exactly 1 memory (M1) before the snapshot"
[ "$(printf '%s' "$S6" | jget discover_runs)" = 0 ] || fail "a discover run exists: the snapshot must have none"
cursor_unmoved
DXP_DB=dxp uv run --project backend python scripts/reset_demo.py --db dxp --snapshot
# expect: snapshot of dxp: <N> documents in <K> collections -> ~/dxp-snapshots/dxp-<UTC>   (reset_demo.py:297)
python3 - <<'EOF'
import json, pathlib, sys
found = []
for p in (pathlib.Path.home() / "dxp-snapshots").glob("*/manifest.json"):
    m = json.loads(p.read_text())
    if m.get("db") == "dxp":
        found.append((m.get("taken_at", ""), p, m))
if not found: sys.exit("FAIL no dxp snapshot manifest")
_, p, m = max(found, key=lambda t: t[0])
c = m["collections"]
print(p, "memories", c.get("memories", 0), "runs", c.get("runs", 0))
if c.get("memories", 0) != 1: sys.exit("FAIL the snapshot must hold exactly 1 memory (M1)")
if c.get("runs", 0) != 1: sys.exit("FAIL the snapshot must hold only the setup run (no discover run)")
EOF
# expect: <path>/manifest.json memories 1 runs 1
fi

# ============================================================================
# 7. The discovery loop | owner: Luis | all core deployed (section 1)
# ============================================================================
if at 7.1; then
# 7.1 Before the run: fingerprint every assay record (diagnostics) and the proposals naming one, for "no assay record changed".
dxpdb python - "$STATE/pre_discover_counts.json" <<'EOF'
import hashlib, json, os, sys, pymongo
db = pymongo.MongoClient(os.environ["MONGODB_URI"])["dxp"]
dx = list(db["diagnostics"].find({}).sort("_id", 1))
c = {"diagnostics": len(dx),
     "diagnostics_sha": hashlib.sha256(json.dumps(dx, default=str, sort_keys=True).encode()).hexdigest(),
     "proposals_with_dx": db["proposals"].count_documents({"diagnostic_id": {"$ne": None}})}
json.dump(c, open(sys.argv[1], "w")); print("pre-discover", c["diagnostics"], c["proposals_with_dx"])
EOF
DISC_RUN_ID="$(dxpk -X POST "$API/runs" -H 'Content-Type: application/json' -d '{"grant_id":"lbdx","set":"discover"}' | jget id)"
[ -n "$DISC_RUN_ID" ] || fail "POST /runs returned no id (409 run_active; discover_without_scope = section 2)"
printf '%s\n' "$DISC_RUN_ID" > "$STATE/disc_run_id"
# expect: Run kind "discover", scope_id scope_plasma_ctdna_nsclc
s=""; for _ in $(seq 1 120); do s="$(dxpk "$API/runs/$DISC_RUN_ID" | jget status)"; case "$s" in running|stopping) sleep 15;; *) break;; esac; done
echo "discover run $DISC_RUN_ID: $s"   # expect: done
dxpk "$API/runs/$DISC_RUN_ID"; echo     # expect: counts.reports >= 1, failures [], scan.cursor_from 2026-11-11, scan.source_refs[0] the anchor
[ "$s" = done ] || fail "discover run not done (a ScanError leaves search_source failed and the cursor unmoved)"
fi

if at 7.2; then
# 7.2 Every I1 loop assertion (development-plan.md:182; V14, V35, V37, V40, V41, V43). Key read from the environment.
DISC_RUN_ID="${DISC_RUN_ID:-$(cat "$STATE/disc_run_id")}"
SETUP_REP="${SETUP_REP:-$(cat "$STATE/setup_report_id")}"
(cd backend && DXP_DB=dxp DISC_RUN_ID="$DISC_RUN_ID" SETUP_REP="$SETUP_REP" uv run python - "$STATE/pre_discover_counts.json" <<'EOF'
import hashlib, json, os, sys, urllib.request, pymongo
from dxp import identity
from dxp.reports.draft import wording_flags
from dxp.actions import slack
API = os.environ["DXP_MODAL_URL"] + "/api/v1"
BASE = os.environ["DXP_BASE_URL"].rstrip("/")
RUN = os.environ["DISC_RUN_ID"]
ANCHOR_NCT = "NCT04712877"; ANCHOR = f"clinicaltrials.gov:{ANCHOR_NCT}"
CURSOR = "2026-11-11"; SCOPE = "scope_plasma_ctdna_nsclc"
CDX, LIQ, CDX_ID = "FoundationOne CDx", "FoundationOne Liquid", "dx_c01e65b2ae2d0950"
def get(path, base=API, key=True):
    h = {"X-DxP-Key": os.environ["DXP_API_KEY"]} if key else {}
    with urllib.request.urlopen(urllib.request.Request(base + path, headers=h), timeout=30) as r:
        return json.load(r)
bad = []
def ok(cond, what):
    print(("PASS " if cond else "FAIL ") + what)
    if not cond: bad.append(what)
def texts(x):
    if isinstance(x, str): yield x
    elif isinstance(x, dict):
        for v in x.values(): yield from texts(v)
    elif isinstance(x, list):
        for v in x: yield from texts(v)
REP = identity.derive("rep_", RUN, ANCHOR)
run = get(f"/runs/{RUN}"); rep = get(f"/reports/{REP}"); audit = get(f"/runs/{RUN}/audit")
scope = get(f"/scopes/{SCOPE}")
acts = get(f"/actions?run_id={RUN}")["items"]
props = get(f"/proposals?report_id={REP}")["items"]
entries = sorted(audit.get("entries") or [], key=lambda e: e.get("seq") or 0)
disc = rep.get("discovery") or {}
vid = rep.get("version_id")
print("report", REP, "draft", rep.get("draft"))

# 1 anchor found first (priority_refs), update date after the cursor, status and results as in the live response
ok((scope.get("priority_refs") or [None])[0] == ANCHOR, "1 scope.priority_refs[0] is the anchor")
ok(((run.get("scan") or {}).get("source_refs") or [None])[0] == ANCHOR, "1 scan.source_refs[0] is the anchor (found first)")
ok((run.get("scan") or {}).get("cursor_from") == CURSOR, "1 scan.cursor_from = 2026-11-11")
ok((scope.get("cursor") or {}).get("set_by_run_id") == RUN, "1 scope cursor now set_by_run_id = discover run")
live = get(f"/studies/{ANCHOR_NCT}", base="https://clinicaltrials.gov/api/v2", key=False)
st = (live.get("protocolSection") or {}).get("statusModule") or {}
live_date = (st.get("lastUpdatePostDateStruct") or {}).get("date")
src = [s for s in audit.get("sources") or [] if s.get("source_ref") == ANCHOR]
ok(bool(live_date) and live_date > CURSOR, f"1 live lastUpdatePostDate {live_date} > cursor {CURSOR}")
ok(bool(src) and (src[0].get("source_date") or "") > CURSOR, f"1 audit source_date {src[0].get('source_date') if src else None} > cursor")
norm = lambda s: str(s or "").upper().replace(" ", "_")
ok(norm(disc.get("trial_status")) == norm(st.get("overallStatus")), f"1 trial_status {disc.get('trial_status')} = live {st.get('overallStatus')}")
ok(disc.get("has_results") == bool(live.get("hasResults")), f"1 has_results {disc.get('has_results')} = live {live.get('hasResults')}")
# 2 mentions (plan: name_mentions; API: discovery.mentions, models.py:795)
men = {m.get("name"): m for m in disc.get("mentions") or []}
ok(CDX in men and men[CDX].get("resolved_diagnostic_id") == CDX_ID, "2 FoundationOne CDx -> " + CDX_ID)
ok(LIQ in men and men[LIQ].get("resolved_diagnostic_id") is None, "2 FoundationOne Liquid -> null, kept as written")
ok(any(LIQ in u for u in rep.get("uncertainties") or []), "2 FoundationOne Liquid listed under uncertainties")
ok(bool((rep.get("gap") or "").strip()), "2 gap named")
# 3 the FoundationOne CDx link blocked by check 2, citing the mention and the scope rule (gate/checks.py team_scope)
blk = [e for e in entries if e.get("kind") == "file_proposal" and e.get("outcome") == "blocked" and e.get("failed_check") == "team_scope"]
ok(len(blk) == 1, f"3 exactly one blocked file_proposal on team_scope (got {len(blk)})")
if blk:
    det = " ".join((c.get("detail") or "") for c in blk[0].get("checks") or [] if c.get("check") == "team_scope")
    print("   check-2 detail:", det)
    ok(f"mention '{CDX}'" in det and CDX_ID in det and "outside the scope" in det, "3 blocked Decision cites the mention and the scope rule")
# 4 draft 1 blocked (claim_performed_or_results) and draft 2 filed. Luis requires it; the plan calls it "if it occurs" (V21):
#   if ONLY this fails, the model did not write the claim in draft 1; Luis decides whether that run counts.
ok(rep.get("draft") == 2 and bool(rep.get("blocked_draft_decision_id")), f"4 report is draft 2 with blocked_draft_decision_id (draft {rep.get('draft')})")
if rep.get("blocked_draft_decision_id"):
    d1b = get(f"/decisions/{rep['blocked_draft_decision_id']}")
    failed_claims = [c for c in d1b.get("claims") or [] if c.get("passed") is False]
    ok(d1b.get("outcome") == "blocked" and any(c.get("claim_kind") == "claim_performed_or_results" for c in failed_claims),
       f"4 draft-1 Decision blocked, naming claim_performed_or_results ({d1b.get('failed_check')}, {[c.get('claim_kind') for c in failed_claims]})")
ok(bool(rep.get("file_decision_id")), "4 draft 2 filed (file_decision_id set)")
# 5 one pending report, its only update adds the anchor to the scope's evidence collection; no assay record changed
ok(rep.get("status") == "pending" and rep.get("diagnostic_ids") == [] and len(rep.get("proposal_ids") or []) == 1, "5 report pending, diagnostic_ids [], one proposal")
ok(len(props) == 1 and props[0].get("field") == "evidence_collection" and props[0].get("value") == ANCHOR
   and props[0].get("diagnostic_id") is None and props[0].get("status") == "pending", "5 proposal: evidence_collection, the anchor, diagnostic_id null, pending")
pre = json.load(open(sys.argv[1]))
db = pymongo.MongoClient(os.environ["MONGODB_URI"])["dxp"]
dx = list(db["diagnostics"].find({}).sort("_id", 1))
post = {"diagnostics": len(dx),
        "diagnostics_sha": hashlib.sha256(json.dumps(dx, default=str, sort_keys=True).encode()).hexdigest(),
        "proposals_with_dx": db["proposals"].count_documents({"diagnostic_id": {"$ne": None}})}
ok(pre == post, f"5 no assay record changed (diagnostics count+hash, proposals with a Diagnostic: {pre['diagnostics']}/{post['diagnostics']})")
# intervention verbatim; ambiguous intervention field under uncertainties
it = disc.get("intervention_text") or ""
ver = db["source_versions"].find_one({"_id": vid}) or {}
ok(bool(it) and it in "\n".join(texts(ver)), "5 intervention_text is verbatim in the pinned source version")
ok(any("intervention field is ambiguous" in u for u in rep.get("uncertainties") or []), "5 ambiguous intervention field under uncertainties (reports/draft.py:29-32)")
# 6 related evidence: labels, both quotes, similarity, method = text_search (DXP_EMBEDDING=none; "related by text search")
rel = rep.get("related") or []
ok(bool(rel) and all(r.get("label") and r.get("new_quote") and r.get("related_quote") and r.get("similarity") is not None
                     and r.get("retrieval_method") for r in rel), f"6 {len(rel)} related: label, both quotes, similarity, retrieval_method")
ok(bool(rel) and all(r.get("retrieval_method") == "text_search" for r in rel), "6 every related[] retrieval_method is text_search")
# 7 Slack: exactly one delivered, its link opens the report on the deployed app, no diagnostic_url, wording rule
ns = [a for a in acts if a.get("kind") == "notify_slack"]
ok(len(ns) == 1, f"7 exactly one notify_slack (got {len(ns)})")
if ns:
    a = ns[0]; res = a.get("result") or {}; links = res.get("link_urls") or {}
    ok(a.get("status") == "delivered" and res.get("http_status") == 200, "7 notify_slack delivered, http 200")
    ok(links.get("report_url") == f"{BASE}/reports/{REP}" and links.get("diagnostic_url") is None, "7 report_url = deployed report page, diagnostic_url null")
    try:
        with urllib.request.urlopen(links.get("report_url") or BASE + "/x", timeout=30) as r: code = r.status
    except Exception as e: code = getattr(e, "code", type(e).__name__)
    ok(code == 200, f"7 the alert's report_url opens (HTTP {code})")
    payload = slack.build_message(action_id=a["id"], report=rep, proposals=props, links=links,
                                  actor=slack.Actor(agent=run.get("agent"), run_id=RUN, grant=f"{run.get('grant_id')}@v{run.get('grant_version')}",
                                                    policy_set_version=run.get("policy_set_version")))
    flags = wording_flags("\n".join(texts(payload)), [CDX, LIQ])
    ok(not flags, f"7 Slack text follows the wording rule {flags}")
    ok(a["id"] == identity.derive("act_", RUN, "notify_slack", "-", REP), "V43 notify act_ id derived with '-' for the Diagnostic")
# wording on the report itself
flags = wording_flags("\n".join([rep.get("headline") or "", disc.get("summary") or "", rep.get("script") or ""]), [CDX, LIQ])
ok(not flags, f"wording: report headline/summary/script follow the wording rule {flags}")
# V43: diagnostic_id null, target.scope_id; check 2 judged the scope, looked up no Diagnostic; '-' in Decision/action/admission ids
ok(bool(props) and (props[0].get("target") or {}).get("scope_id") == SCOPE, "V43 proposal target.scope_id")
fd = get(f"/decisions/{rep['file_decision_id']}") if rep.get("file_decision_id") else {}
ok((fd.get("target") or {}).get("diagnostic_id") is None and (fd.get("target") or {}).get("scope_id") == SCOPE, "V43 file Decision target: scope_id, diagnostic_id null")
c2 = [c for c in fd.get("checks") or [] if c.get("check") == "team_scope"]
ok(bool(c2) and c2[0].get("passed") is True and "targets the scope's evidence collection" in (c2[0].get("detail") or ""), "V43 check 2 passed on the scope")
mine = [a for a in acts if a.get("decision_id") == fd.get("id") or a.get("kind") == "notify_slack"]
for a in mine:
    adm = db["admissions"].find_one({"_id": a.get("admission_id")}) if a.get("admission_id") else None
    ok(adm is not None and adm.get("item_key", "").split("|")[2:3] == ["-"], f"V43 admission of {a.get('kind')} uses '-' for the Diagnostic ({adm and adm.get('item_key')})")
# M1 in memories used with its before/after effect taken from the two gated drafts
d1 = [e for e in entries if e.get("kind") == "file_proposal" and (e.get("inputs") or {}).get("draft") == 1 and str((e.get("inputs") or {}).get("id_target", "")).startswith(REP)]
d2 = [e for e in entries if e.get("kind") == "file_proposal" and (e.get("inputs") or {}).get("draft") == 2 and str((e.get("inputs") or {}).get("id_target", "")).startswith(REP)]
m1 = [u for u in rep.get("memories_used") or [] if (u.get("source") or {}).get("report_id") == os.environ["SETUP_REP"]]
ok(len(m1) == 1 and m1[0].get("author") == "sam", "M1 in memories_used, author sam, source.report_id = setup report")
eff = (m1[0].get("effect") if m1 else None) or {}
ok(bool(eff) and eff.get("before") != eff.get("after"), f"M1 effect non-null and before != after: {eff}")
if eff and d1 and d2:
    t1, t2 = "\n".join(texts(d1[0].get("inputs"))), "\n".join(texts(d2[-1].get("inputs")))
    ok((eff["before"] == "" or eff["before"] in t1) and (eff["after"] == "" or eff["after"] in t2),
       "M1 effect.before is in draft 1 and effect.after is in draft 2 (audit inputs, reports/file.py:80-88)")
else:
    ok(False, f"both gated drafts in the audit (draft 1: {len(d1)}, draft 2: {len(d2)})")
# V40 version_id pinned
pins = [q.get("version_id") for q in disc.get("quotes") or []] + [(r.get("new_quote") or {}).get("version_id") for r in rel]
pins += [(p.get("evidence") or {}).get("version_id") for p in props]
pins += [(e.get("evidence_ref") or {}).get("version_id") for e in entries if (e.get("evidence_ref") or {}).get("source_ref") == ANCHOR]
pins += [(a.get("inputs") or {}).get("version_id") for a in ns if (a.get("inputs") or {}).get("version_id")]
ok(bool(vid) and all(p == vid for p in pins), f"V40 every anchor pin = report.version_id ({len(pins)} pins)")
# CHECK: related[].related_quote.version_id and retrieval.items[].version_id pin the related items' versions, not the anchor's.
# V41 script; V14 audit: sources with the cursor, retrieval method text_search, memories used with effect, labels with both quotes, Slack result
ok(bool(rep.get("script")) and bool(rep.get("script_hash")), "V41 report.script and script_hash non-empty")
seqs = [e.get("seq") for e in entries if e.get("seq") is not None]
ok(seqs == sorted(seqs), "V14 audit entries in seq order")
ss = [e for e in entries if e.get("kind") == "search_source"]
ok(bool(ss) and (ss[0].get("scan") or {}).get("cursor_from") == CURSOR and ANCHOR in ((ss[0].get("scan") or {}).get("source_refs") or []),
   "V14 audit shows the sources fetched with the cursor")
if d2:
    e2 = d2[-1]
    ok((e2.get("retrieval") or {}).get("method") == "text_search", "V14 audit retrieval method text_search")
    ok(any(u.get("effect") for u in e2.get("memories_used") or []), "V14 audit shows memories used with their effect")
    rels = e2.get("relationships") or []
    ok(bool(rels) and all(r.get("label") and r.get("new_quote") and r.get("related_quote") for r in rels), "V14 audit relationship labels with both quotes")
    ok(bool(e2.get("claims")), "V14 final draft entry has its claim checks")
na = [e for e in entries if e.get("kind") == "notify_slack"]
ok(bool(na) and na[0].get("status") == "delivered" and (na[0].get("result") or {}).get("http_status") == 200, "V14 audit shows the Slack result")
print("FAILED:", len(bad)) if bad else print("ALL I1 LOOP ASSERTIONS PASS")
sys.exit(1 if bad else 0)
EOF
)
# expect: every line PASS, then ALL I1 LOOP ASSERTIONS PASS
REP="$(cd backend && uv run python -c "from dxp import identity; print(identity.derive('rep_', '$DISC_RUN_ID', 'clinicaltrials.gov:$ANCHOR_NCT'))")"
echo "open $DXP_BASE_URL/reports/$REP"
# MANUAL: in Slack, click "Review in DxP" on the ONE new alert; expect: this same report page opens; no "Open diagnostic" link.
# MANUAL: the related evidence section reads "Related by text search (Vector Search unavailable)" (related-evidence.tsx:92).
# MANUAL: wording by eye: no "uses", "studies", "showed" or performance wording on either name in the headline, summary,
#         script and the Slack alert (wording_flags, reports/draft.py:255, catches the verb forms; performance words need a human).
# MANUAL: open the run's Audit view; expect: sources with the cursor, "text search", M1 with before/after, both quotes, Slack delivered.
pause "MANUAL: Slack link, text-search label, wording and Audit view checked"
echo "I1 loop done"   # expect: I1 loop done
fi
