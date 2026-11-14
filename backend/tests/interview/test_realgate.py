"""The interview lane against main's REAL gate, on A06's seeded fake world (red team 4: every other test here uses
`fake_gate`, which hid the missing ID target). Skipped when A06's world is not in the tree."""

from __future__ import annotations

import pytest

a06 = pytest.importorskip("a06.conftest", reason="A06's seeded world is on main, not on this branch")
world = a06.world  # the fixture

from dxp.api import models as m  # noqa: E402
from dxp.interview import service, texts  # noqa: E402

from .conftest import REPORT_ID, make_ctx  # noqa: E402


def reviewer_ctx(w, actions=None, grant_version: int = 2, request_id: str = "req_real_1") -> m.RunContext:
    ctx = make_ctx(actions)
    return ctx.model_copy(
        update={
            "policy_set_version": w.policy_set_version,
            "grant_version": grant_version,
            "request_id": request_id,
            "cause": m.DecisionCause(report_id=REPORT_ID, origin_run_id=w.run_id),
        }
    )


async def decisions_of(w) -> list[dict]:
    return [d async for d in w.db["decisions"].find({"kind": "answer_question"})]


async def test_a_question_is_answered_on_the_real_gate_with_one_decision(world, store, fake_llm, settled) -> None:
    ctx = reviewer_ctx(world)
    response = await service.answer_question(REPORT_ID, "What is the status of this trial?", ctx)
    assert response.refused is False and response.citations and response.decision_id.startswith("dec_")
    [decision] = await decisions_of(world)
    assert decision["_id"] == response.decision_id and decision["outcome"] == "allowed"
    assert decision["stamp"]["kind"] == "reviewer" and decision["stamp"]["run_id"] is None
    assert decision["inputs"]["outcome"] == "answered" and decision["inputs"]["id_target"] == REPORT_ID
    assert decision["inputs"]["cited"][0]["version_id"] == "sv_aaaaaaaaaaaaaaaa"
    assert [c["passed"] for c in decision["inputs"]["claim_checks"]] == [True]


async def test_every_kind_of_reply_records_one_decision_each(world, store, fake_llm, settled) -> None:
    questions = ["What is the status?", "Should I join this trial?", "What is the Moon?", "What is the study design?"]
    for number, question in enumerate(questions):
        await service.answer_question(REPORT_ID, question, reviewer_ctx(world, request_id=f"req_real_{number}"))
    outcomes = sorted(d["inputs"]["outcome"] for d in await decisions_of(world))
    assert outcomes == ["answered", "answered", "not_in_record", "refused_medical_advice"]
    assert len({d["_id"] for d in await decisions_of(world)}) == 4, "each question is its own Decision"


async def test_the_action_is_settled_on_the_real_gate(world, store, fake_llm) -> None:
    response = await service.answer_question(REPORT_ID, "What is the status?", reviewer_ctx(world))
    decision = await world.db["decisions"].find_one({"_id": response.decision_id})
    action = await world.db["actions"].find_one({"decision_id": response.decision_id})
    assert action is not None and action["status"] == "done", action
    assert action["result"]["outcome"] == "answered" and action["result"]["cited"]
    assert decision["outcome"] == "allowed"


async def test_a_blocked_grant_is_a_refusal_with_no_model_call(world, store, fake_llm) -> None:
    # sam@v1 has no answer_question: the gate blocks, nothing is answered and the model is never asked.
    ctx = reviewer_ctx(world, actions=["answer_question"], grant_version=1)
    ctx = ctx.model_copy(update={"principal": ctx.principal.model_copy(update={"actions": ["decide_report"]})})
    response = await service.answer_question(REPORT_ID, "What is the study design?", ctx)
    assert response.refused is True and response.refusal_reason == "blocked" and response.answer == texts.BLOCKED
    assert fake_llm.calls == []


async def test_a_revoked_grant_costs_no_model_call(world, store, fake_llm) -> None:
    await world.new_grant_version("sam", "revoked")
    response = await service.answer_question(REPORT_ID, "What is the study design?", reviewer_ctx(world, grant_version=3))
    assert response.refused is True and response.refusal_reason == "blocked"
    assert fake_llm.calls == [], "the gate runs before the model, so a revoked grant never costs a model call"
