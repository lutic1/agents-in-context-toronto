---
name: DxProvida (DxP)
description: A discovery agent for lung cancer diagnostic evidence, every claim and relationship backed by quotes. shadcn/ui on Next.js 16 with Tailwind; this file specifies the brand layer only.
status: final  # revised for the pivot, 13 Nov, the readiness fixes, 14 Nov (readiness-fixes-2026-11-14.md), and the Slack change, 14 Nov (sprint-change-proposal-2026-11-14-slack.md)
created: 2026-11-13
updated: 2026-11-14
sources:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-discovery-agent.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-14-slack.md
  - _bmad-output/planning-artifacts/readiness-fixes-2026-11-14.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-11-13.md
  - _bmad-output/planning-artifacts/epics.md
  - _bmad-output/planning-artifacts/prds/prd-agents-in-context-toronto-2026-11-12/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-agents-in-context-toronto-2026-11-13/ARCHITECTURE-SPINE.md
colors:
  # Brand overrides on top of shadcn defaults. Light mode only on Saturday [ASSUMPTION].
  background: '#F6F8FB'        # slide: cool glass-slide white, page background
  card: '#FFFFFF'              # coverslip: panels and table surfaces
  foreground: '#23264F'        # haematoxylin ink: all body text, primary actions
  muted-foreground: '#5A5F7D'  # faded ink: captions, source lines, secondary text
  border: '#CDD3E0'            # slide rule: table rules, panel edges
  primary: '#23264F'           # haematoxylin ink
  primary-foreground: '#FFFFFF'
  ink-tint: '#E3E5F3'          # haematoxylin wash: selected row, hover, quote rule
  eosin: '#D2457A'             # new or changed: fills, rings, dots (never text)
  eosin-text: '#B8325F'        # new or changed: text and icons (5.7:1 on white)
  eosin-tint: '#F7DCE6'        # new or changed: row and chip background
  low-confidence: '#9A6512'    # ochre: low-confidence marker, text-safe on white
  accepted: '#2F7F73'          # methyl green: accepted decisions
  # Graph node types, each from a real histology stain
  node-diagnostic: '#23264F'   # haematoxylin
  node-biomarker: '#2F7F73'    # methyl green
  node-trial: '#8A5A2B'        # DAB chromogen brown
  node-drug: '#3F6FB5'         # toluidine blue
  node-tumour: '#6E4C9E'       # Giemsa violet
  node-provider: '#7A8194'     # unstained grey
  # Glass layer (v2): frosted coverslips over a defocused stained-tissue field
  field-base: '#EEF0F8'        # page base under the tissue field
  field-haematoxylin: '#6F6BC2' # blurred nuclei, 18-28% opacity in the field
  field-eosin: '#E78AAE'       # blurred cytoplasm, 18-28% opacity in the field
  field-green: '#7FC2B5'       # blurred counterstain, 12-18% opacity in the field
  glass: '#FFFFFFB8'           # panel fill, white at 72%
  glass-strong: '#FFFFFFE0'    # top bar and dense tables, white at 88%
  glass-edge: '#FFFFFFCC'      # 1px top-left highlight edge
  glass-shadow: '#23264F1F'    # ink-tinted shadow at 12%
  ink-deep: '#171A3D'          # top bar active pill, primary button gradient end
  # brand-lavender and brand-violet were the prepared logo's colours. Not used on
  # Saturday unless an organiser clears the logo in writing (readiness fix D1).
  brand-lavender: '#A78ED5'    # cleared logo only: D and P
  brand-violet: '#8B6EC2'      # cleared logo only: the twisted x
typography:
  display:
    fontFamily: 'Atkinson Hyperlegible Next'
    fontSize: 34px
    fontWeight: '700'
    lineHeight: '1.15'
    letterSpacing: -0.01em
  title:
    fontFamily: 'Atkinson Hyperlegible Next'
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.25'
  heading:
    fontFamily: 'Atkinson Hyperlegible Next'
    fontSize: 19px
    fontWeight: '600'
    lineHeight: '1.3'
  body:
    fontFamily: 'Atkinson Hyperlegible Next'
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  table:
    fontFamily: 'Atkinson Hyperlegible Next'
    fontSize: 15px
    fontWeight: '400'
    lineHeight: '1.4'
  caption:
    fontFamily: 'Atkinson Hyperlegible Next'
    fontSize: 13px
    fontWeight: '400'
    lineHeight: '1.4'
  quote:
    fontFamily: 'Source Serif 4'
    fontSize: 17px
    fontWeight: '400'
    lineHeight: '1.6'
  identifier:
    fontFamily: 'Atkinson Hyperlegible Mono'
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.4'
rounded:
  sm: 4px
  md: 10px
  lg: 18px
  xl: 24px
  full: 9999px
spacing:
  # Tailwind 4-based scale inherited. Named tokens below only.
  page-gutter: 32px
  panel-gap: 24px
  content-max: 1360px
components:
  glass-panel:
    background: '{colors.glass}'
    backdrop: 'blur(20px) saturate(150%)'
    border: '1px solid {colors.glass-edge}'
    shadow: '0 1px 0 {colors.glass-edge} inset, 0 12px 32px -12px {colors.glass-shadow}'
    radius: '{rounded.lg}'
  wordmark:
    text: 'DxP, typed text built during the event (no image)'
    font: 'Atkinson Hyperlegible Next, 700, 22px in the top bar'
    color: '{colors.foreground}'
    logo-images: 'imports/ PNGs only if an organiser clears them in writing'
  icon:
    set: 'lucide-react (ships with shadcn/ui)'
    stroke: '1.75px'
    size: '18px in navigation and buttons, 16px inline'
  button-primary:
    background: 'linear-gradient {colors.primary} to {colors.ink-deep}'
    foreground: '{colors.primary-foreground}'
    radius: '{rounded.md}'
  stage-track:
    filled: '{colors.foreground}'
    empty: 'outline {colors.border}'
    early-research: '{colors.ink-tint}'
    radius: '{rounded.sm}'
  evidence-quote:
    font: '{typography.quote}'
    rule: '{colors.ink-tint}'
    source-font: '{typography.caption}'
    source-color: '{colors.muted-foreground}'
  changed-mark:
    dot: '{colors.eosin}'
    text: '{colors.eosin-text}'
    background: '{colors.eosin-tint}'
  early-research-badge:
    background: '{colors.ink-tint}'
    foreground: '{colors.foreground}'
    border: '1px dashed {colors.foreground}'
    radius: '{rounded.full}'
  capability-tag:
    background: 'transparent'
    foreground: '{colors.muted-foreground}'
    border: '1px solid {colors.border}'
    radius: '{rounded.sm}'
    font: '{typography.caption}'
  synthetic-badge:
    background: 'transparent'
    foreground: '{colors.muted-foreground}'
    border: '1px dotted {colors.muted-foreground}'
    radius: '{rounded.full}'
  # Governed agent (pivot, 13 Nov). Existing tokens only; no new colours.
  identity-card:
    background: '{colors.card}'
    radius: '{rounded.lg}'
    label: '{typography.caption} {colors.muted-foreground}'
    value: '{typography.body} {colors.foreground}'
    identifiers: '{typography.identifier}'
  action-row:
    background: '{colors.card}'
    radius: '{rounded.md}'
    font: '{typography.table}'
    time: '{typography.identifier}, tabular figures'
    selected: '{colors.ink-tint}'
  action-state-pending:
    # allowed (queued), dispatching (claimed, in flight)
    foreground: '{colors.muted-foreground}'
    icon: 'lucide shield-check, send'
  action-state-took-effect:
    # includes "Proposal filed (pending review)": the filing took effect, the record has not changed
    foreground: '{colors.accepted}'
    icon: 'lucide circle-check'
  action-state-delivered:
    # Slack answered HTTP 200 ok. The proposal is still pending until a Reviewer decides it in DxP.
    foreground: '{colors.accepted}'
    icon: 'lucide bell'
    label: '"Slack alert delivered" and the time posted in {typography.identifier}'
  action-state-blocked:
    foreground: 'shadcn destructive (inherited)'
    rule: '3px left rule, shadcn destructive'
    icon: 'lucide shield-x'
  action-state-unknown:
    # timeout, connection error or 5xx from Slack; never retried; a Reviewer resolves it in DxP
    foreground: '{colors.low-confidence}'
    icon: 'lucide circle-help'
    label: '"Result unknown", the copyable action ID, and "Check #all-mango-db-hackathon for {action_id}, then resolve"'
  action-state-reconciling:
    # read-time only: abandoned admission, dispatching action being settled by the background sweep
    foreground: '{colors.low-confidence}'
    icon: 'lucide refresh-cw (static, no spin)'
  action-state-failed:
    # Slack refused it (4xx, or a second 429), or a queued action of an abandoned admission (reason abandoned_before_send)
    foreground: 'shadcn destructive (inherited)'
    icon: 'lucide circle-x'
  resolve-control:
    # unknown Slack alert only, in the Run console and the Audit view; shown only when the signed-in principal's actions (GET /whoami) include resolve_notification
    button: 'secondary variant, lucide square-check, label "Resolve"'
    form: 'inline under the row: radio "Delivered: I found it in the channel" / "Failed: it is not in the channel", required note (Textarea), primary "Save resolution"'
    resolved: 'the chosen state mark, plus "Resolved by {reviewer} at {time}" in {typography.caption}'
  report-not-found:
    # /reports/[report_id] with an unknown ID (replaces proposal-focus; /review?proposal= is replaced by the report page)
    notice: 'inline notice on {colors.card}, lucide search-x, "Report not found. Open Reports to see what is pending."'
  # Discovery agent (discovery-agent change, 14 Nov). Existing tokens only; no new colours.
  relationship-label:
    # supports, contradicts, extends, new question: needs two checked quotes. Never eosin (change) and never destructive (error).
    shape: 'chip, {rounded.sm}, 1px solid {colors.border}, {colors.card} fill, {typography.caption} at weight 600'
    foreground: '{colors.foreground}'
    supports: 'lucide equal, "Supports"'
    contradicts: 'lucide equal-not, "Contradicts" (neutral ink, never red)'
    extends: 'lucide git-branch-plus, "Extends"'
    new-question: 'lucide message-circle-question, "New question"'
    related-no-relationship: 'lucide minus, 1px dashed {colors.border}, {colors.muted-foreground}, "Related (no relationship established)"'
    quotes: 'two {components.evidence-quote} side by side, headed "New evidence" and "Related evidence" in {typography.caption}'
  similarity-score:
    figure: '{typography.identifier}, tabular figures, {colors.muted-foreground}'
    label: '"(similarity, not evidence)" in {typography.caption}, {colors.muted-foreground}; never a bar, meter or percentage'
  text-search-fallback:
    # shown when related retrieval used Atlas Search text search instead of Vector Search
    note: 'lucide text-search, "Related by text search (Vector Search unavailable)" in {typography.caption}, {colors.low-confidence}, beside the panel heading'
    score-label: '"(text score, not evidence)"'
  memory-chip:
    shape: 'chip, {rounded.sm}, {colors.ink-tint} fill, 1px solid {colors.border}'
    icon: 'lucide brain, 16px'
    id: '{typography.identifier} (M1)'
    author: '{typography.caption}, "Sam" plus {components.synthetic-badge}, and the date'
    effect: 'below the chip: "Before" label, the old text struck through in {colors.muted-foreground}; "After" label, the new text in {colors.foreground}; both in {typography.body} sans (DxP words, never serif)'
  memory-status-active:
    foreground: '{colors.foreground}'
    icon: 'lucide brain'
    label: '"Active" and the version ("v1")'
  memory-status-corrected:
    foreground: '{colors.muted-foreground}'
    icon: 'lucide history'
    label: '"Corrected" and "Replaced by {id} v{n}" (linked)'
  memory-status-revoked:
    foreground: '{colors.muted-foreground}'
    icon: 'lucide ban'
    label: '"Revoked by {reviewer} at {time}"; memory text struck through; the word carries the meaning, not the strike'
  pending-badge:
    background: '{colors.card}'
    foreground: '{colors.muted-foreground}'
    border: '1px dashed {colors.muted-foreground}'
    icon: 'lucide clock'
    label: '"Pending review"'
    radius: '{rounded.full}'
  accepted-badge:
    background: '{colors.card}'
    foreground: '{colors.accepted}'
    border: '1px solid {colors.accepted}'
    icon: 'lucide circle-check'
    label: '"Accepted"'
    radius: '{rounded.full}'
  rejected-badge:
    background: '{colors.card}'
    foreground: 'shadcn destructive (inherited)'
    border: '1px solid shadcn destructive'
    icon: 'lucide circle-x'
    label: '"Rejected"'
    radius: '{rounded.full}'
  claim-blocked:
    # a draft claim failing a claim-accuracy check (V7), blocked before filing
    foreground: 'shadcn destructive (inherited)'
    rule: '3px left rule, shadcn destructive; no red fill'
    icon: 'lucide shield-x'
    label: '"Claim blocked" and, on a second line in {typography.caption}, "Claim blocked before filing: {word} needs {requirement}. The source is {status} and {has_results}."'
    draft: 'the blocked draft sentence in {typography.body} sans, struck through, labelled "Draft"'
    check: 'the failed claim check by name, with {typography.identifier} code (claim_performed_or_results)'
  task-state-recommended:
    foreground: '{colors.muted-foreground}'
    icon: 'lucide list-checks'
    label: '"Recommended. Runs only if approved."'
  task-state-authorised:
    foreground: '{colors.foreground}'
    icon: 'lucide key-round'
    label: '"Authorised by {reviewer} at {time}", the task grant in {typography.identifier} and its expiry; when task execution is off, "Follow-up task authorised; not run" (V38). No start button'
  task-state-queued:
    # V38: approval queues the task and it starts by itself; no button
    foreground: '{colors.muted-foreground}'
    icon: 'lucide clock'
    label: '"Queued: starts by itself when the current run ends", the task grant in {typography.identifier} and its expiry'
  task-state-running:
    foreground: '{colors.muted-foreground}'
    icon: 'lucide play (static)'
    label: '"Running" and "{n} of max {max} filed"'
  task-state-blocked:
    foreground: 'shadcn destructive (inherited)'
    icon: 'lucide shield-x'
    rule: '3px left rule, shadcn destructive'
    label: '"Blocked before it ran: {check} failed"'
  task-state-done:
    foreground: '{colors.accepted}'
    icon: 'lucide circle-check'
    label: '"Done. {n} related items filed (pending review)." or "Done. No matching results found among the records searched." (V42), always followed by the query, the records searched and the limit in {typography.caption}'
  task-state-stopped:
    foreground: '{colors.foreground}'
    icon: 'lucide octagon-x'
    label: '"Stopped at {time}" and totals'
  briefing-player:
    # behind the briefing flag; inside the report page, under the discovery header
    container: 'solid {colors.card} row, {rounded.md}, 1px solid {colors.border}'
    button: 'secondary variant, lucide play / pause, label "Play briefing (10 s)" / "Pause"'
    time: '{typography.identifier}, tabular figures'
    transcript: '{typography.body} sans, always visible below the button'
    caption: '"Built only from this report''s evidence fields." in {typography.caption}, {colors.muted-foreground}'
    # V29: on demand only; the transcript (the script) is always shown as text
    not-generated: 'secondary button, lucide audio-lines, "Generate briefing"; transcript visible'
    generating: 'button disabled, lucide audio-lines (static), "Preparing briefing"'
    unavailable: 'lucide volume-x, "Briefing unavailable. The script is shown above." in {colors.muted-foreground}; never destructive'
    hidden: 'renders nothing (flag off)'
  avatar-player:
    # HeyGen avatar video (V13), behind the avatar flag; next to the briefing player, same grounded script; the loop never waits on it
    container: 'solid {colors.card} panel, {rounded.md}, 1px solid {colors.border}, 16:9, beside the briefing player (stacked below it at narrow widths)'
    caption: '"Same script as the briefing, built only from this report''s evidence fields." in {typography.caption}, {colors.muted-foreground}'
    # V29: on demand only; one render for the demo report; nothing waits on it
    not-rendered: 'secondary button, lucide clapperboard, "Render avatar"'
    rendering: '{colors.ink-tint} still placeholder, lucide clapperboard (static), "Rendering avatar video. The report is ready to review now." in {colors.muted-foreground}; no progress bar or percentage'
    ready: 'poster frame, secondary button lucide play, "Play avatar video (about 20 s)"; captions on; never autoplays'
    unavailable: 'lucide video-off, "Avatar unavailable. The script is shown above; the report is unaffected." in {colors.muted-foreground}; never destructive (not an error of the loop)'
    hidden: 'renders nothing (flag off)'
  evidence-gap:
    # V26: one per report, after the uncertainties; the recommended task answers it
    container: 'solid {colors.card} row, {rounded.md}, 1px dashed {colors.border}'
    heading: 'lucide circle-dashed, "Evidence gap" in {typography.caption} at weight 600'
    question: '{typography.body} sans (DxP words, never serif)'
  record-mention:
    # V37: an assay name present in a trial record, never proof of use
    shape: 'chip, {rounded.sm}, 1px dotted {colors.muted-foreground}, {colors.card} fill'
    icon: 'lucide tag, 16px'
    label: '"Named in the record" in {typography.caption}, then the name verbatim in {typography.identifier}'
    never: 'never styled as a Diagnostic link or an accepted value; FoundationOne CDx and FoundationOne Liquid CDx are never shown as one'
  decisions-bar:
    container: 'sticky to the bottom of the main column while pending, {colors.glass-strong}, {rounded.lg}, top border 1px {colors.border}'
    approve: 'button-primary, lucide check, "Approve"'
    approve-with-correction: 'secondary variant, lucide pencil-line, "Approve with correction"'
    reject: 'outline variant in ink, turns destructive on hover and focus only, lucide x, "Reject"'
    form: 'inline Textarea under the bar, required, prompt "What should the agent do differently next time?", plus a shadcn Select "What kind of claim is this about?" (the memory claim-kind tag, V22)'
    decided: 'replaced by the accepted or rejected badge and "Accepted by Sam at {time}" / "Rejected by Sam at {time}"; after approval the line reads "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27) when the task was queued, or "Approved: 1 update accepted. Follow-up task authorised; not run." when it was not (V38)'
  stop-control:
    running: 'button-primary, lucide square icon, label "Stop run"'
    stopping: 'disabled, {colors.muted-foreground}, lucide circle-pause, "Stopping: {n} in flight"'
    stopped: 'text only, {colors.foreground}, lucide octagon-x, "Stopped"'
  audit-entry:
    timeline-rule: '1px {colors.border}'
    timestamps: '{typography.identifier}'
    quote: '{components.evidence-quote}'
    checks: 'five rows, check name and result word with icon (shield-check passed, shield-x failed)'
  after-the-run:
    heading: '{typography.heading}, "After the run"'
    entry: 'same timeline as audit-entry, links to originating run and proposal'
  # Cut (discovery-agent change, 14 Nov): the impact graph view. Kept for after the hackathon; do not build.
  graph-notification-node:
    # notification:<action_id>, one per Slack alert the run posted
    shape: 'rounded rectangle, 14 by 10px, 1.5px {colors.foreground} outline, {colors.card} fill'
    glyph: 'lucide bell at 8px inside the node'
    state: 'tooltip and list view name the state in words: delivered, failed or unknown'
  graph-context-node:
    opacity: '40%'
    label: 'word "Context" in {typography.caption}, {colors.muted-foreground}'
    changed-mark: 'never'
---

There are no mockups in this repository. The earlier key-screen mockups were removed on 13 November with the pivot, because the hackathon rules allow only work built during the event to be shown. Every screen is built on Saturday from `EXPERIENCE.md` and this file.

`sprint-change-proposal-2026-11-14-discovery-agent.md` (V1 to V24, with its section 7 cuts 1 to 5 as the baseline, then V25 to V37 from its sections 10 and 11, with V33 to V37 winning over V25 to V27) wins over this file where they disagree.

## Brand & Style

DxP is where a Director of Diagnostics checks what the evidence says about a lung cancer test before taking it into a meeting. The look comes from the bench, not the boardroom: a glass slide under a microscope, stained with haematoxylin and eosin. Haematoxylin is the ink of the whole interface. Eosin, the pink counterstain, means one thing only: this is new or has changed since you last looked.

The product's argument is that every value has a source. So the evidence is visibly literature: quotes are set in a serif, as they would appear in the paper, while everything DxP itself says is set in a clear sans. A viewer can tell at a glance which words are the source's and which are DxP's.

The single bold element is the **stage track**: the nine Lifecycle stages drawn as a short strip that fills with ink up to the current stage, with the two Early research stages washed pale. It appears on every Diagnostic, in tables, on the Record and in the graph tooltip, so the lifecycle is always visible without reading a word. Everything around it stays quiet.

**Governed agent (pivot, 13 November).** DxP is now pitched for "Agents You Can Audit": the governed agent is the product and the screens only inspect it. The visual identity is unchanged. The new surfaces (Run console, Audit view) use the same ink, glass and type; the stage track and the evidence quote stay the content, now joined by the identity card and the action row. The bold moment moves from the Home hero to the blocked action and its "Who authorised this?" answer, carried by words and icons, not by colour or motion.

**Discovery agent (14 November).** DxP is a proactive research agent: it discovers new trials, relates them to existing evidence, remembers reviewer corrections and proposes follow-up work. The visual identity is unchanged. The new centre of the product is the **report page**, read like a short review article: the discovery and its quotes at the top, related evidence argued from two quotes each, the memories that changed the wording shown as before and after, then the proposed updates and the one recommended task. The serif and sans split now does extra work: a quote is the source's words; a relationship label, a memory effect and a blocked draft are DxP's words, always in the sans. Pending and accepted look different at a glance (a dashed faded pill against a solid methyl-green pill), and both always carry a word. The bold moments are the blocks before they take effect (the team-scope block on the record's "FoundationOne CDx" mention on every take, V35, V37, and an unsupported claim when the first of the two gated drafts writes it, V21) and the memory chip's before and after, carried by words and icons, not colour or motion.

**Review of the branch (14 November, V38 to V44; approved by Luis (14 Nov)).** The follow-up task has no start button: it shows Authorised ("not run") or Queued, then Running, by itself (V38). The report's script is always shown as text, even when the briefing and avatar are cut (V41). A capped search's empty answer reads "No matching results found among the records searched", with its query, records searched and limit (V42). A scope-collection update shows its accepted state in place, with no "Accepted knowledge" link (V43). Nothing visual changes.

**Review of PR #8 and the registry check (14 November, V25 to V37).** The report's headline is a new trial signal worth investigating, never a performance claim, set in the sans like every DxP sentence. An assay name in a trial record is a mention: a dotted "Named in the record" chip with the name verbatim in mono, never a Diagnostic link, and FoundationOne CDx and FoundationOne Liquid CDx are never shown as one (V37). Every report carries one evidence gap, a quiet dashed row after the uncertainties (V26). After approval the decision line says "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27). The briefing and the avatar video are made only on demand, from "Generate briefing" and "Render avatar" buttons; the script is always on the page as text, and a failure says "unavailable" in faded ink (V29). No new colours.

**Graph-led hero: Deferred (pivot, 13 Nov).** Kept here for after the hackathon; do not build it on Saturday. Original note (v3, Luis's pick after v2 read as lacklustre): Home opens on a hero band: a dark haematoxylin field (`{colors.ink-deep}` deepening from `{colors.primary}`) with a defocused micrograph behind it, and on it a live mini network of the Team's own Diagnostics, biomarkers, trials and drugs. Nodes glow softly in their stain colours; whatever changed since the last visit glows eosin and pulses once. The welcome-back panel is a white glass panel docked over the right of the hero. Below the hero the page returns to light, solid panels. The hero is the one bold moment of the whole product; every other page stays calm.

**Glass layer (v2, after Luis asked for a more polished, pharmaceutical look).** The page sits on a defocused field of stained tissue: large, heavily blurred haematoxylin, eosin and counterstain cells, as if the slide were out of focus behind the work. Panels are frosted coverslips on top of it: translucent white, a fine highlight edge, an ink-tinted shadow. The look should sit beside a pharmaceutical company's own medical-affairs tools: confident, clean and premium, with real iconography and a clean text wordmark, never playful. The glass is the setting; the quotes, the stage track and the changed marks stay the content.

DxP inherits shadcn/ui defaults wholesale. This file specifies the brand layer: colours, type, the stage track, the evidence quote, the changed mark, and three small badges. [ASSUMPTION: light mode only on Saturday.]

## Colors

- **Slide (`{colors.background}`)** is the page. **Coverslip (`{colors.card}`)** is every panel and table surface on top of it. The two whites are close on purpose: panels separate by a rule, not by shadow.
- **Haematoxylin ink (`{colors.foreground}`, also `{colors.primary}`)** is all text, primary buttons, the filled part of the stage track and Diagnostic nodes. **Faded ink (`{colors.muted-foreground}`)** is for source lines, captions and secondary text.
- **Haematoxylin wash (`{colors.ink-tint}`)** marks a selected row, hover, the rule beside a quote, and the Early research part of the stage track.
- **Eosin** is reserved for change. `{colors.eosin}` fills dots, rings and graph highlights; `{colors.eosin-text}` is the text-safe shade; `{colors.eosin-tint}` backs a new row or chip. Never used for errors, brand decoration, buttons or hover.
- **Ochre (`{colors.low-confidence}`)** marks a low-confidence value, always with a text label.
- **Methyl green (`{colors.accepted}`)** marks an accepted decision and an action that took effect. Rejection, errors and a blocked action use shadcn's `destructive`, always with an icon and a word.
- **Action states** reuse these tokens and add no colour: pending states (allowed, dispatching) in faded ink; took effect and "Slack alert delivered" in methyl green; blocked and failed in `destructive`; unknown and reconciling in ochre, since ochre already means "not certain". Each state also carries its icon and its word, so no state relies on colour. Eosin is not an action state: it stays reserved for new or changed.
- **Discovery-agent states** also add no colour. Relationship labels are all neutral ink chips, told apart by icon and word: Contradicts is a finding, never red, and no label is green or pink. "Related (no relationship established)" is faded ink with a dashed edge. Pending review is faded ink with a dashed edge; Accepted is methyl green; Rejected is `destructive`. A claim blocked before filing and a blocked task use `destructive` with `shield-x` and words, like any blocked action. A running or recommended task is faded ink, an authorised task is ink, a done task is methyl green. Memory statuses are ink (active) or faded ink (corrected, revoked). The text-search fallback note is ochre, because it is "less certain than Vector Search". Similarity is a plain figure in faded ink, never a bar or a colour scale. The "New" eosin mark appears on the newly discovered trial only.
- **Graph node colours** (impact view cut, 14 Nov) each come from a stain used in pathology: methyl green for biomarkers, DAB brown for trials, toluidine blue for drugs, Giemsa violet for tumour types, unstained grey for providers, and haematoxylin for Diagnostics. Colour is never the only cue: each type also has its own node shape (see Components).

Avoid: gradients, a second accent, eosin used for anything except change, red used for anything except rejection and errors.

## Typography

- **Atkinson Hyperlegible Next** carries the interface. It was designed for low-vision readers by the Braille Institute, and it holds up in a screen recording compressed to 1080p, where gene names like EGFR, ALK, ROS1 and RET must stay distinct. Roles: `{typography.display}` for a Record's name and the welcome-back greeting; `{typography.title}` for page titles; `{typography.heading}` for panel headings; `{typography.body}`; `{typography.table}` for table cells; `{typography.caption}` for source lines and tags.
- **Source Serif 4** (`{typography.quote}`) is used only for Evidence quotes: words taken from a source. Nothing DxP writes appears in the serif.
- **Atkinson Hyperlegible Mono** (`{typography.identifier}`) is used only for identifiers a user may copy or compare: NCT IDs, PMIDs, PMA numbers, run IDs (`run_…`), action IDs (`act_…`), grants (`{grant_id}@v{version}`) and policy sets (`ps_ab12…`, followed by "(N policies)" in the body font).
- Sentence case everywhere. No all-caps labels. Gene symbols keep their official case (EGFR, not Egfr). Quote line length stays under 75 characters.

## Layout & Spacing

- Desktop first. The demo is recorded at 1440 × 900 [ASSUMPTION]; content sits inside `{spacing.content-max}` with `{spacing.page-gutter}` on each side.
- A single top bar holds, left to right, the "DxP" text wordmark, navigation (Run console, Reports with the pending count, Audit) and the read-only "Signed in as" chip. Impact is cut. There is no Team picker: a run is started from the Run console by choosing a grant, labelled with its Team and research scope.
- **Report page (`/reports/[report_id]`).** Main column plus the 360px right-hand column. Main column, top to bottom: discovery header (trial ID, title, source status, "New" mark, report status badge), the briefing player and the avatar video player side by side when their flags are on, supporting quotes, related evidence (one item per row, label then the two quotes side by side, then similarity), uncertainties, proposed updates with their badges, the recommended task with its state (no start button: the task starts by itself after approval when task execution is on, V38), the report's script as text (always, V41), and the sticky decisions bar. Right-hand column: the memories panel, with one capability tag. Pending reports list (`/reports`): one table panel. Accepted knowledge view (`/diagnostics/[dx_id]`): the Diagnostic name in `{typography.display}` with the stage track, a pending-reports notice when one applies, then the accepted values and trials. The capture box and "your name" picker are deferred (pivot, 13 Nov). No sidebar: tables and the graph need the width.
- Pages are one main column with an optional right-hand panel of 360px (Evidence, "Who authorised this?"). The Run impact view is cut (14 Nov).
- Run console: before a run, a "Start run" panel holds a shadcn `Select` of the grants the caller may start, each option reading `{grant_id}@v{version}` and its Team (for example "`lbdx@v1`, Team Liquid Biopsy Dx (Synthetic)"), and the primary "Start run" button. During a run, the identity card spans the top of the column, with Stop run at its right; the action feed fills the column below, newest at the top. Audit view: the identity card, then the audit entries in time order, oldest first.
- Left-aligned throughout. Numbers in tables right-aligned with tabular figures.
- The footer carries the data credits line in `{typography.caption}`.

## Elevation & Depth

Three layers, back to front:

1. **Tissue field.** Inside the hero band (deferred with the hero) and behind the Run impact view: a defocused micrograph, 40 to 70 haematoxylin nuclei 14 to 36px across at 35 to 55% opacity, blurred 4 to 8px, over soft eosin patches, so it reads as cells, not a pastel blur. Elsewhere the page is `{colors.field-base}` with five to seven very large circles in `{colors.field-haematoxylin}`, `{colors.field-eosin}` and `{colors.field-green}`, blurred 80–120px, fixed behind the page. It never moves except one slow drift when the page loads (skipped under reduced motion). Behind the Graph the field is fainter, at half these opacities, so links stay legible.
2. **Glass panels.** Glass is used only for the top bar and for panels docked over the hero or the Graph; every other panel is solid white (`{colors.card}`) with the same radius and shadow. The `glass-panel` component: `{colors.glass}` fill with `blur(20px) saturate(150%)`, a 1px `{colors.glass-edge}` edge, an inset top highlight and an ink-tinted shadow. The top bar and dense tables use `{colors.glass-strong}` so text contrast stays at AA over any part of the field.
3. **Popovers and dialogs.** shadcn defaults on white, above the glass.

Text never sits directly on the tissue field; it always sits on glass at 72% white or more, which keeps body text above 7:1 and captions above 4.5:1.

## Shapes

- `{rounded.sm}` (4px) for the stage track segments and chips.
- `{rounded.md}` (10px) for buttons, inputs and rows inside a panel.
- `{rounded.lg}` (18px) for glass panels and the graph's card.
- `{rounded.xl}` (24px) for the welcome-back panel only (deferred, pivot 13 Nov).
- `{rounded.full}` only for badges (Early research, synthetic) and round graph nodes.

## Components

shadcn components used as they ship: `Button` (secondary, outline, ghost, destructive variants), `Table`, `Dialog`, `Sheet`, `Popover`, `Tabs`, `Select`, `Command`, `Toast` (sonner), `Skeleton`, `Badge`, `Textarea`, `Checkbox`, `Progress`, `Tooltip`.

Brand-layer components:

- **Wordmark.** The interface shows a text wordmark, "DxP", typed in Atkinson Hyperlegible Next at weight 700, 22px, in `{colors.foreground}`, on the left of the top bar on glass. It is built during the event as plain text, not an image. Do not use the prepared logo images in `imports/` (such as `imports/dxp-logo-original.png`): they are used only if an organiser clears them in writing on Saturday. The favicon is the letters "DxP" or the browser default. `{colors.brand-lavender}` and `{colors.brand-violet}` belong to that prepared logo, so they are not used unless it is cleared, and never for UI states, so eosin keeps its meaning.
- **Icons.** lucide-react, the set shadcn/ui ships with, at 1.75px stroke. One icon per navigation item and per primary action: Run console `square-terminal`, Reports `file-search`, Audit `scroll-text`; Start run `play`, Stop run `square`, Who authorised this `shield-question`, External link `square-arrow-out-up-right`, Evidence source `file-text`, Trial `flask-conical`, Drug `pill`, Biomarker `dna`, Search source (action kind) `radar`, Send Slack alert (action kind) `message-square`, Resolve `square-check`, Report not found `search-x`, Approve `check`, Approve with correction `pencil-line`, Reject `x`, Correct memory `pencil-line`, Revoke memory `ban`, Play briefing `play` / `pause`. Action states: allowed `shield-check`, dispatching `send`, took effect `circle-check`, Slack alert delivered `bell`, blocked and claim blocked `shield-x`, failed `circle-x`, unknown `circle-help`, reconciling `refresh-cw`; run stopping `circle-pause`, stopped `octagon-x`. Relationships: supports `equal`, contradicts `equal-not`, extends `git-branch-plus`, new question `message-circle-question`, related with no relationship `minus`; text-search fallback `text-search`. Memory `brain` (active), `history` (corrected), `ban` (revoked). Report status: pending review `clock`, accepted `circle-check`, rejected `circle-x`. Task: recommended `list-checks`, authorised `key-round`, running `play`, blocked `shield-x`, done `circle-check`, stopped `octagon-x`. Briefing: generate and generating `audio-lines`, unavailable `volume-x`. Avatar video: render and rendering `clapperboard`, ready `play`, unavailable `video-off`. Evidence gap `circle-dashed`. Record mention `tag`. Cut or deferred with their surfaces: Impact `waypoints`, Listen `headphones`, Home `house`, Diagnostics `microscope`, Find `search`, Categories `layout-grid`, Jobs `cpu`, Flag `flag`, Export `download`. Icons sit beside words; never an icon alone without a label or tooltip.
- **Glass panel.** See Elevation & Depth. Panel headings carry their icon inline at 18px before the heading text, on the same left edge as the body; no icon circles.
- **Hero network (deferred, pivot 13 Nov).** The Team's neighbourhood from `GET /graph?focus=` (Story 5.1), drawn with the Graph view's node shapes on the dark hero: nodes in lightened stain colours with a 6px soft glow, links at 30% white, changed nodes and links eosin with the one-time pulse. Labels only on the changed nodes and the Team's biomarkers. Clicking a node opens the Graph page focused on it.
- **Navigation pill.** The active item is `{colors.ink-tint}` with ink text, not a solid ink pill.
- **Avatar.** The read-only "Signed in as" chip shows initials in a 28px circle in `{colors.ink-deep}`.

- **Button, primary.** `{colors.primary}` fill, `{colors.primary-foreground}` text, `{rounded.md}`. At most one primary button visible per panel.
- **Reject button.** Outline variant in ink; turns `destructive` on hover and focus only, so red never sits on screen at rest.
- **Stage track.** Nine segments, 16px wide by 10px high with a 3px gap, in Lifecycle order; 12 by 8px inside dense table cells. Segments up to and including the current stage are solid: `{colors.foreground}`, except discovery and assay development, which are a solid `{colors.ink-tint}` wash so an Early research Diagnostic reads pale. Later stages are hollow: a 1px `{colors.border}` outline with no fill. Filled means reached; hollow means not yet. The current stage's name follows in `{typography.caption}`. "Stage not determined" shows nine empty segments and that text. When the stage has just advanced, the newly filled segment is `{colors.eosin}` until marked as seen.
- **Evidence quote.** The quote in `{typography.quote}`, with a 3px left rule in `{colors.ink-tint}`. Below it, in `{typography.caption}` and `{colors.muted-foreground}`: source name, the identifier in `{typography.identifier}` linking to the source, and "data as of" date. A manually sourced value replaces the quote with the submitter's note and the words "Manually sourced".
- **Changed mark.** A 6px `{colors.eosin}` dot before the item and the word "New" or "Changed" in `{colors.eosin-text}`. No pink fill on list rows; `{colors.eosin-tint}` is used only behind a single chip or a single highlighted value, never across a list.
- **Early research badge.** Pill with a dashed haematoxylin border, `{colors.ink-tint}` fill, text "Early research".
- **Low-confidence marker.** The text "Low confidence" in `{colors.low-confidence}` with a small open circle; never colour alone.
- **Capability tag.** A quiet outlined tag in `{typography.caption}` naming the MongoDB capability that powers a panel, such as "Schema validation" or "Change streams". At most one per panel.
- **Synthetic badge.** Dotted-outline pill reading "Synthetic", on every synthetic Team, person who starts a run, rule, correction and recalled memory.
- **Identity card.** A solid `{colors.card}` panel at `{rounded.lg}` with the standard shadow. A two-column list of label and value: labels in `{typography.caption}` and `{colors.muted-foreground}`, values in `{typography.body}`. Rows in this order: Agent (the executing agent and model), Run (`run_…`), Started by (`initiated_by`, the principal who started the run), Grant (`{grant_id}@v{version}`, its Team and research scope), Policy set (`ps_ab12… (N policies)`), Scan cursor ("Scanning trials updated since {date}"). A follow-up task run adds "Follow-up task for report {report_id}" and "Authorised by Sam at {time}", with the task grant `task-<hex>@v1`. Run ID, grant and version, policy-set hash and model in `{typography.identifier}`, each with a copy button. "Started by" is a label and value, not an avatar, so it never reads as the "Signed in as" chip, which stays unchanged in the top bar. The run status sits beside the heading as a word with its icon ("Running", "Stopping", "Stopped"). Stop run is the panel's one primary button.
- **Action row.** A row inside the feed panel at `{rounded.md}`, `{typography.table}`. Left to right: state icon and state word, kind ("Search source", "File report" (the report-level `file_proposal` kind), "Send Slack alert", "Generate briefing", "Generate avatar video", "File related evidence"), subject (trial, Diagnostic, report or destination, `#all-mango-db-hackathon` for an alert), then the time in `{typography.identifier}` with tabular figures, right-aligned. Every state shows its icon and its word; colour only reinforces. Pending states in `{colors.muted-foreground}`. Took effect in `{colors.accepted}`. A filed report reads **"Report filed (pending review)"** with a link to the report page; it never reads "Record updated", because accepted knowledge changes only when Sam approves the report in DxP. A blocked draft claim uses the claim-blocked treatment. **Slack alert delivered** in `{colors.accepted}` with `bell`, the words "Slack alert delivered" and the time posted; it never reads "Approved", because approval happens only in DxP. **Reconciling** (read-time only: an abandoned admission, while the background sweep runs) in `{colors.low-confidence}` with `refresh-cw` and the word "Reconciling", until it becomes Unknown. **Failed** in shadcn `destructive` with `circle-x` and the word "Failed", plus the reason on a second line in `{typography.caption}`: Slack's error (for example `channel_not_found`, or a second 429) with "Not retried", or "Never sent (`abandoned_before_send`)" for a queued action of an abandoned admission. **Blocked** in shadcn `destructive`: `shield-x`, the word "Blocked" and, on a second line in `{typography.caption}`, "Blocked before it ran: {check} failed under policy set `ps_ab12…` (N policies)"; a 3px `destructive` left rule marks the row, with no red fill. **Unknown** in `{colors.low-confidence}`: `circle-help`, the words "Result unknown" and the copyable action ID (`act_…`), with "Check #all-mango-db-hackathon for {action_id}, then resolve" on a second line in `{typography.caption}`. When the signed-in principal's `actions` (from `GET /whoami`) include `resolve_notification`, a secondary "Resolve" button (`square-check`) sits at the row's right and opens the inline resolve form (`resolve-control`). Eosin never marks an action state.
- **Relationship label.** A chip at `{rounded.sm}` with a 1px `{colors.border}` edge on `{colors.card}`, the icon and the word in `{typography.caption}` at weight 600, all in ink: Supports (`equal`), Contradicts (`equal-not`), Extends (`git-branch-plus`), New question (`message-circle-question`). Under it the two checked quotes as Evidence quotes side by side, headed "New evidence" and "Related evidence". "Related (no relationship established)" uses `minus`, a dashed edge and faded ink, and shows no quote pair. Never eosin, never `destructive`, never colour-coded.
- **Similarity score.** The figure (for example 0.82) in `{typography.identifier}` with tabular figures and faded ink, followed by "(similarity, not evidence)" in `{typography.caption}`. No bar, meter, percentage or colour scale. Under the text-search fallback the panel heading carries `text-search` and "Related by text search (Vector Search unavailable)" in ochre, and each score reads "(text score, not evidence)".
- **Memory chip.** An `{colors.ink-tint}` chip at `{rounded.sm}`: `brain`, the memory ID in mono, the author with the Synthetic badge, the date and the status word. Its effect sits below: "Before" with the old text struck through in faded ink, "After" with the new text in ink, both in the sans (they are DxP's words, not a source's). The labels "Before" and "After" are always written.
- **Memory status.** Each memory shows its tags in `{typography.caption}`: the claim kind it is about (how it is retrieved, V22) and the assay it was written on. Active: `brain`, "Active" and the version, in ink. Corrected: `history`, "Corrected" and "Replaced by M1 v2", faded ink. Revoked: `ban`, "Revoked by Sam at {time}", faded ink, the memory text struck through. Correct and Revoke are ghost buttons on each memory in the panel, behind the `memory_edit` flag, opening inline forms with a required note.
- **Pending, accepted and rejected badges.** Pills at `{rounded.full}` on `{colors.card}`. Pending review: `clock`, faded ink, 1px dashed faded-ink edge. Accepted: `circle-check`, methyl green text and edge. Rejected: `circle-x`, `destructive` text and edge. Each pill always carries its word. A pending item never sits in an accepted list.
- **Claim blocked.** Same treatment as a blocked action row: `shield-x`, "Claim blocked", a 3px `destructive` left rule, no red fill. A second line in `{typography.caption}` names the requirement and the source fields ("'showed' needs reported results. The source is RECRUITING and has no posted results."). In the Audit entry the draft sentence shows in the sans, struck through and labelled "Draft", with the failed claim check by name and its code in mono, and "Nothing filed. No external call made."
- **Task states.** A word and icon beside the recommended task and on its run: Recommended (`list-checks`, faded ink), Authorised (`key-round`, ink, with the task grant in mono and the expiry; "Follow-up task authorised; not run" when task execution is off), Queued (`clock`, faded ink, "starts by itself when the current run ends", V38), Running (`play`, static, faded ink, "{n} of max {max} filed"), Blocked (`shield-x`, `destructive`, 3px left rule), Done (`circle-check`, methyl green), Stopped (`octagon-x`, ink).
- **Briefing player.** Behind the `briefing` flag, under the discovery header: a solid card row at `{rounded.md}` with the transcript (the script) always visible in the sans and "Built only from this report's evidence fields." in caption. Not generated: a secondary "Generate briefing" button (`audio-lines`); nothing is generated automatically (V29). Generating: disabled button, `audio-lines` (static), "Preparing briefing". Ready: a secondary button "Play briefing (10 s)" (`play`, then `pause`) and the elapsed time in mono. Unavailable: `volume-x` and "Briefing unavailable. The script is shown above." in faded ink. Hidden (flag off): renders nothing. Never autoplays.
- **Avatar video player.** Behind the `avatar` flag, next to the briefing player: a solid card at `{rounded.md}`, 16:9, with the caption "Same script as the briefing, built only from this report's evidence fields." Not rendered: a secondary "Render avatar" button (`clapperboard`); nothing renders automatically, and for the demo one render is requested for the demo report only (V29). Rendering: an `{colors.ink-tint}` still with `clapperboard` (static) and "Rendering avatar video. The report is ready to review now.", no progress bar. Ready: a poster frame and a secondary "Play avatar video (about 20 s)" button (`play`), captions on, never autoplays. Avatar unavailable: `video-off` and "Avatar unavailable. The script is shown above; the report is unaffected." in faded ink, never `destructive`. Hidden (flag off): renders nothing. The video frame is the only moving image in the product, and only when the user presses play.
- **Decisions bar.** Sticky at the bottom of the report's main column while pending, on `{colors.glass-strong}`. Approve is the panel's one primary button (`check`); Approve with correction is secondary (`pencil-line`); Reject is the outline Reject button (`x`). Correction and reject open an inline required Textarea and a claim-kind Select (the memory's claim-kind tag, V22). Once decided, the bar is replaced by the badge and "Accepted by Sam at {time}" or "Rejected by Sam at {time}"; after an approval the line reads "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (V27), and the task's findings keep the Pending review pill.
- **Evidence gap.** One per report, after the uncertainties: a solid card row at `{rounded.md}` with a 1px dashed `{colors.border}` edge, `circle-dashed` and "Evidence gap" in caption weight 600, then the question in the sans (V26).
- **Record mention.** A chip at `{rounded.sm}` with a 1px dotted faded-ink edge on `{colors.card}`: `tag`, "Named in the record" in caption, then the name verbatim in mono (for example `FoundationOne CDx`). It is never a link to a Diagnostic and never an accepted value; two different devices are never collapsed into one chip (V37).
- **Report not found.** An unknown `/reports/<report_id>` shows an inline notice on `{colors.card}` with `search-x`, never a toast or an error page.
- **Stop control.** Running: primary button "Stop run" with `square`. Pressing it stops new admissions at once. Stopping: the button disables and the card shows `circle-pause` and "Stopping: {n} in flight", the count in `{typography.identifier}`, while admitted actions finish. Stopped: the button is replaced by `octagon-x`, "Stopped" and the totals. Never red: stopping is the safe action, not an error.
- **Audit entry.** A vertical timeline in a solid panel: a 1px `{colors.border}` rule on the left joins the entries, each marked by its state icon. One entry per gate decision, allowed or blocked; opening one loads `GET /decisions/<decision_id>`. Each entry: the action sentence in `{typography.heading}`, the timestamps in `{typography.identifier}`, the Evidence quote, the inputs and destination, the five checks as a short list (check name, then `shield-check` and "Passed" or `shield-x` and "Failed", with its detail), then the grant evaluated (`{grant_id}@v{version}`) and the policy set (`ps_ab12… (N policies)`) in `{typography.caption}`. A "Send Slack alert" entry adds the notification result (its state mark, the HTTP status and Slack's response, and the two link URLs sent in `{typography.identifier}`) and the report's and its proposals' live review status as a word with its icon: "Pending review" (`clock`, faded ink), "Applied by Sam at {time}" (`circle-check`, methyl green) or "Rejected by Sam at {time}" (`circle-x`, `destructive`). The webhook URL never appears. A blocked entry ends with "No record changed. No external call made." in `{typography.body}`. "Who authorised this?" is an outline button with `shield-question`; the answer, built from the Decision's `authorised_by`, opens in the right-hand panel as plain sentences, identifiers in mono. Blocked, failed, unknown and reconciling entries use the same marks as the action row; an unknown entry carries the same Resolve button, under the same rule. A "File report" entry adds the retrieval (method, top-k, each score as a similarity score), the memory chips with their before and after, and the relationship labels with both quotes. A claim-blocked entry uses the claim-blocked treatment. There is no briefing link or player in the Audit view; the briefing lives on the report page.
- **After the run.** A section below the run's entries in the Audit view, headed "After the run" in `{typography.heading}`, using the same timeline. Each entry is a Reviewer decision (accept, edit, reject, or resolving an unknown Slack alert) with the Reviewer ("Decided by Sam" or "Resolved by Sam", no agent), the time, and links to the originating run and proposal or action. Its evidence check reads "Not applicable"; an edit or reject shows its reason, and a resolve shows its outcome and note.
- **Graph nodes.** Diagnostic: circle, 10px, `{colors.node-diagnostic}`, sized up to 16px by number of links, with a dashed outline when Early research. Biomarker: rounded square, `{colors.node-biomarker}`. Trial: diamond, `{colors.node-trial}`. Drug: triangle, `{colors.node-drug}`. Tumour type: hexagon, `{colors.node-tumour}`. Provider: small hollow square, 1.5px `{colors.node-provider}` outline. Notification (`notification:<action_id>`, one per Slack alert the run posted): rounded rectangle with a 1.5px `{colors.foreground}` outline and a `bell` glyph, its state (delivered, failed or unknown) named in the tooltip and the list view, never by colour alone. Links in `{colors.border}`, 1px; links that cross Categories in `{colors.muted-foreground}`, 1.5px. Changed nodes and links get a 3px `{colors.eosin}` ring or stroke. Labels in `{typography.caption}` appear on hover and at zoom levels where they do not overlap. **Run impact view:** by default only the changed elements (attributed to the run) are drawn. "Show context" is an outline button that adds a touched Diagnostic's other neighbours as context nodes: 40% opacity, no eosin ring, and the word "Context" in their label and tooltip, so they never read as attributed to the run.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Use eosin only for new or changed, as a dot and a word | Use eosin for buttons, errors, decoration or row fills |
| Set every source quote in Source Serif 4 | Set anything DxP writes in the serif |
| Show the stage track wherever a Diagnostic appears | Show the stage as text alone in tables |
| Pair every colour signal with a word or shape | Rely on colour alone for confidence, change, node type or action state |
| Mark a blocked action with `destructive`, `shield-x` and "Blocked" | Use eosin for blocked, or fill a blocked row red |
| Mark a delivered Slack alert with `bell` and "Slack alert delivered", and an unknown one with `circle-help` and "Result unknown" | Show a delivered alert as "Approved", or show the webhook URL anywhere |
| Float content on frosted glass over the tissue field | Put text straight on the field, or use glass without the field behind it |
| Use lucide icons beside labels | Use emoji, icon-only buttons without labels, or a second icon set |
| Keep one capability tag per panel, quiet | Add MongoDB logos or badges to every element |
| Use sentence case and official gene symbols | Use all-caps labels or recased gene names |
| Show a relationship label with its icon, its word and two quotes | Colour-code relationships, or style Contradicts as an error |
| Show similarity as a plain figure with "(similarity, not evidence)" | Show similarity as a percentage, bar or "match" |
| Say "Related by text search" when the fallback was used | Show "Vector Search" when it was not used |
| Show a memory's effect as labelled Before and After | Say "the AI learned" or present a memory as a rule |
| Mark pending with the dashed "Pending review" pill and accepted with the methyl-green "Accepted" pill | Put pending items in an accepted list, or rely on the pill colour alone |
| Mark a blocked claim with `destructive`, `shield-x`, "Claim blocked" and the failed check | Hide the blocked draft, or fill the row red |
| Keep the briefing transcript visible and the audio user-started | Autoplay the briefing |
| Show the avatar video's state in words ("Rendering", "Avatar unavailable") and let the report work without it | Block the report on the render, show a fake progress bar, or autoplay the video |
| Make the briefing and the avatar only on demand ("Generate briefing", "Render avatar"), with the script always on the page | Generate media automatically for every report, or hide the script when a service fails |
| Show an assay name from a trial record as a "Named in the record" chip, verbatim | Show it as proof the trial used the product, link it as a Diagnostic, or merge FoundationOne CDx with FoundationOne Liquid CDx |
| Say "Approved: 1 update accepted. Follow-up task authorised; its findings will be pending review." (task queued) or "… Follow-up task authorised; not run." (V38) | Show the task's findings as accepted because the report was approved; add a button to start the task |
| Show "No matching results found among the records searched" with the query, records searched and limit (V42) | Say a capped search proved that no qualifying study has posted results |
