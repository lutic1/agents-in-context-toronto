"""Interview this evidence (V70, interview flag): a gated, logged question about an accepted report.

The answer is built only from verbatim quotes stored on that report, in the fields of one fixed intent, with
allowlisted framing sentences. The model only ranks the eligible quotes; DxP writes the text. Medical, off-topic
and unanswerable questions are refused or answered "not in the record" before any model call. The lane reads
reports and calls `gate.evaluate` and `llm`; it writes nothing except through the gate (the Decision).
"""

from __future__ import annotations

from dxp.interview.service import answer_question

__all__ = ["answer_question"]
