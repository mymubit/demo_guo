from __future__ import annotations

import unittest
import json
from pathlib import Path

import jsonschema
from v6.engine import CallTransaction, InMemoryArtifactStore, OperationRegistry, TransactionError, VersionConflict, canonical_hash


ROOT = Path(__file__).resolve().parents[3]


class TransactionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = OperationRegistry(ROOT)

    def command(self):
        return {"episode_range": [8, 10], "change_requests": ["tighten hook"], "base_version": 3}

    def system_inputs(self):
        return {"engine_version": "6", "artifact_schema_versions": {"episode_plan": 2}, "active_rule_versions": {"catalog": 1}, "caller_identity": "test"}

    def transaction(self):
        operation = self.registry.operation("operation.revise-episode-plan")
        reads = {name: {"version": 3, "hash": canonical_hash(name)} for name in operation["reads"]}
        return CallTransaction(operation, self.command(), self.system_inputs(), reads, call_id="call-test")

    def complete_to_impact(self):
        tx = self.transaction()
        tx.set_plan({"steps": ["revise"]})
        tx.compile_execution_pack(
            self.registry.execution_persona(tx.operation["id"]),
            self.registry.execution_capabilities(tx.operation["id"]),
        )
        tx.set_candidate({"episode_plan": {"episodes": [8, 9, 10]}})
        tx.set_validation({"valid": True, "errors": []})
        tx.set_change_set({"paths": ["episode_plan.episodes.8"]})
        tx.set_impact_plan({"affected": ["episode_scripts.8"]})
        return tx

    def test_registry_exposes_all_nine_operations(self):
        ids = [self.registry.operation(item)["id"] for item in [
            "operation.create-project-brief", "operation.compose-story-bible", "operation.design-episode-plan",
            "operation.write-episodes", "operation.revise-episode-plan", "operation.score-script",
            "operation.revise-script", "operation.check-compliance", "operation.prepare-delivery",
        ]]
        self.assertEqual(len(ids), 9)

    def test_missing_inputs_are_rejected_before_plan(self):
        operation = self.registry.operation("operation.revise-episode-plan")
        with self.assertRaises(TransactionError):
            CallTransaction(operation, {}, self.system_inputs(), {})

    def test_stage_order_is_strict(self):
        tx = self.transaction()
        with self.assertRaises(TransactionError):
            tx.set_candidate({})

    def test_execution_pack_is_exact_and_hashed(self):
        tx = self.transaction()
        tx.set_plan({"steps": []})
        pack = tx.compile_execution_pack(
            self.registry.execution_persona(tx.operation["id"]),
            self.registry.execution_capabilities(tx.operation["id"]),
        )
        self.assertEqual(tx.envelope["execution_meta"]["execution_pack_hash"], canonical_hash(pack))

    def test_invalid_validation_rejects_candidate(self):
        tx = self.transaction()
        tx.set_plan({})
        tx.compile_execution_pack(
            self.registry.execution_persona(tx.operation["id"]),
            self.registry.execution_capabilities(tx.operation["id"]),
        )
        tx.set_candidate({"episode_plan": {}})
        tx.set_validation({"valid": False, "errors": [{"code": "scope"}]})
        self.assertEqual(tx.envelope["status"], "rejected")
        with self.assertRaises(TransactionError):
            tx.set_change_set({})

    def test_commit_requires_confirmation(self):
        tx = self.complete_to_impact()
        with self.assertRaises(TransactionError):
            tx.commit(InMemoryArtifactStore(), confirmed=False)

    def test_atomic_commit_checks_base_versions(self):
        tx = self.complete_to_impact()
        store = InMemoryArtifactStore({name: {"version": 4, "value": {}} for name in tx.envelope["execution_meta"]["base_versions"]})
        with self.assertRaises(VersionConflict):
            tx.commit(store, confirmed=True)

    def test_commit_and_trace_are_replayable(self):
        tx = self.complete_to_impact()
        base = tx.envelope["execution_meta"]["base_versions"]
        store = InMemoryArtifactStore({name: {"version": version, "value": {}} for name, version in base.items()})
        receipt = tx.commit(store, confirmed=True)
        replay = tx.replay_document()
        self.assertEqual(receipt["versions"]["episode_plan"], 1)
        self.assertEqual(replay["status"], "committed")
        self.assertEqual([event["stage"] for event in replay["trace"]], list(tx.operation["stages"]))
        self.assertEqual(len({event["payload_hash"] for event in replay["trace"]}), 8)
        schema = json.loads((ROOT / "v6" / "contracts" / "call-envelope.schema.json").read_text(encoding="utf-8"))
        jsonschema.validate(replay, schema)


if __name__ == "__main__":
    unittest.main()
