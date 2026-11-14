"""Fixed texts of the interview lane (V70). The model never writes any of these, and none is built from a question."""

from __future__ import annotations

# "Reply exactly" (Luis's ruling): no full stop, no extra words.
NOT_IN_RECORD = "The accepted record doesn't answer that"

# One fixed refusal for a medical-advice question. No model call is made before or after it.
MEDICAL_REFUSAL = (
    "This page can't give medical advice, a diagnosis or a treatment recommendation. "
    "It only quotes the accepted public record about this report. Please ask a qualified clinician."
)

# Shown when the policy gate blocks the question (no grant, wrong scope, a failed claim check).
BLOCKED = "The policy gate blocked this question, so no answer was given. The Decision records why."

# The permanent label on the page (the web page shows the same words).
VOICE_LABEL = (
    "AI voice for DxP reading public records about this report. "
    "Not the manufacturer, not a clinician, not medical advice."
)

REASON_MEDICAL = "medical_advice"
REASON_NOT_IN_RECORD = "not_in_record"
REASON_BLOCKED = "blocked"

# Lead-ins are fixed. A sentence is one lead-in, one verbatim quote and one citation marker.
LEAD_DISCOVERY = "The accepted record says:"
LEAD_RELATED = "A related record says:"
LEAD_MENTION = "{names} {verb} named in the record:"
