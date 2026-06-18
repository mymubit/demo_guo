# -*- coding: utf-8 -*-
"""Print an observable workflow execution trace."""
from __future__ import annotations

import json
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandError

from apps.workflow.execution_models import NodeExecution, WorkflowInstance
from apps.workflow.runtime_contract import json_size_bytes, summarize_value


def _compact(value: Any) -> Dict[str, Any]:
    size, _ = json_size_bytes(value or {})
    return {
        "bytes": size,
        "shape": summarize_value(value or {}, max_depth=2),
    }


class Command(BaseCommand):
    help = "Print a workflow instance trace with node input/output snapshots and events."

    def add_arguments(self, parser):
        parser.add_argument("instance_id", nargs="?", default="", help="WorkflowInstance id")
        parser.add_argument("--project-id", default="", help="Use the latest WorkflowInstance for a project")
        parser.add_argument("--events-limit", type=int, default=20, help="Max events per node")
        parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    def handle(self, *args, **options):
        instance = self._resolve_instance(options)
        payload = self._build_trace(instance, max(0, int(options["events_limit"] or 0)))
        if options.get("json"):
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
            return
        self._write_human(payload)

    def _resolve_instance(self, options) -> WorkflowInstance:
        instance_id = options.get("instance_id") or ""
        project_id = options.get("project_id") or ""
        qs = WorkflowInstance.objects.select_related("project", "pack").order_by("-created_at")
        if instance_id:
            try:
                return qs.get(id=instance_id)
            except WorkflowInstance.DoesNotExist as exc:
                raise CommandError(f"WorkflowInstance not found: {instance_id}") from exc
        if project_id:
            instance = qs.filter(project_id=project_id).first()
            if instance:
                return instance
            raise CommandError(f"No WorkflowInstance found for project: {project_id}")
        raise CommandError("Pass an instance_id or --project-id")

    def _build_trace(self, instance: WorkflowInstance, events_limit: int) -> Dict[str, Any]:
        executions = (
            NodeExecution.objects.filter(instance=instance)
            .prefetch_related("events")
            .order_by("created_at")
        )
        return {
            "instance": {
                "id": str(instance.id),
                "project_id": str(instance.project_id or ""),
                "pack_id": str(instance.pack_id),
                "status": instance.status,
                "current_node_id": instance.current_node_id,
                "failure_node_id": instance.failure_node_id,
                "failure_reason": instance.failure_reason,
                "coin_cost_total": instance.coin_cost_total,
                "llm_token_in_total": instance.llm_token_in_total,
                "llm_token_out_total": instance.llm_token_out_total,
                "started_at": instance.started_at,
                "finished_at": instance.finished_at,
                "duration_ms": instance.total_duration_ms,
                "context": _compact(instance.context),
            },
            "nodes": [self._node_payload(node, events_limit) for node in executions],
        }

    def _node_payload(self, node: NodeExecution, events_limit: int) -> Dict[str, Any]:
        events = list(node.events.all()[:events_limit])
        return {
            "id": str(node.id),
            "node_id": node.node_id,
            "node_name": node.node_name,
            "runner_type": node.runner_type,
            "status": node.status,
            "attempt": node.attempt,
            "retry_count": node.retry_count,
            "coin_cost": node.coin_cost,
            "llm_token_in": node.llm_token_in,
            "llm_token_out": node.llm_token_out,
            "duration_ms": node.duration_ms,
            "agent_execution_run_ids": node.agent_execution_run_ids,
            "errors": node.errors,
            "input_context": node.input_context,
            "output_context": _compact(node.output_context),
            "events": [
                {
                    "event_type": event.event_type,
                    "level": event.level,
                    "message": event.message,
                    "duration_ms": event.duration_ms,
                    "extra": event.extra,
                    "created_at": event.created_at,
                }
                for event in events
            ],
        }

    def _write_human(self, payload: Dict[str, Any]) -> None:
        inst = payload["instance"]
        self.stdout.write(
            "WorkflowInstance {id} status={status} project={project_id} current={current_node_id}".format(
                **inst
            )
        )
        if inst.get("failure_reason"):
            self.stdout.write(f"Failure: {inst['failure_reason']}")
        self.stdout.write(
            "Cost: coin={coin_cost_total} token_in={llm_token_in_total} token_out={llm_token_out_total}".format(
                **inst
            )
        )
        self.stdout.write("Context: {bytes} bytes".format(bytes=inst["context"]["bytes"]))
        for node in payload["nodes"]:
            self.stdout.write("")
            self.stdout.write(
                "[{status}] {node_id} runner={runner_type} cost={coin_cost} "
                "tokens={llm_token_in}/{llm_token_out} duration={duration_ms}ms".format(**node)
            )
            if node.get("errors"):
                self.stdout.write(f"  errors={json.dumps(node['errors'], ensure_ascii=False, default=str)}")
            input_ctx = node.get("input_context") or {}
            if input_ctx:
                self.stdout.write(f"  input={json.dumps(input_ctx, ensure_ascii=False, default=str)}")
            self.stdout.write(
                "  output={bytes} bytes {shape}".format(
                    bytes=node["output_context"]["bytes"],
                    shape=json.dumps(node["output_context"]["shape"], ensure_ascii=False, default=str),
                )
            )
            for event in node["events"]:
                self.stdout.write(
                    "  - {level}/{event_type} {duration_ms}ms {message}".format(**event)
                )
