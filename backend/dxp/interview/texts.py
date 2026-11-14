"""Fixed texts of the interview lane (V70). The model never writes any of these, and none is built from a question."""

from __future__ import annotations

from dxp.interview import framing

# "Reply exactly" (Luis's ruling, V70 amendment): the allowlisted sentence, with its full stop.
NOT_IN_RECORD = framing.FRAME_NOT_IN_RECORD

# A question with no intent at all (a greeting, an off-topic question): the same outcome, with what can be asked.
NO_INTENT_HELP = (
    "I can answer from this report's record: its status, dates, conditions, phase, design, interventions, sponsor, "
    "location, enrollment or posted results."
)

# One fixed refusal for a medical question. No model call is made before or after it. Built only from the
# sentences listed in `framing` (each passes the no-facts check); the import below fails if that ever stops being true.
MEDICAL_REFUSAL = " ".join(framing.MEDICAL_SENTENCES)

# Shown when the policy gate blocks the question (no grant, wrong scope, a failed claim check).
BLOCKED = " ".join(framing.BLOCKED_SENTENCES)

assert framing.is_fixed_reply(MEDICAL_REFUSAL, framing.MEDICAL_SENTENCES), "MEDICAL_REFUSAL left the allowlist"
assert framing.is_fixed_reply(BLOCKED, framing.BLOCKED_SENTENCES), "BLOCKED left the allowlist"

# The permanent label on the page (the web page shows the same words). The persona is "DxP's evidence guide".
VOICE_LABEL = (
    f"{framing.PERSONA}: reads quotes from the public record about this report. "
    "Not the manufacturer, not a clinician, not medical advice."
)

REASON_MEDICAL = "medical_advice"
REASON_NOT_IN_RECORD = "not_in_record"
REASON_BLOCKED = "blocked"
