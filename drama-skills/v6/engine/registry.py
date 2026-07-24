from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import yaml


class RegistryError(ValueError):
    pass


class OperationRegistry:
    """Load V6 declarations without importing legacy runtime code."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.v6 = self.root / "v6"
        self._operations: dict[str, dict] = {}
        self._capabilities: dict[str, dict] = {}
        self._personas: dict[str, dict] = {}
        self._atomic_rules: dict[str, dict] = {}
        self._load()

    @staticmethod
    def _yaml(path: Path) -> dict:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def _load(self) -> None:
        manifest = self._yaml(self.v6 / "manifest.yaml")
        catalog = self._yaml(self.v6 / "capabilities" / "catalog.yaml")
        atom_catalog = self._yaml(self.v6 / "atoms" / "catalog.yaml")
        persona_catalog = self._yaml(self.v6 / "personas" / "catalog.yaml")
        for relative in atom_catalog.get("rule_files", []):
            for rule in self._yaml(self.root / relative).get("rules", []):
                self._atomic_rules[rule["id"]] = rule
        for entry in persona_catalog.get("personas", []):
            declaration = self._yaml(self.root / entry["source"])
            self._personas[declaration["id"]] = declaration
        for entry in catalog.get("capabilities", []):
            declaration = self._yaml(self.root / entry["source"])
            self._capabilities[declaration["id"]] = declaration
        for relative in manifest.get("operations", []):
            declaration = self._yaml(self.root / relative)
            self._operations[declaration["id"]] = declaration

    def operation(self, operation_id: str) -> dict:
        if operation_id not in self._operations:
            raise RegistryError(f"unknown V6 operation: {operation_id}")
        return deepcopy(self._operations[operation_id])

    def execution_capabilities(self, operation_id: str) -> list[dict]:
        operation = self.operation(operation_id)
        missing = [item for item in operation["capabilities"] if item not in self._capabilities]
        if missing:
            raise RegistryError(f"operation has unknown capabilities: {missing}")
        capabilities = []
        for item in operation["capabilities"]:
            capability = deepcopy(self._capabilities[item])
            unknown_rules = [rule for rule in capability.get("rules", []) if rule not in self._atomic_rules]
            if unknown_rules:
                raise RegistryError(f"capability has unknown atomic rules: {unknown_rules}")
            capability["rule_definitions"] = [
                deepcopy(self._atomic_rules[rule]) for rule in capability.get("rules", [])
            ]
            capabilities.append(capability)
        return capabilities

    def execution_persona(self, operation_id: str) -> dict:
        operation = self.operation(operation_id)
        persona_id = operation["persona"]
        if persona_id not in self._personas:
            raise RegistryError(f"operation has unknown persona: {persona_id}")
        return deepcopy(self._personas[persona_id])
