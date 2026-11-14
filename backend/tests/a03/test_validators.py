"""Each validator accepts a good document and rejects a bad one (Story 9.2, A03 done-when).

The local tests read the `$jsonSchema` with `jsonschema_lite`; the Atlas tests
(only with `MONGODB_URI`) insert into a fresh test database and expect Atlas
itself to refuse, including the `$expr` rules the local reader does not check.
"""

from __future__ import annotations

import copy
from datetime import timedelta

import pytest
from pymongo.errors import WriteError

from dxp.store import schemas

from .examples import BAD_CHANGES, NOW, bad_document, by_id, seeded, task_grant, valid_documents
from .jsonschema_lite import validate


def ok(collection: str, doc: dict) -> bool:
    return not validate(schemas.validator(collection), doc)


# --- Every collection named in "Contracts come first" has a strict validator ----------


def test_every_contract_collection_has_a_validator():
    expected = {
        "grants",
        "policies",
        "policy_sets",
        "runs",
        "admissions",
        "decisions",
        "actions",
        "research_scopes",
        "reports",
        "memories",
        "tasks",
        "media",
        "source_versions",
        "proposals",
    }
    assert expected <= set(schemas.COLLECTIONS)
    for name in schemas.COLLECTIONS:
        options = schemas.collection_options(name)
        assert options["validationLevel"] == "strict"
        assert options["validationAction"] == "error"
        assert "$jsonSchema" in options["validator"]


def test_validator_answers_for_every_store_collection():
    """A01's `ensure_indexes()` asks for every collection; one without a validator gets None."""
    from dxp import store

    for name in store.COLLECTIONS:
        result = schemas.validator(name)
        assert result is None or "$jsonSchema" in result
    assert schemas.validator("aliases") is None
    assert schemas.validator("grants")["$jsonSchema"] is schemas.VALIDATORS["grants"]


@pytest.mark.parametrize("collection", sorted(valid_documents()))
def test_valid_document_passes(collection):
    assert validate(schemas.validator(collection), valid_documents()[collection]) == []


@pytest.mark.parametrize("collection,path,value,why", BAD_CHANGES, ids=[c[3] for c in BAD_CHANGES])
def test_bad_document_is_rejected(collection, path, value, why):
    assert validate(schemas.validator(collection), bad_document(collection, path, value)), why


def test_scope_scan_config_is_optional(tmp_path, keys):
    scope = copy.deepcopy(seeded(tmp_path, keys)["research_scopes"][0])
    assert ok("research_scopes", scope)
    for key in ("condition_aliases", "priority_refs"):
        assert ok("research_scopes", {k: v for k, v in scope.items() if k != key})


def test_every_validated_collection_has_a_rejection_case():
    covered = {c[0] for c in BAD_CHANGES} | {"grants", "policies", "research_scopes"}
    assert covered == set(schemas.COLLECTIONS)


def test_v48_statuses_validate():
    docs = valid_documents()
    for status in ("reverting", "reverted"):
        assert ok("reports", {**docs["reports"], "status": status})
    assert ok("tasks", {**docs["tasks"], "status": "cancelled"})
    remove = {**docs["proposals"], "op": "remove", "reverts_proposal_id": "p_" + "e" * 16, "status": "applied"}
    assert ok("proposals", remove)


# --- Seeded grants, policies and scope ------------------------------------------------


def test_seeded_documents_validate(tmp_path, keys):
    built = seeded(tmp_path, keys)
    for collection in ("grants", "policies", "research_scopes"):
        for doc in built[collection]:
            assert validate(schemas.validator(collection), doc) == [], doc["_id"]


@pytest.fixture
def grants(tmp_path, keys):
    return by_id(seeded(tmp_path, keys)["grants"])


def test_scope_all_is_rejected_unless_principal_is_seed(grants):
    lbdx = copy.deepcopy(grants["lbdx@v1"])
    lbdx["scope"] = {"all": True}
    assert not ok("grants", lbdx)
    sam = copy.deepcopy(grants["sam@v1"])
    sam["scope"] = {**sam["scope"], "all": True}
    assert not ok("grants", sam)
    impostor = copy.deepcopy(grants["seed@v1"])
    impostor["principal"] = "dxp-curator"
    assert not ok("grants", impostor)
    assert ok("grants", grants["seed@v1"])


@pytest.mark.parametrize(
    "grant_id,field,value,why",
    [
        ("lbdx@v1", "actions", ["search_source", "decide_report"], "an agent grant with a human kind"),
        ("sam@v1", "actions", ["decide_proposal"], "decide_proposal is superseded and granted to no one"),
        ("sam@v1", "actions", ["apply_value"], "apply_value belongs to the seed grant"),
        ("lbdx@v1", "destinations", ["ledger", "slack:#general"], "an unknown destination"),
        ("lbdx@v1", "status", "paused", "an unknown grant status"),
        ("lbdx@v1", "key_hash", "not-a-hash", "a key hash that is not SHA-256 hex"),
        ("lbdx@v1", "expires_at", "2026-11-16", "an expiry that is not a date"),
        ("seed@v1", "actions", ["apply_value", "file_proposal"], "the seed grant with another action"),
        (
            "lbdx@v1",
            "scope",
            {"scope_id": "scope_plasma_ctdna_nsclc", "diagnostic_ids": []},
            "an empty Diagnostic scope",
        ),
    ],
)
def test_bad_grant_is_rejected(grants, grant_id, field, value, why):
    doc = copy.deepcopy(grants[grant_id])
    doc[field] = value
    assert not ok("grants", doc), why


def test_sam_carries_revert_report_from_the_start(grants):
    assert "revert_report" in grants["sam@v1"]["actions"]


def test_task_grant_validates_and_its_expired_v2_too(grants):
    lbdx = grants["lbdx@v1"]
    assert ok("grants", task_grant(lbdx))
    assert ok("grants", task_grant(lbdx, version=2, status="expired", expires_at=NOW, created_at=NOW))
    assert ok("grants", task_grant(lbdx, kind="task"))


@pytest.mark.parametrize(
    "overrides,why",
    [
        ({"actions": ["search_source", "file_related_evidence", "notify_slack"]}, "a task grant with an extra action"),
        (
            {"destinations": ["source:clinicaltrials.gov", "slack:#all-mango-db-hackathon"]},
            "a task grant posting to Slack",
        ),
        ({"limits": {"max_results": 6}}, "a task grant above 5 results"),
        ({"limits": None}, "a task grant with no limit"),
        ({"key_hash": "a" * 64}, "a task grant with a key"),
        ({"scope": {"all": True}}, "a task grant with scope all"),
        ({"task_id": None}, "a task grant with no task"),
    ],
)
def test_bad_task_grant_is_rejected(grants, overrides, why):
    assert not ok("grants", task_grant(grants["lbdx@v1"], **overrides)), why


def test_kind_task_only_on_a_task_grant(grants):
    lbdx = copy.deepcopy(grants["lbdx@v1"])
    lbdx["kind"] = "task"
    assert not ok("grants", lbdx)


@pytest.mark.parametrize(
    "field,value,why",
    [
        ("requires", {"quote_found": True, "run_shell": "rm"}, "requires accepts only its four keys"),
        ("requires", {"claim_checks": ["claim_vibes"]}, "an unknown claim check"),
        ("requires", {}, "a policy that requires nothing"),
        ("status", "enabled", "an unknown policy status"),
        ("applies_to", ["decide_proposal"], "a superseded kind"),
    ],
)
def test_bad_policy_is_rejected(tmp_path, keys, field, value, why):
    policy = copy.deepcopy(by_id(seeded(tmp_path, keys)["policies"])["claim_planned@v1"])
    policy[field] = value
    assert not ok("policies", policy), why


@pytest.mark.parametrize(
    "path,value,why",
    [
        ("cursor.last_update_post_date", "14 Nov 2026", "a cursor that is not YYYY-MM-DD"),
        ("source", "pubmed", "a scope on another source"),
        ("assays", [], "a scope with no assays"),
        ("version", None, "a scope without its version"),
        ("condition_aliases", "NSCLC", "condition aliases that are not a list"),
        ("condition_aliases", [""], "an empty condition alias"),
        ("priority_refs", ["04712877"], "a priority ref that is not an NCT ID"),
        ("priority_refs", ["NCT04712877", "NCT04712877"], "a repeated priority ref"),
    ],
)
def test_bad_scope_is_rejected(tmp_path, keys, path, value, why):
    scope = copy.deepcopy(seeded(tmp_path, keys)["research_scopes"][0])
    target = scope
    *parents, last = path.split(".")
    for part in parents:
        target = target[part]
    target[last] = value
    assert not ok("research_scopes", scope), why


# --- Atlas: the database itself refuses -------------------------------------------------


def _atlas_cases(tmp_path, keys):
    built = seeded(tmp_path, keys)
    grants = by_id(built["grants"])
    lbdx = grants["lbdx@v1"]
    good = [(c, d) for c, d in valid_documents().items()]
    good += [("grants", g) for g in built["grants"]] + [("policies", p) for p in built["policies"]]
    good += [("research_scopes", s) for s in built["research_scopes"]]
    good += [
        ("grants", task_grant(lbdx)),
        ("grants", task_grant(lbdx, version=2, status="expired", expires_at=NOW, created_at=NOW)),
    ]
    bad = [(c, bad_document(c, p, v), why) for c, p, v, why in BAD_CHANGES]
    bad_scope_all = copy.deepcopy(lbdx)
    bad_scope_all.update(_id="lbdx@v9", version=9, scope={"all": True})
    bad += [
        ("grants", bad_scope_all, "scope all on a non-seed grant"),
        (
            "grants",
            {**task_grant(lbdx), "_id": "task-" + "f" * 16 + "@v1", "grant_id": "task-" + "f" * 16},
            "a task grant whose ID is not its task's ($expr)",
        ),
        (
            "grants",
            task_grant(lbdx, version=3, expires_at=NOW + timedelta(hours=2)),
            "a task grant over one hour ($expr)",
        ),
        ("grants", {**copy.deepcopy(lbdx), "_id": "lbdx@v7"}, "_id not grant_id@v<version> ($expr)"),
        (
            "grants",
            task_grant(lbdx, version=4, actions=["search_source", "notify_slack"]),
            "a task grant with another action",
        ),
    ]
    return good, bad


@pytest.mark.atlas
async def test_atlas_rejects_bad_documents(db, tmp_path, keys):
    """Atlas itself refuses: the validators as `store.ensure_indexes()` applied them (A01's `db`)."""
    good, bad = _atlas_cases(tmp_path, keys)
    inserted: list[tuple[str, str]] = []
    try:
        for collection, doc in good:
            await db[collection].insert_one(copy.deepcopy(doc))
            inserted.append((collection, doc["_id"]))
        for collection, doc, why in bad:
            with pytest.raises(WriteError) as caught:
                await db[collection].insert_one(copy.deepcopy(doc))
            assert caught.value.code == 121, why  # DocumentValidationFailure
    finally:
        for collection, doc_id in inserted:
            await db[collection].delete_one({"_id": doc_id})


@pytest.mark.atlas
async def test_atlas_validators_are_strict_and_reapply(db):
    await schemas.apply(db)  # idempotent beside store.ensure_indexes()
    info = {c["name"]: c["options"] async for c in await db.list_collections()}
    for name in schemas.COLLECTIONS:
        assert info[name]["validationLevel"] == "strict"
        assert info[name]["validationAction"] == "error"
        assert info[name]["validator"] == schemas.validator(name)
