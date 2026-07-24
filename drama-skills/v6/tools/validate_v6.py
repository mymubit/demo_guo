from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
V6 = ROOT / "v6"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    manifest = load_yaml(V6 / "manifest.yaml")

    for label, relative in manifest.get("contracts", {}).items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing contract {label}: {relative}")
            continue
        try:
            contract = json.loads(path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(contract)
        except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append(f"invalid JSON contract {relative}: {exc}")

    for label, relative in manifest.get("runtime", {}).items():
        if label == "stage_order":
            continue
        if not (ROOT / relative).exists():
            errors.append(f"missing runtime component {label}: {relative}")

    schema_objects = list(manifest.get("artifacts", {}).items()) + list(manifest.get("components", {}).items())
    for artifact_key, artifact in schema_objects:
        schema_path = ROOT / artifact["schema"]
        if not schema_path.exists():
            errors.append(f"missing artifact schema {artifact_key}: {artifact['schema']}")
            continue
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.Draft202012Validator.check_schema(schema)
        except (json.JSONDecodeError, jsonschema.SchemaError) as exc:
            errors.append(f"invalid artifact schema {artifact_key}: {exc}")
            continue
        for fixture_relative in artifact.get("valid_fixtures", []):
            fixture_path = ROOT / fixture_relative
            if not fixture_path.exists():
                errors.append(f"missing valid fixture {artifact_key}: {fixture_relative}")
                continue
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            try:
                jsonschema.validate(fixture, schema)
            except jsonschema.ValidationError as exc:
                errors.append(f"invalid fixture {fixture_relative}: {exc.message}")

    constraint_paths = manifest.get("constraints", [])
    for relative in constraint_paths:
        constraint_path = ROOT / relative
        if not constraint_path.exists():
            errors.append(f"missing constraint file: {relative}")
            continue
        document = load_yaml(constraint_path) or {}
        if not isinstance(document.get("version"), int) or not isinstance(document.get("constraints"), dict):
            errors.append(f"{relative}: constraint document requires integer version and constraints object")
            continue
        for constraint_id, constraint in document["constraints"].items():
            if not isinstance(constraint, dict) or not constraint.get("source_refs"):
                errors.append(f"{relative}#{constraint_id}: missing source_refs")

    operation_schema = json.loads((V6 / "contracts" / "operation.schema.json").read_text(encoding="utf-8"))
    atomic_rule_schema = json.loads((V6 / "contracts" / "atomic-rule.schema.json").read_text(encoding="utf-8"))
    capability_schema = json.loads((V6 / "contracts" / "capability.schema.json").read_text(encoding="utf-8"))
    persona_schema = json.loads((V6 / "contracts" / "persona.schema.json").read_text(encoding="utf-8"))
    advisory_schema = json.loads((V6 / "contracts" / "advisory.schema.json").read_text(encoding="utf-8"))

    advisory_ids = set()
    advisory_files = manifest.get("advisories", {}).get("files", [])
    for relative in advisory_files:
        advisory_path = ROOT / relative
        if not advisory_path.exists():
            errors.append(f"missing advisory file: {relative}")
            continue
        advisory = load_yaml(advisory_path)
        try:
            jsonschema.validate(advisory, advisory_schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{relative}: {exc.message}")
        advisory_id = advisory.get("id")
        if advisory_id in advisory_ids:
            errors.append(f"duplicate advisory id: {advisory_id}")
        advisory_ids.add(advisory_id)
    atom_catalog = load_yaml(V6 / "atoms" / "catalog.yaml")
    rule_ids = set()
    for relative in atom_catalog.get("rule_files", []):
        atom_path = ROOT / relative
        if not atom_path.exists():
            errors.append(f"missing atomic rule file: {relative}")
            continue
        for rule in (load_yaml(atom_path) or {}).get("rules", []):
            try:
                jsonschema.validate(rule, atomic_rule_schema)
            except jsonschema.ValidationError as exc:
                errors.append(f"{relative}#{rule.get('id', '?')}: {exc.message}")
            if rule.get("id") in rule_ids:
                errors.append(f"duplicate atomic rule id: {rule.get('id')}")
            rule_ids.add(rule.get("id"))

    operation_paths = [ROOT / item for item in manifest.get("operations", [])]
    persona_catalog = load_yaml(V6 / "personas" / "catalog.yaml")
    persona_ids = set()
    for item in persona_catalog.get("personas", []):
        source = item.get("source")
        if not source or not (ROOT / source).exists():
            errors.append(f"{item.get('id', '?')}: missing persona source {source}")
            continue
        persona = load_yaml(ROOT / source)
        try:
            jsonschema.validate(persona, persona_schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{source}: {exc.message}")
        if persona.get("id") != item.get("id"):
            errors.append(f"{source}: persona id does not match catalog")
        persona_ids.add(persona.get("id"))
    capability_catalog = load_yaml(V6 / "capabilities" / "catalog.yaml")
    capability_ids = {item["id"] for item in capability_catalog.get("capabilities", [])}
    for item in capability_catalog.get("capabilities", []):
        source = item.get("source")
        if not source:
            errors.append(f"{item['id']}: missing capability source")
            continue
        capability_path = ROOT / source
        if not capability_path.exists():
            errors.append(f"{item['id']}: missing capability file {source}")
            continue
        capability = load_yaml(capability_path)
        try:
            jsonschema.validate(capability, capability_schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{source}: {exc.message}")
        unknown_rules = sorted(set(capability.get("rules", [])) - rule_ids)
        if unknown_rules:
            errors.append(f"{source}: unknown atomic rules {unknown_rules}")
    operations_by_id = {}
    for path in operation_paths:
        if not path.exists():
            errors.append(f"missing operation: {path.relative_to(ROOT)}")
            continue
        operation = load_yaml(path)
        operations_by_id[operation.get("id")] = operation
        try:
            jsonschema.validate(operation, operation_schema)
        except jsonschema.ValidationError as exc:
            errors.append(f"{path.relative_to(ROOT)}: {exc.message}")
        unknown = sorted(set(operation.get("capabilities", [])) - capability_ids)
        if unknown:
            errors.append(f"{path.relative_to(ROOT)}: unknown capabilities {unknown}")
        if operation.get("persona") not in persona_ids:
            errors.append(f"{path.relative_to(ROOT)}: unknown persona {operation.get('persona')}")

    workbench_relative = manifest.get("workbench")
    if not workbench_relative or not (ROOT / workbench_relative).exists():
        errors.append(f"missing V6 workbench: {workbench_relative}")
    else:
        workbench = load_yaml(ROOT / workbench_relative) or {}
        mounted = [item.get("id") for item in workbench.get("operations", [])]
        if len(mounted) != len(set(mounted)):
            errors.append("V6 workbench mounts duplicate operations")
        missing_mounts = sorted(set(operations_by_id) - set(mounted))
        unknown_mounts = sorted(set(mounted) - set(operations_by_id))
        if missing_mounts or unknown_mounts:
            errors.append(
                f"V6 workbench operation mismatch missing={missing_mounts} unknown={unknown_mounts}"
            )
        produced_artifacts = {
            artifact
            for operation in operations_by_id.values()
            for artifact in operation.get("writes", [])
        }
        for item in workbench.get("operations", []):
            operation = operations_by_id.get(item.get("id")) or {}
            if item.get("result_view") is None:
                errors.append(f"{item.get('id')}: workbench result_view is required")
            unknown_dependencies = sorted(
                set(item.get("dependencies", [])) - produced_artifacts
            )
            if unknown_dependencies:
                errors.append(f"{item.get('id')}: unknown workbench dependencies {unknown_dependencies}")
            if set(item.get("invalidates", [])) & set(operation.get("writes", [])):
                errors.append(f"{item.get('id')}: operation cannot invalidate its own writes")

    for skill_path in V6.glob("operations/*/SKILL.md"):
        text = skill_path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not match:
            errors.append(f"{skill_path.relative_to(ROOT)}: missing YAML frontmatter")
            continue
        frontmatter = yaml.safe_load(match.group(1)) or {}
        if set(frontmatter) != {"name", "description"}:
            errors.append(
                f"{skill_path.relative_to(ROOT)}: frontmatter must contain only name and description"
            )
        agents_path = skill_path.parent / "agents" / "openai.yaml"
        if not agents_path.exists():
            errors.append(f"{skill_path.relative_to(ROOT)}: missing agents/openai.yaml")

    forbidden = []
    for path in V6.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".yaml", ".yml", ".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?:from|import)\s+(?:runtime|orchestration)(?:\.|\s)", text):
            forbidden.append(path.relative_to(ROOT).as_posix())
    if forbidden:
        errors.append(f"V6 runtime imports V5 runtime/orchestration: {forbidden}")

    inventory = json.loads((ROOT / "migration" / "inventory.json").read_text(encoding="utf-8"))
    mapping = json.loads((ROOT / "migration" / "mapping.json").read_text(encoding="utf-8"))
    if len(inventory.get("files", [])) != len(mapping.get("mappings", [])):
        errors.append("inventory and mapping counts differ")

    rule_mapping = json.loads((ROOT / "migration" / "rule-mapping.json").read_text(encoding="utf-8"))
    for item in rule_mapping.get("mappings", []):
        if item.get("status") != "verified":
            continue
        unknown_targets = sorted(set(item.get("targets", [])) - rule_ids)
        if unknown_targets:
            errors.append(f"{item.get('legacy_rule_key')}: verified mapping has unknown targets {unknown_targets}")
        if not item.get("tests"):
            errors.append(f"{item.get('legacy_rule_key')}: verified mapping has no tests")
        for relative in item.get("tests", []):
            if not (ROOT / relative).exists():
                errors.append(f"{item.get('legacy_rule_key')}: missing mapping evidence {relative}")

    print(
        json.dumps(
            {
                "operations": len(operation_paths),
                "capabilities": len(capability_ids),
                "personas": len(persona_ids),
                "atomic_rules": len(rule_ids),
                "advisories": len(advisory_ids),
                "v5_inventory_files": len(inventory.get("files", [])),
                "artifacts": len(manifest.get("artifacts", {})),
                "components": len(manifest.get("components", {})),
                "constraint_files": len(constraint_paths),
                "errors": errors,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
