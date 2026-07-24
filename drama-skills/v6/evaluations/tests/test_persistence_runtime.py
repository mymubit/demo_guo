from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from v6.engine import CallJournal, CallTransaction, FileArtifactStore, OperationRegistry, TransactionError, canonical_hash


ROOT = Path(__file__).resolve().parents[3]


class PersistenceRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = OperationRegistry(ROOT)
        self.operation = self.registry.operation("operation.revise-episode-plan")
        command = {"episode_range": [1, 1], "change_requests": ["hook"], "base_version": 1}
        system = {"engine_version": "6", "artifact_schema_versions": {}, "active_rule_versions": {}, "caller_identity": "test"}
        reads = {name: {"version": None, "hash": canonical_hash(name)} for name in self.operation["reads"]}
        self.tx = CallTransaction(self.operation, command, system, reads, call_id="persistent-call")

    def tearDown(self):
        self.temp.cleanup()

    def advance(self):
        self.tx.set_plan({"steps": ["x"]})
        self.tx.compile_execution_pack(
            self.registry.execution_persona(self.operation["id"]),
            self.registry.execution_capabilities(self.operation["id"]),
        )
        self.tx.set_candidate({"episode_plan": {"episodes": [1]}})
        self.tx.set_validation({"valid": True, "errors": []})
        self.tx.set_change_set({"paths": ["episode_plan"]})
        self.tx.set_impact_plan({"affected": []})

    def test_journal_round_trip_and_resume(self):
        self.tx.set_plan({"steps": ["x"]})
        journal = CallJournal(self.root / "calls")
        journal.save(self.tx.replay_document())
        resumed = CallTransaction.from_replay(self.operation, journal.load("persistent-call"))
        resumed.compile_execution_pack(
            self.registry.execution_persona(self.operation["id"]),
            self.registry.execution_capabilities(self.operation["id"]),
        )
        self.assertEqual(resumed.envelope["stage"], "execution_pack")

    def test_tampered_journal_cannot_resume(self):
        self.tx.set_plan({"steps": ["x"]})
        envelope = self.tx.replay_document()
        envelope["plan"]["steps"] = ["tampered"]
        with self.assertRaises(TransactionError):
            CallTransaction.from_replay(self.operation, envelope)

    def test_file_commit_is_persistent_and_idempotent(self):
        self.advance()
        store = FileArtifactStore(self.root / "artifacts.json")
        first = self.tx.commit(store, confirmed=True)
        second = store.commit(self.operation["writes"], {"episode_plan": {"different": True}}, {}, commit_id="persistent-call")
        self.assertEqual(first, second)
        self.assertEqual(FileArtifactStore(self.root / "artifacts.json").snapshot()["episode_plan"]["version"], 1)


if __name__ == "__main__":
    unittest.main()
