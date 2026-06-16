"""
SSE 统一进度上报服务。

提供统一的 SSE（Server-Sent Events）事件流，
供前端实时订阅创作项目进度。

SSE 事件格式：
    event: progress
    data: {project_id, task_id, current_node, overall_progress, eta_seconds, coin_spent, last_event}

    event: node_complete
    data: {project_id, node_index, node_name, status, artifact_key}

    event: error
    data: {project_id, code, message}

使用方式：
    from apps.creation.services.sse_progress import broadcast_progress, subscribe

    # 创作服务中广播进度
    broadcast_progress(project_id, {"event": "progress", ...})

    # View 中建立 SSE 连接
    response = subscribe(project_id, user_id)
    return StreamingHttpResponse(response, content_type="text/event-stream")
"""

import asyncio
import json
import logging
import threading
from typing import Any, AsyncGenerator, Dict, Optional

from django.core.cache import cache

logger = logging.getLogger(__name__)

# Redis pub/sub channel 命名
CHANNEL_PREFIX = "sse_progress"


def _channel_name(project_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{project_id}"


class SSEProgressBroadcaster:
    """
    基于 Redis pub/sub 的进度广播。

    使用 django_redis 的 pub/sub 功能，支持多进程/多实例部署。
    广播时将消息发布到对应 project_id 的 channel。
    """

    @staticmethod
    def broadcast_progress(project_id: str, event_data: dict) -> bool:
        """
        广播进度事件到指定项目 channel。

        Args:
            project_id: 项目 ID
            event_data: 事件数据字典，包含 event 类型和 payload

        Returns:
            广播是否成功
        """
        try:
            channel = _channel_name(project_id)
            message = json.dumps(event_data, ensure_ascii=False)
            cache.set(f"_last_event_{channel}", message, timeout=3600)
            cache.publish(channel, message)
            return True
        except Exception as exc:
            logger.warning("[SSEProgress] 广播失败 project_id=%s: %s", project_id, exc)
            return False

    @staticmethod
    def get_last_event(project_id: str) -> Optional[dict]:
        """
        获取项目最近一次事件（用于新订阅者获取当前状态）。

        Returns:
            最近一次事件字典，或 None
        """
        try:
            channel = _channel_name(project_id)
            data = cache.get(f"_last_event_{channel}")
            if data:
                return json.loads(data)
        except Exception as exc:
            logger.warning("[SSEProgress] 获取最近事件失败 project_id=%s: %s", project_id, exc)
        return None


# 同步广播快捷函数
def broadcast_progress(project_id: str, event_data: dict) -> bool:
    """
    快捷函数：广播进度事件。

    Usage:
        broadcast_progress(project_id, {
            "event": "progress",
            "project_id": project_id,
            "task_id": task_id,
            "current_node": 3,
            "overall_progress": 45.5,
            "eta_seconds": 120,
            "coin_spent": 28,
            "last_event": "正在执行节点 3",
        })
    """
    return SSEProgressBroadcaster.broadcast_progress(project_id, event_data)


def broadcast_node_complete(project_id: str, node_index: int, node_name: str,
                              status: str, artifact_key: str) -> bool:
    """
    广播节点完成事件。

    Usage:
        broadcast_node_complete(project_id, 3, "scene_generation", "completed", "episode_scripts")
    """
    return broadcast_progress(project_id, {
        "event": "node_complete",
        "project_id": project_id,
        "node_index": node_index,
        "node_name": node_name,
        "status": status,
        "artifact_key": artifact_key,
    })


def broadcast_error(project_id: str, code: str, message: str) -> bool:
    """
    广播错误事件。

    Usage:
        broadcast_error(project_id, "NODE_TIMEOUT", "节点 3 执行超时")
    """
    return broadcast_progress(project_id, {
        "event": "error",
        "project_id": project_id,
        "code": code,
        "message": message,
    })


class SSEProgressSubscriber:
    """
    SSE 订阅者，生成 yield 事件流。

    订阅 Redis channel 并 yield 格式化后的 SSE data。
    支持超时自动关闭连接。
    """

    def __init__(self, project_id: str, user_id: int,
                 timeout_seconds: int = 3600, poll_interval: float = 0.5):
        """
        Args:
            project_id: 项目 ID
            user_id: 用户 ID（用于权限校验标记）
            timeout_seconds: 订阅超时时间，默认 1 小时
            poll_interval: 轮询间隔（秒），默认 0.5s
        """
        self.project_id = project_id
        self.user_id = user_id
        self.timeout_seconds = timeout_seconds
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._pubsub = None

    def stop(self):
        """停止订阅。"""
        self._stop_event.set()
        if self._pubsub:
            try:
                self._pubsub.close()
            except Exception:
                pass

    def _format_sse(self, event_type: str, data: Any) -> str:
        """格式化 SSE 事件。"""
        json_data = json.dumps(data, ensure_ascii=False)
        return f"event: {event_type}\ndata: {json_data}\n\n"

    def _heartbeat(self) -> str:
        """发送心跳。"""
        return self._format_sse("heartbeat", {"ts": _timestamp()})

    def subscribe(self) -> AsyncGenerator[str, None]:
        """
        生成 SSE 事件流。

        Yields:
            格式化后的 SSE 事件字符串
        """
        import time
        channel = _channel_name(self.project_id)

        last_event = SSEProgressBroadcaster.get_last_event(self.project_id)
        if last_event:
            yield self._format_sse(last_event.get("event", "progress"), last_event)

        start_time = time.time()
        pubsub = cache.client.get_client().pubsub()
        self._pubsub = pubsub

        try:
            pubsub.subscribe(channel)
            while not self._stop_event.is_set():
                elapsed = time.time() - start_time
                if elapsed > self.timeout_seconds:
                    logger.info("[SSEProgress] 订阅超时 project_id=%s user_id=%s", self.project_id, self.user_id)
                    break

                try:
                    message = pubsub.get_message(timeout=self.poll_interval)
                    if message and message.get("type") == "message":
                        data = message.get("data")
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")
                        event_data = json.loads(data)
                        event_type = event_data.get("event", "progress")
                        yield self._format_sse(event_type, event_data)
                except Exception as exc:
                    logger.warning("[SSEProgress] 接收消息失败: %s", exc)

                if int(elapsed) % 30 == 0:
                    yield self._heartbeat()

        finally:
            try:
                pubsub.unsubscribe(channel)
                pubsub.close()
            except Exception:
                pass
            self._pubsub = None


def _timestamp() -> int:
    """获取当前时间戳（秒）。"""
    import time
    return int(time.time())


# 同步版本（用于 Django view 返回 StreamingHttpResponse）
def subscribe(project_id: str, user_id: int):
    """
    返回 SSE generator 供 StreamingHttpResponse 使用。

    Usage:
        from django.http import StreamingHttpResponse

        def sse_view(request, project_id):
            response = subscribe(project_id, request.user.id)
            return StreamingHttpResponse(response, content_type="text/event-stream")
    """
    subscriber = SSEProgressSubscriber(project_id, user_id)

    async def generator():
        for event in subscriber.subscribe():
            yield event

    return generator()
