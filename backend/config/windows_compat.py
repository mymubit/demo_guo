"""
Windows 本地开发兼容（dj_queue 依赖 Unix 的 fcntl / SIGQUIT）。

生产 Linux/Docker 不受影响。
"""
from __future__ import annotations

import sys
import types


def apply() -> None:
    if sys.platform != "win32":
        return

    _stub_fcntl()


def apply_after_django_setup() -> None:
    if sys.platform != "win32":
        return
    if len(sys.argv) > 1 and sys.argv[1] == "dj_queue":
        _patch_dj_queue_async_supervisor()


def _stub_fcntl() -> None:
    if "fcntl" in sys.modules:
        return
    try:
        import fcntl  # noqa: F401
    except ModuleNotFoundError:
        stub = types.ModuleType("fcntl")
        stub.LOCK_EX = 2
        stub.LOCK_NB = 4
        stub.LOCK_UN = 8

        def _flock(fd, op):  # noqa: ARG001
            return None

        stub.flock = _flock
        sys.modules["fcntl"] = stub


def _patch_dj_queue_async_supervisor() -> None:
    import signal

    from dj_queue.runtime.supervisor import AsyncSupervisor

    def register_signal_handlers(self):
        signal.signal(signal.SIGINT, self.handle_sigterm)
        if hasattr(signal, "SIGTERM"):
            try:
                signal.signal(signal.SIGTERM, self.handle_sigterm)
            except ValueError:
                pass

    AsyncSupervisor.register_signal_handlers = register_signal_handlers
