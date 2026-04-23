from __future__ import annotations

"""自动驾驶守护进程进程管理器

将 main.py 中的守护进程生命周期管理提取到此处，降低 main.py 复杂度。
"""
import os
import sys
import threading
import multiprocessing
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── 进程级全局状态 ──
_daemon_process: multiprocessing.Process | None = None
_daemon_stop_event: multiprocessing.Event | None = None


def _is_expected_daemon_shutdown_exception(exc: BaseException) -> bool:
    """热重载/停止时的中断视为正常退出，避免子进程打印长栈。"""
    import asyncio
    current = exc
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if isinstance(current, (KeyboardInterrupt, asyncio.CancelledError)):
            return True
        current = current.__cause__ or current.__context__
    return False


def _stop_all_running_novels() -> None:
    """重启时将所有运行中的小说设置为停止状态。"""
    try:
        from application.paths import get_db_path
        import sqlite3

        db_path = get_db_path()
        db_path_obj = Path(db_path) if isinstance(db_path, str) else db_path

        if not db_path_obj.exists():
            logger.warning("⚠️  数据库文件不存在: %s", db_path)
            return

        conn = sqlite3.connect(str(db_path_obj), timeout=10.0)
        try:
            cur = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='novels' LIMIT 1"
            )
            if cur.fetchone() is None:
                logger.info("ℹ️  新库尚无 novels 表，跳过运行中小说复位")
                return

            cursor = conn.execute(
                "SELECT COUNT(*) FROM novels WHERE autopilot_status = 'running'"
            )
            running_count = cursor.fetchone()[0]

            if running_count > 0:
                conn.execute(
                    "UPDATE novels SET autopilot_status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE autopilot_status = 'running'"
                )
                conn.commit()
                logger.info("🔒 已将 %d 本运行中的小说设置为停止状态（服务重启）", running_count)
            else:
                logger.info("✅ 没有运行中的小说需要停止")
        finally:
            conn.close()
    except Exception as e:
        logger.error("❌ 停止运行中小说失败: %s", e, exc_info=True)


def _run_daemon_in_process(
    stop_event: threading.Event,
    log_level: int,
    log_file: str,
    stream_queue=None,
):
    """在独立进程中运行守护进程（完全隔离，不阻塞主进程）。"""
    from interfaces.api.middleware.logging_config import setup_logging

    setup_logging(level=log_level, log_file=log_file)

    if stream_queue is not None:
        from application.engine.services.streaming_bus import inject_stream_queue

        inject_stream_queue(stream_queue)
        logger.info("✅ 守护进程：流式队列已注入")

    try:
        _scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
        if _scripts_dir not in sys.path:
            sys.path.insert(0, _scripts_dir)
        from start_daemon import build_daemon

        daemon = build_daemon()
        logger.info("🚀 守护进程已启动（独立进程），开始轮询...")

        while not stop_event.is_set():
            try:
                active_novels = daemon._get_active_novels()
                if active_novels:
                    import asyncio

                    for novel in active_novels:
                        if stop_event.is_set():
                            break
                        asyncio.run(daemon._process_novel(novel))
                stop_event.wait(timeout=daemon.poll_interval)
            except BaseException as e:
                if stop_event.is_set() or _is_expected_daemon_shutdown_exception(e):
                    logger.info("ℹ️ 守护进程在停止/热重载期间中断，正常退出")
                    break
                logger.error("❌ 守护进程异常: %s", e, exc_info=True)
                stop_event.wait(timeout=10)
    except BaseException as e:
        if stop_event.is_set() or _is_expected_daemon_shutdown_exception(e):
            logger.info("ℹ️ 守护进程收到停止信号，正常退出")
        else:
            logger.error("❌ 守护进程初始化失败: %s", e, exc_info=True)
    finally:
        logger.info("🛑 守护进程已停止")


def start_autopilot_daemon(log_level: int, log_file: str) -> None:
    """启动自动驾驶守护进程（独立进程，不阻塞主事件循环）。"""
    global _daemon_process, _daemon_stop_event

    if _daemon_process is not None and _daemon_process.is_alive():
        logger.warning("⚠️  守护进程已在运行，跳过重复启动")
        return

    if os.getenv("DISABLE_AUTO_DAEMON", "").lower() in ("1", "true", "yes"):
        logger.info("🔒 守护进程自动启动已禁用（DISABLE_AUTO_DAEMON=1）")
        return

    from application.engine.services.streaming_bus import init_streaming_bus

    stream_queue = init_streaming_bus()
    _daemon_stop_event = multiprocessing.Event()
    _daemon_process = multiprocessing.Process(
        target=_run_daemon_in_process,
        args=(_daemon_stop_event, log_level, log_file, stream_queue),
        name="AutopilotDaemon",
        daemon=True,
    )
    _daemon_process.start()
    logger.info("✅ 守护进程已创建并启动（独立进程模式，流式队列已传递）")


def stop_autopilot_daemon() -> None:
    """停止守护进程。"""
    global _daemon_process, _daemon_stop_event

    if _daemon_stop_event:
        logger.info("🛑 正在停止守护进程...")
        _daemon_stop_event.set()

    if _daemon_process and _daemon_process.is_alive():
        _daemon_process.join(timeout=5)
        if _daemon_process.is_alive():
            logger.warning("⚠️  守护进程未在超时时间内停止，强制终止")
            _daemon_process.terminate()
            _daemon_process.join(timeout=2)
        else:
            logger.info("✅ 守护进程已成功停止")

    _daemon_process = None
    _daemon_stop_event = None


def restart_autopilot_daemon(log_level: int, log_file: str) -> None:
    """重启守护进程以拾取新的 LLM / 嵌入配置。"""
    stop_autopilot_daemon()
    start_autopilot_daemon(log_level, log_file)
    logger.info("🔄 守护进程已因配置变更重启")


def get_daemon_status() -> dict:
    """获取守护进程状态（供 health check 使用）。"""
    return {
        "running": _daemon_process is not None and _daemon_process.is_alive(),
        "pid": _daemon_process.pid if _daemon_process else None,
    }


def on_startup(log_level: int, log_file: str) -> None:
    """应用启动时的守护进程初始化。"""
    _stop_all_running_novels()
    start_autopilot_daemon(log_level, log_file)


def on_shutdown() -> None:
    """应用关闭时的守护进程清理。"""
    stop_autopilot_daemon()
