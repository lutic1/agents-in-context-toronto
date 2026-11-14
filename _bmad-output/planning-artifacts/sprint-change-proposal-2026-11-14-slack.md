---
title: Sprint Change Proposal, Slack replaces GitHub as the external system
status: approved
created: 2026-11-14
approved_by: Luis
scope: moderate
supplements: sprint-change-proposal-2026-11-13.md, readiness-fixes-2026-11-14.md
---

# Slack replaces GitHub as the external system

## Trigger

Luis tested a Slack incoming webhook that posts to `#all-mango-db-hackathon`. It posts a Block Kit alert for a new diagnostic. Slack is now the external system in the demo, and GitHub is removed as a planned integration.

Where any earlier document mentions GitHub, a review issue, `dxp-review-sandbox` or reconciling against GitHub, this file wins.

## The core story, unchanged

1. DxP finds and links evidence for a diagnostic.
2. It records a proposed review in DxP.
3. It applies the policy gate before the Slack notification.
4. It writes an audit record. From that record a reviewer can see:
   - the agent identity;
   - its authority;
   - the policy decision;
   - the notification result;
   - the DxP review status.

Approval and rejection happen in DxP, never in Slack.

## Decisions

### What the notification is

- **S1. Action kind.** `notify_slack` replaces `create_review_issue` everywhere: grants, policies, the gate, actions, decisions, the audit and the screens.
- **S2. Destination.** The destination is `slack:#all-mango-db-hackathon`. The agent grant's destinations are `ledger` and `slack:#all-mango-db-hackathon`, and its actions are `file_proposal` and `notify_slack`. A notification to any other destination fails check 3.
- **S3. Configuration.**
  - `SLACK_WEBHOOK_URL` holds the webhook. It is a credential: it lives only in `.env` and in the Modal secret, and is never committed, logged or shown on screen.
  - `DXP_BASE_URL` is the production web address, for example the Vercel production URL. It is used to build links back to DxP.
  - The old `DXP_GITHUB_TOKEN` and `DXP_GITHUB_REPO` are removed.
- **S4. Notify only.** The message has links and no interactive elements: no approve or reject buttons and no Slack actions. Slack sends nothing back to DxP, and DxP exposes no Slack callback route.

### The message and its links

- **S5. The message.** A Block Kit alert with:
  - a header "New diagnostic evidence for review", plus the action ID;
  - the Diagnostic name;
  - the evidence: the trial NCT ID with its ClinicalTrials.gov link, and the quote of at most 300 characters;
  - the proposed change, for example "Add trial NCT04712877 to Trials";
  - who acted: the agent, the run ID, the grant `{grant_id}@v{version}`, and the policy set `ps_…`;
  - a context line: "Approve or reject in DxP. Slack only notifies."
- **S6. Links back to DxP.** Built from `DXP_BASE_URL`:
  - "Review in DxP" links to `${DXP_BASE_URL}/review?proposal=<p_id>`. The Review page (`web/app/review/`, PR B04) opens with that proposal focused, and shows "Proposal not found" if the ID is unknown.
  - "Open diagnostic" links to `${DXP_BASE_URL}/diagnostics/<dx_id>`, the Record page (`web/app/diagnostics/[id]`, PR B04).

  The sender refuses to start if `DXP_BASE_URL` is not set. Story 9.4 tests that both links resolve on the deployed web app.

### Sending, failure and recovery

- **S7. Sending and its outcome.** A webhook post cannot be looked up afterwards, so DxP records exactly what it observed. The action's statuses are `queued`, `dispatching`, `delivered`, `failed` and `unknown`, plus `reconciling` at read time only.
  - The action ID is saved first, and the action is claimed atomically (`queued` to `dispatching`) so two workers never both send it.
  - **HTTP 200 with body `ok`:** `delivered`, with the time posted and the response.
  - **HTTP 4xx** (for example `invalid_payload`, `no_service`, `channel_not_found`): `failed`, never retried.
  - **HTTP 429:** nothing was posted. Retry once, after `Retry-After`, while still holding the claim. A second 429 means `failed`.
  - **Timeout, connection error or HTTP 5xx:** the outcome is ambiguous, so the action is `unknown`. It is never retried automatically.
  - All of these updates are conditional on the current status.
- **S8. Manual resolution replaces reconciling against GitHub.**
  - `POST /actions/<action_id>/resolve { outcome: delivered | failed, note }`, gated as kind `resolve_notification`, lets a Reviewer settle an `unknown` notification after checking the channel for the action ID. It is audited as a Decision with the Reviewer's stamp.
  - The sweep marks `dispatching` actions of abandoned admissions `unknown`, never retried. It still marks `queued` ones `failed` with `abandoned_before_send`.
  - The GitHub reconcile route and the listing of issues are removed.
- **S9. The audit record.** Each notification action keeps:
  - its Decision (the agent, `initiated_by`, the grant evaluated, the policy set and every check);
  - its inputs and evidence reference;
  - the destination;
  - timestamps: queued, claimed, posted and observed;
  - the result: HTTP status, Slack's response body, and the link URLs sent.

  The audit and the Audit view also show the proposal's live DxP review status: pending, applied or rejected, with who decided and when. "Who authorised this?" answers from the Decision's `authorised_by`.

### Screens and the demo

- **S10. Screens.**
  - The action row shows "Slack alert delivered" with the time, or Failed or Unknown.
  - The impact view shows notification nodes (`notification:<action_id>`) in place of issue nodes.
  - Proposals carry `notification { action_id, status, posted_at }` instead of `review_issue`.
- **S11. The demo.**
  - The second screen shows the alert arriving in Slack `#all-mango-db-hackathon` (instead of the issue in GitHub). Its "Review in DxP" link opens the focused proposal, where Sam approves.
  - The blocked case is unchanged: FoundationOne CDx is outside the Team's scope, so no proposal is filed and no Slack message is sent.
  - The 60-second video: 10 to 30 seconds is the allowed action reaching Slack.

### Repository and sign-off

- **S12. Open items and README.**
  - Removed: "create `dxp-review-sandbox` and its token".
  - Added:
    - "set `DXP_BASE_URL` to the production URL and confirm the alert links resolve (owner Luis, during A04)";
    - "keep `SLACK_WEBHOOK_URL` only in `.env` and the Modal secret".
  - The README's prepared material lists the Slack webhook and its channel, created and tested before the event. Any script used for that test is not reused; the notifier is written during the event.
- **S13. What is not changed.** Grants, policy sets, admissions, stop, decisions, apply, the selected set, aliases, the team scope, pacing and the reset all stay as D1 to D40 define them, with GitHub replaced by Slack.

## Who changes what

| Item | Owner |
|---|---|
| Story 9.4 is renamed "External action: a Slack alert for diagnostic evidence" | — |
| PR A09 becomes the Slack notifier, branch `story/9.4-slack-notify` | Luis |
| PR A03 seeds the new grant actions and destination | Luis |
| PR B04 adds the `?proposal=` focus | Vlad |
| `sprint-status.yaml` maps the renamed Story 9.4 key | — |
| The required behaviour "ambiguous external result" now reads: save the action ID first; if the outcome is uncertain, mark it `unknown` and never retry; a Reviewer resolves it in DxP | — |
