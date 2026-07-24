from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v6.engine import CallJournal, CallTransaction, FileArtifactStore, OperationRegistry


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and inspect observable V6 operation transactions")
    parser.add_argument("--state-root", default=".v6-state")
    sub = parser.add_subparsers(dest="action", required=True)
    inspect_parser = sub.add_parser("inspect")
    inspect_parser.add_argument("operation")
    start = sub.add_parser("start")
    start.add_argument("operation")
    start.add_argument("--command", required=True)
    start.add_argument("--system-inputs", required=True)
    start.add_argument("--reads", required=True)
    show = sub.add_parser("show")
    show.add_argument("call_id")
    args = parser.parse_args()

    registry = OperationRegistry(ROOT)

    if args.action == "inspect":
        output = {
            "operation": registry.operation(args.operation),
            "capabilities": registry.execution_capabilities(args.operation),
        }
    elif args.action == "start":
        state_root = Path(args.state_root)
        journal = CallJournal(state_root / "calls")
        FileArtifactStore(state_root / "artifacts.json")
        transaction = CallTransaction(
            registry.operation(args.operation),
            read_json(args.command),
            read_json(args.system_inputs),
            read_json(args.reads),
        )
        journal.save(transaction.replay_document())
        output = transaction.replay_document()
    else:
        journal = CallJournal(Path(args.state_root) / "calls")
        output = journal.load(args.call_id)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
