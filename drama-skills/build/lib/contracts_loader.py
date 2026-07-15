"""加载 contracts/ 目录下的产物与参数契约。"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_PATH = ROOT / "contracts" / "artifacts.yaml"
PARAMETERS_PATH = ROOT / "contracts" / "parameters.yaml"

FORBIDDEN_ROLE_PARAM_KEYS = {
    "type",
    "enum",
    "default",
    "items_type",
    "enum_items",
    "minimum",
    "maximum",
    "pattern",
    "source",
    "source_ref",
    "max_items",
    "max_items_source",
    "ui_widget",
    "nullable",
    "unique_items",
    "min_length",
    "enum_source",
}


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_artifacts_contract(root: Optional[Path] = None) -> Dict[str, Any]:
    return load_yaml((root or ROOT) / "contracts" / "artifacts.yaml")


def load_parameters_contract(root: Optional[Path] = None) -> Dict[str, Any]:
    return load_yaml((root or ROOT) / "contracts" / "parameters.yaml")


def artifact_keys(contract: Optional[Dict[str, Any]] = None) -> Set[str]:
    data = contract or load_artifacts_contract()
    keys = set((data.get("artifacts") or {}).keys())
    keys.update((data.get("virtual_artifacts") or {}).keys())
    keys.update((data.get("external_artifacts") or {}).keys())
    return keys


def producer_map(contract: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
    data = contract or load_artifacts_contract()
    result: Dict[str, str] = {}
    for key, definition in (data.get("artifacts") or {}).items():
        producer = (definition or {}).get("producer")
        if producer:
            result[key] = producer
    return result


def schema_path_for(key: str, contract: Optional[Dict[str, Any]] = None) -> Path:
    data = contract or load_artifacts_contract()
    artifacts = data.get("artifacts") or {}
    if key not in artifacts:
        raise KeyError(key)
    relative = artifacts[key]["schema_path"]
    return ROOT / relative


def role_output_artifacts(
    contract: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """返回 producer → artifact_key，产物关系只来自 artifact contract。"""
    data = contract or load_artifacts_contract()
    return {
        definition["producer"]: key
        for key, definition in (data.get("artifacts") or {}).items()
        if (definition or {}).get("producer")
    }


def parameter_names(contract: Optional[Dict[str, Any]] = None) -> Set[str]:
    data = contract or load_parameters_contract()
    return set((data.get("parameters") or {}).keys())


def role_parameter_refs(agent_id: str, contract: Optional[Dict[str, Any]] = None) -> List[str]:
    data = contract or load_parameters_contract()
    return list((data.get("role_parameter_refs") or {}).get(agent_id) or [])
