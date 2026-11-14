---
name: DxProvida (DxP)
description: Lung cancer diagnostics tracked by agents, every value backed by a quote. shadcn/ui on Next.js 16 with Tailwind; this file specifies the brand layer only.
status: final  # revised for the pivot, 13 Nov (sprint-change-proposal-2026-11-13.md)
created: 2026-11-13
updated: 2026-11-13
sources:
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
  brand-lavender: '#A78ED5'    # DxP logo: D and P (Luis's logo)
  brand-violet: '#8B6EC2'      # DxP logo: the twisted x
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
  logo:
    source: 'imports/dxp-logo-original.png (Luis)'
    colors: '{colors.brand-lavender} D and P, {colors.brand-violet} x'
    height: '28px in the top bar'
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
    # allowed (queued), dispatching, in flight (sent)
    foreground: '{colors.muted-foreground}'
    icon: 'lucide shield-check, send, clock'
  action-state-took-effect:
    foreground: '{colors.accepted}'
    icon: 'lucide circle-check'
  action-state-blocked:
    foreground: 'shadcn destructive (inherited)'
    rule: '3px left rule, shadcn destructive'
    icon: 'lucide shield-x'
  action-state-unknown:
    foreground: '{colors.low-confidence}'
    icon: 'lucide circle-help'
  stop-control:
    running: 'button-primary, lucide square icon, label "Stop run"'
    stopping: 'disabled, {colors.muted-foreground}, lucide circle-pause'
    stopped: 'text only, {colors.foreground}, lucide octagon-x'
  audit-entry:
    timeline-rule: '1px {colors.border}'
    timestamps: '{typography.identifier}'
    quote: '{components.evidence-quote}'
---

There are no mockups in this repository. The earlier key-screen mockups were removed on 13 November with the pivot, because the hackathon rules allow only work built during the event to be shown. Every screen is built on Saturday from `EXPERIENCE.md` and this file.

## Brand & Style

DxP is where a Director of Diagnostics checks what the evidence says about a lung cancer test before taking it into a meeting. The look comes from the bench, not the boardroom: a glass slide under a microscope, stained with haematoxylin and eosin. Haematoxylin is the ink of the whole interface. Eosin, the pink counterstain, means one thing only: this is new or has changed since you last looked.

The product's argument is that every value has a source. So the evidence is visibly literature: quotes are set in a serif, as they would appear in the paper, while everything DxP itself says is set in a clear sans. A viewer can tell at a glance which words are the source's and which are DxP's.

The single bold element is the **stage track**: the nine Lifecycle stages drawn as a short strip that fills with ink up to the current stage, with the two Early research stages washed pale. It appears on every Diagnostic, in tables, on the Record and in the graph tooltip, so the lifecycle is always visible without reading a word. Everything around it stays quiet.

**Governed agent (pivot, 13 November).** DxP is now pitched for "Agents You Can Audit": the governed agent is the product and the screens only inspect it. The visual identity is unchanged. The new surfaces (Run console, Audit view) use the same ink, glass and type; the stage track and the evidence quote stay the content, now joined by the identity card and the action row. The bold moment moves from the Home hero to the blocked action and its "Who authorised this?" answer, carried by words and icons, not by colour or motion.

**Graph-led hero: Deferred (pivot, 13 Nov).** Kept here for after the hackathon; do not build it on Saturday. Original note (v3, Luis's pick after v2 read as lacklustre): Home opens on a hero band: a dark haematoxylin field (`{colors.ink-deep}` deepening from `{colors.primary}`) with a defocused micrograph behind it, and on it a live mini network of the Team's own Diagnostics, biomarkers, trials and drugs. Nodes glow softly in their stain colours; whatever changed since the last visit glows eosin and pulses once. The welcome-back panel is a white glass panel docked over the right of the hero. Below the hero the page returns to light, solid panels. The hero is the one bold moment of the whole product; every other page stays calm.

**Glass layer (v2, after Luis asked for a more polished, pharmaceutical look).** The page sits on a defocused field of stained tissue: large, heavily blurred haematoxylin, eosin and counterstain cells, as if the slide were out of focus behind the work. Panels are frosted coverslips on top of it: translucent white, a fine highlight edge, an ink-tinted shadow. The look should sit beside a pharmaceutical company's own medical-affairs tools: confident, clean and premium, with real iconography and a proper logo, never playful. The glass is the setting; the quotes, the stage track and the changed marks stay the content.

DxP inherits shadcn/ui defaults wholesale. This file specifies the brand layer: colours, type, the stage track, the evidence quote, the changed mark, and three small badges. [ASSUMPTION: light mode only on Saturday.]

## Colors

- **Slide (`{colors.background}`)** is the page. **Coverslip (`{colors.card}`)** is every panel and table surface on top of it. The two whites are close on purpose: panels separate by a rule, not by shadow.
- **Haematoxylin ink (`{colors.foreground}`, also `{colors.primary}`)** is all text, primary buttons, the filled part of the stage track and Diagnostic nodes. **Faded ink (`{colors.muted-foreground}`)** is for source lines, captions and secondary text.
- **Haematoxylin wash (`{colors.ink-tint}`)** marks a selected row, hover, the rule beside a quote, and the Early research part of the stage track.
- **Eosin** is reserved for change. `{colors.eosin}` fills dots, rings and graph highlights; `{colors.eosin-text}` is the text-safe shade; `{colors.eosin-tint}` backs a new row or chip. Never used for errors, brand decoration, buttons or hover.
- **Ochre (`{colors.low-confidence}`)** marks a low-confidence value, always with a text label.
- **Methyl green (`{colors.accepted}`)** marks an accepted decision and an action that took effect. Rejection, errors and a blocked action use shadcn's `destructive`, always with an icon and a word.
- **Action states** reuse these tokens and add no colour: pending states (allowed, dispatching, in flight) in faded ink; took effect in methyl green; blocked and failed in `destructive`; unknown in ochre, since ochre already means "not certain". Eosin is not an action state: it stays reserved for new or changed.
- **Graph node colours** each come from a stain used in pathology: methyl green for biomarkers, DAB brown for trials, toluidine blue for drugs, Giemsa violet for tumour types, unstained grey for providers, and haematoxylin for Diagnostics. Colour is never the only cue: each type also has its own node shape (see Components).

Avoid: gradients, a second accent, eosin used for anything except change, red used for anything except rejection and errors.

## Typography

- **Atkinson Hyperlegible Next** carries the interface. It was designed for low-vision readers by the Braille Institute, and it holds up in a screen recording compressed to 1080p, where gene names like EGFR, ALK, ROS1 and RET must stay distinct. Roles: `{typography.display}` for a Record's name and the welcome-back greeting; `{typography.title}` for page titles; `{typography.heading}` for panel headings; `{typography.body}`; `{typography.table}` for table cells; `{typography.caption}` for source lines and tags.
- **Source Serif 4** (`{typography.quote}`) is used only for Evidence quotes: words taken from a source. Nothing DxP writes appears in the serif.
- **Atkinson Hyperlegible Mono** (`{typography.identifier}`) is used only for identifiers a user may copy or compare: NCT IDs, PMIDs, PMA numbers.
- Sentence case everywhere. No all-caps labels. Gene symbols keep their official case (EGFR, not Egfr). Quote line length stays under 75 characters.

## Layout & Spacing

- Desktop first. The demo is recorded at 1440 × 900 [ASSUMPTION]; content sits inside `{spacing.content-max}` with `{spacing.page-gutter}` on each side.
- A single top bar holds navigation (Run console, Audit, Review, Impact) and the read-only "Signed in as" chip. The capture box, Team picker and "your name" picker are deferred (pivot, 13 Nov). No sidebar: tables and the graph need the width.
- Pages are one main column with an optional right-hand panel of 360px (Evidence, "Who authorised this?"). The Run impact view is full width under the top bar.
- Run console: the identity card spans the top of the column, with Stop run at its right; the action feed fills the column below, newest at the top. Audit view: the identity card, then the audit entries in time order, oldest first.
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

- **Logo.** Luis's own DxP logo (`imports/dxp-logo-original.png`): a heavy rounded "D" and "P" in `{colors.brand-lavender}` with an "x" of two twisting strands, like a DNA double helix, in `{colors.brand-violet}`. Use it as supplied: no recolouring, outlines or effects. In the top bar it sits at 28px tall on glass; on the dark hero it can appear as is, since the lavender reads well on ink. The favicon and app icon are the twisted "x" alone. The two logo purples are used only in the logo, never for UI states, so eosin keeps its meaning.
- **Icons.** lucide-react, the set shadcn/ui ships with, at 1.75px stroke. One icon per navigation item and per primary action: Run console `square-terminal`, Audit `scroll-text`, Review `clipboard-check`, Impact `waypoints`; Start run `play`, Stop run `square`, Who authorised this `shield-question`, Open in GitHub `square-arrow-out-up-right`, Evidence source `file-text`, Trial `flask-conical`, Drug `pill`, Biomarker `dna`, Issue `circle-dot`. Action states: allowed `shield-check`, dispatching `send`, in flight `clock`, took effect `circle-check`, blocked `shield-x`, failed `circle-x`, unknown `circle-help`; run stopping `circle-pause`, stopped `octagon-x`. Deferred with their surfaces: Home `house`, Diagnostics `microscope`, Find `search`, Categories `layout-grid`, Alerts `bell`, Jobs `cpu`, Dismiss `x`, Flag `flag`, Memory `brain`, Export `download`. Icons sit beside words; never an icon alone without a label or tooltip.
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
- **Capability tag.** A quiet outlined tag in `{typography.caption}` naming the MongoDB capability that powers a panel, such as "Atlas Vector Search" or "Agent Memory". At most one per panel.
- **Synthetic badge.** Dotted-outline pill reading "Synthetic", on every synthetic Team, person acted for, rule, correction and recalled memory.
- **Identity card.** A solid `{colors.card}` panel at `{rounded.lg}` with the standard shadow. A two-column list of label and value: labels in `{typography.caption}` and `{colors.muted-foreground}`, values in `{typography.body}`. Run ID, grant ID and versions, policy-set version and model in `{typography.identifier}`, each with a copy button. The run status sits beside the heading as a word with its icon ("Running", "Stopping", "Stopped"). Stop run is the panel's one primary button.
- **Action row.** A row inside the feed panel at `{rounded.md}`, `{typography.table}`. Left to right: state icon and state word, kind ("Update record", "Open review issue"), Diagnostic and field or destination, then the time in `{typography.identifier}` with tabular figures, right-aligned. Every state shows its icon and its word; colour only reinforces. Pending states in `{colors.muted-foreground}`. Took effect in `{colors.accepted}` with the issue number as a link. **Blocked** in shadcn `destructive`: `shield-x`, the word "Blocked" and, on a second line in `{typography.caption}`, "Blocked before it ran: {check} failed under policy v{n}"; a 3px `destructive` left rule marks the row, with no red fill. **Unknown** in `{colors.low-confidence}`: `circle-help`, the words "Result unknown" and the copyable action ID. Eosin never marks an action state.
- **Stop control.** Running: primary button "Stop run" with `square`. Stopping: the button disables and the card shows `circle-pause`, "Stopping" and the in-flight count in `{typography.identifier}`. Stopped: the button is replaced by `octagon-x`, "Stopped" and the totals. Never red: stopping is the safe action, not an error.
- **Audit entry.** A vertical timeline in a solid panel: a 1px `{colors.border}` rule on the left joins the entries, each marked by its state icon. Each entry: the action sentence in `{typography.heading}`, the four timestamps in `{typography.identifier}`, the Evidence quote, then grant and policy-set versions in `{typography.caption}`. "Who authorised this?" is an outline button with `shield-question`; the answer opens in the right-hand panel as plain sentences, identifiers in mono. Blocked and unknown entries use the same marks as the action row.
- **Graph nodes.** Diagnostic: circle, 10px, `{colors.node-diagnostic}`, sized up to 16px by number of links, with a dashed outline when Early research. Biomarker: rounded square, `{colors.node-biomarker}`. Trial: diamond, `{colors.node-trial}`. Drug: triangle, `{colors.node-drug}`. Tumour type: hexagon, `{colors.node-tumour}`. Provider: small hollow square, 1.5px `{colors.node-provider}` outline. Links in `{colors.border}`, 1px; links that cross Categories in `{colors.muted-foreground}`, 1.5px. Changed nodes and links get a 3px `{colors.eosin}` ring or stroke. Labels in `{typography.caption}` appear on hover and at zoom levels where they do not overlap.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Use eosin only for new or changed, as a dot and a word | Use eosin for buttons, errors, decoration or row fills |
| Set every source quote in Source Serif 4 | Set anything DxP writes in the serif |
| Show the stage track wherever a Diagnostic appears | Show the stage as text alone in tables |
| Pair every colour signal with a word or shape | Rely on colour alone for confidence, change, node type or action state |
| Mark a blocked action with `destructive`, `shield-x` and "Blocked" | Use eosin for blocked, or fill a blocked row red |
| Float content on frosted glass over the tissue field | Put text straight on the field, or use glass without the field behind it |
| Use lucide icons beside labels | Use emoji, icon-only buttons without labels, or a second icon set |
| Keep one capability tag per panel, quiet | Add MongoDB logos or badges to every element |
| Use sentence case and official gene symbols | Use all-caps labels or recased gene names |
