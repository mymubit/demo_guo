from __future__ import annotations

import hashlib
import json
import uuid
from copy import deepcopy


STAGES = ("command", "plan", "execution_pack", "candidate", "validation", "change_set", "impact_plan", "commit")
STATUS = {
    "command": "planned",
    "plan": "planned",
    "execution_pack": "executing",
    "candidate": "executing",
    "validation": "validating",
    "change_set": "validating",
    "impact_plan": "ready_to_commit",
    "commit": "committed",
}


class TransactionError(RuntimeError):
    pass


def canonical_hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class CallTransaction:
    """Deterministic state machine for one observable V6 operation call."""

    def __init__(
        self,
        operation: dict,
        command: dict,
        system_inputs: dict,
        versioned_reads: dict,
        call_id: str | None = None,
    ):
        missing = sorted(set(operation.get("required_params", [])) - set(command))
        if missing:
            raise TransactionError(f"missing command parameters: {missing}")
        missing_system = sorted(set(operation.get("system_inputs", [])) - set(system_inputs))
        if missing_system:
            raise TransactionError(f"missing system inputs: {missing_system}")
        self.operation = deepcopy(operation)
        self._stage_index = 0
        self.envelope = {
            "call_id": call_id or str(uuid.uuid4()),
            "operation": operation["id"],
            "stage": "command",
            "status": STATUS["command"],
            "command": {
                "user_inputs": deepcopy(command),
                "system_inputs": deepcopy(system_inputs),
                "versioned_reads": deepcopy(versioned_reads),
            },
            "plan": {},
            "execution_meta": {
                "engine_version": "6",
                "base_versions": {name: item.get("version") for name, item in versioned_reads.items()},
            },
            "trace": [],
        }
        self._trace("command", self.envelope["command"])

    def _trace(self, stage: str, payload: object) -> None:
        self.envelope["trace"].append(
            {
                "sequence": len(self.envelope["trace"]) + 1,
                "stage": stage,
                "status": self.envelope["status"],
                "payload_hash": canonical_hash(payload),
            }
        )

    def _advance(self, stage: str, payload: dict) -> None:
        expected = STAGES[self._stage_index + 1] if self._stage_index + 1 < len(STAGES) else None
        if stage != expected:
            raise TransactionError(f"invalid stage transition: expected={expected}, received={stage}")
        self._stage_index += 1
        self.envelope["stage"] = stage
        self.envelope["status"] = STATUS[stage]
        self.envelope[stage] = deepcopy(payload)
        self._trace(stage, payload)

    def set_plan(self, plan: dict) -> None:
        self._advance("plan", plan)

    def compile_execution_pack(self, persona: dict, capabilities: list[dict]) -> dict:
        if self.envelope["stage"] != "plan":
            raise TransactionError("execution pack requires the plan stage")
        actual = [item.get("id") for item in capabilities]
        if actual != self.operation["capabilities"]:
            raise TransactionError("execution capabilities do not exactly match operation declaration")
        pack = {
            "operation": deepcopy(self.operation),
            "persona": deepcopy(persona),
            "capabilities": deepcopy(capabilities),
            "rules": list(dict.fromkeys(rule for item in capabilities for rule in item.get("rules", []))),
            "atomic_rules": [
                deepcopy(rule)
                for item in capabilities
                for rule in item.get("rule_definitions", [])
            ],
            "reads": deepcopy(self.envelope["command"]["versioned_reads"]),
        }
        pack_hash = canonical_hash(pack)
        self.envelope["execution_meta"]["execution_pack_hash"] = pack_hash
        self._advance("execution_pack", pack)
        return deepcopy(pack)

    def set_candidate(self, candidate: dict, prompt: object | None = None) -> None:
        if prompt is not None:
            self.envelope["execution_meta"]["prompt_hash"] = canonical_hash(prompt)
        self._advance("candidate", candidate)

    def set_validation(self, validation: dict) -> None:
        if not isinstance(validation.get("valid"), bool) or not isinstance(validation.get("errors", []), list):
            raise TransactionError("validation requires boolean valid and an errors array")
        self._advance("validation", validation)
        if not validation["valid"]:
            self.envelope["status"] = "rejected"
            self.envelope["trace"][-1]["status"] = "rejected"
            self.envelope["errors"] = deepcopy(validation.get("errors", []))

    def set_change_set(self, change_set: dict) -> None:
        if self.envelope["status"] == "rejected":
            raise TransactionError("rejected candidate cannot produce a change set")
        self._advance("change_set", change_set)

    def set_impact_plan(self, impact_plan: dict) -> None:
        self._advance("impact_plan", impact_plan)

    def commit(self, store, confirmed: bool) -> dict:
        if not confirmed:
            raise TransactionError("explicit commit confirmation is required")
        if self.envelope["stage"] != "impact_plan" or self.envelope["status"] != "ready_to_commit":
            raise TransactionError("transaction is not ready to commit")
        try:
            receipt = store.commit(
                self.operation["writes"],
                self.envelope["candidate"],
                self.envelope["execution_meta"]["base_versions"],
                commit_id=self.envelope["call_id"],
            )
        except TypeError:
            receipt = store.commit(
                self.operation["writes"],
                self.envelope["candidate"],
                self.envelope["execution_meta"]["base_versions"],
            )
        self._advance("commit", receipt)
        return deepcopy(receipt)

    def replay_document(self) -> dict:
        return deepcopy(self.envelope)

    @classmethod
    def from_replay(cls, operation: dict, envelope: dict) -> "CallTransaction":
        if envelope.get("operation") != operation.get("id"):
            raise TransactionError("replay operation does not match declaration")
        trace = envelope.get("trace", [])
        expected_stages = list(STAGES[: len(trace)])
        if [event.get("stage") for event in trace] != expected_stages:
            raise TransactionError("replay trace is not a contiguous stage prefix")
        for index, event in enumerate(trace, start=1):
            stage = event["stage"]
            if event.get("sequence") != index or canonical_hash(envelope.get(stage, {})) != event.get("payload_hash"):
                raise TransactionError(f"replay trace integrity failure at {stage}")
        instance = cls.__new__(cls)
        instance.operation = deepcopy(operation)
        instance.envelope = deepcopy(envelope)
        instance._stage_index = STAGES.index(envelope["stage"])
        return instance
