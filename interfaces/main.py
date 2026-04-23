"""FastAPI 主应用

提供 RESTful API 接口。
"""
# 必须在任何 HuggingFace/Transformers 导入前设置离线模式
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
if os.getenv('DISABLE_SSL_VERIFY', 'false').lower() == 'true':
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''

from pathlib import Path
import sys
import time
import logging
from datetime import datetime

# 必须在其他 aitext 模块导入前执行：将仓库根目录 `.env` 写入 os.environ
_AITEXT_ROOT = Path(__file__).resolve().parents[1]
if str(_AITEXT_ROOT) not in sys.path:
    sys.path.insert(0, str(_AITEXT_ROOT))
try:
    from load_env import load_env

    load_env()
except Exception:
    # 无 .env 或非标准启动方式时忽略
    pass

# 配置日志（必须在导入其他模块前）
from interfaces.api.middleware.logging_config import setup_logging

log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
log_file = os.getenv("LOG_FILE", "logs/aitext.log")
setup_logging(level=log_level, log_file=log_file)

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from starlette.requests import Request
import threading
import signal
from interfaces.api.routers import register_all_routers
from interfaces.daemon_manager import on_startup, on_shutdown, get_daemon_status


# 产品发布版本（与前端 / 安装包一致）
APP_RELEASE_VERSION = "1.0.1"
# 构建标识（每次进程启动唯一）
BACKEND_BUILD_ID = datetime.now().strftime("%Y%m%d-%H%M%S")
STARTUP_TIME = time.time()

logger.info("=" * 80)
logger.info(
    "🚀 BACKEND STARTING - Release %s (build %s)",
    APP_RELEASE_VERSION,
    BACKEND_BUILD_ID,
)
logger.info(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info(f"   Log Level: {logging.getLevelName(log_level)}")
logger.info(f"   Log File: {log_file}")
logger.info(f"   Python: {sys.version.split()[0]}")
logger.info(f"   Working Dir: {Path.cwd()}")
logger.info("=" * 80)

# 创建 FastAPI 应用
app = FastAPI(
    title="PlotPilot API",
    version="1.0.1",
    description="PlotPilot（墨枢）AI 小说创作平台 API",
    redirect_slashes=True,  # 自动将 /api/v1/novels 重定向到 /api/v1/novels/
)

# ── 前端静态文件托管 ──
_FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(_FRONTEND_DIR / "assets")), name="frontend-assets")
    # favicon 等根级静态资源
    _favicon = _FRONTEND_DIR / "favicon.svg"
    if _favicon.exists():
        app.get("/favicon.svg", include_in_schema=False, response_class=FileResponse)(
            lambda: FileResponse(str(_favicon), media_type="image/svg+xml")
        )
    # SPA fallback: 所有非 API 路径都返回 index.html
    _INDEX_HTML = _FRONTEND_DIR / "index.html"

# 修复反向代理场景下 trailing slash 重定向使用后端本地地址的 bug
# 当 FastAPI 的 trailing slash 重定向指向 127.0.0.1 时，
# 从 X-Forwarded-Host / Host / Referer 获取真实地址并改写 Location header
@app.middleware("http")
async def fix_redirect_host(request, call_next):
    response = await call_next(request)
    if response.status_code in (301, 307, 308):
        location = response.headers.get("location", "")
        if location and ("127.0.0.1" in location or "localhost" in location):
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(location)
            original_host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
            if not original_host or "127.0.0.1" in original_host or "localhost" in original_host:
                referer = request.headers.get("referer", "")
                if referer:
                    from urllib.parse import urlparse as _urlparse
                    ref_host = _urlparse(referer).netloc
                    if ref_host and "127.0.0.1" not in ref_host and "localhost" not in ref_host:
                        original_host = ref_host
            if original_host and "127.0.0.1" not in original_host and "localhost" not in original_host:
                scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
                new_location = urlunparse((scheme, original_host, parsed.path, parsed.params, parsed.query, parsed.fragment))
                response.headers["location"] = new_location
    return response


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("📦 Loading modules and routes...")
    logger.info("✅ FastAPI application started successfully")
    logger.info(f"📊 Registered {len(app.routes)} routes")

    # 守护进程启动 + 运行中小说复位
    on_startup(log_level, log_file)

def _checkpoint_sqlite_wal_safe() -> None:
    """桌面端优雅退出时尽量将 WAL 落盘，降低异常断电时的损坏概率。"""
    try:
        import sqlite3

        from application.paths import get_db_path

        dbp = get_db_path()
        conn = sqlite3.connect(dbp, timeout=15.0)
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        finally:
            conn.close()
    except Exception as e:
        logger.warning("WAL checkpoint 失败（可忽略）: %s", e)



@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件（uvicorn 优雅退出时触发；Windows 桌面专用路径见 /internal/shutdown）。"""
    on_shutdown()


def _assert_internal_shutdown_localhost(request: Request) -> None:
    if not request.client:
        raise HTTPException(status_code=403, detail="forbidden")
    host = request.client.host or ""
    if host not in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        raise HTTPException(status_code=403, detail="forbidden")


def _internal_shutdown_after_response() -> None:
    """HTTP 响应已发出后再触发进程级退出，避免截断响应体。"""
    time.sleep(0.15)
    if os.name == "nt":
        on_shutdown()
        logging.shutdown()
        os._exit(0)
    os.kill(os.getpid(), signal.SIGINT)


@app.post("/internal/shutdown", include_in_schema=False)
async def internal_shutdown(request: Request):
    """仅本机：供 Tauri 在关闭窗口前触发优雅停机（Unix 走 SIGINT→uvicorn；Windows 走钩子+_exit）。"""
    _assert_internal_shutdown_localhost(request)
    threading.Thread(target=_internal_shutdown_after_response, daemon=True).start()
    return {"ok": True, "message": "shutting down"}

# 配置 CORS
# 前后端同端口部署：前端是同源请求，默认允许所有源。
# 开发环境可通过 CORS_ORIGINS 环境变量限制。
_cors_origins_env = os.getenv("CORS_ORIGINS", "")
if _cors_origins_env:
    _allowed_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
else:
    _allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP 访问日志由 uvicorn.access 输出（与 uvicorn 默认格式一致：IP + 请求行 + 状态码）

# 注册所有路由
register_all_routers(app)


@app.get("/")
async def root():
    """根路径 — 返回前端页面（SPA）或 API 欢迎消息"""
    if _FRONTEND_DIR.exists() and _INDEX_HTML.exists():
        return FileResponse(str(_INDEX_HTML), media_type="text/html")
    return {"message": "PlotPilot API", "release": APP_RELEASE_VERSION}


@app.get("/health")
async def health_check():
    """健康检查

    Returns:
        健康状态
    """
    uptime = time.time() - STARTUP_TIME
    daemon_status = get_daemon_status()
    return {
        "status": "healthy",
        "version": APP_RELEASE_VERSION,
        "build_id": BACKEND_BUILD_ID,
        "uptime_seconds": round(uptime, 2),
        "daemon_process": daemon_status,
    }


# ── SPA fallback：前端路由兜底（必须在 API 路由之后注册）──
if _FRONTEND_DIR.exists() and _INDEX_HTML.exists():
    @app.get("/{full_path:path}", include_in_schema=False)
    @app.post("/{full_path:path}", include_in_schema=False)
    @app.put("/{full_path:path}", include_in_schema=False)
    @app.patch("/{full_path:path}", include_in_schema=False)
    @app.delete("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str, req: Request):
        """SPA fallback — 所有未匹配的路径返回 index.html"""
        # 排除 API 路径、统计路由和静态资源
        if (full_path.startswith("api/") or full_path.startswith("stats/")
                or full_path.startswith("assets/") or full_path.startswith("_")):
            # 对无尾部斜杠的 API 路径做 307 重定向到带斜杠版本
            if not full_path.endswith('/'):
                redirect_url = req.url.path + '/'
                if req.url.query:
                    redirect_url += '?' + req.url.query
                return RedirectResponse(url=redirect_url, status_code=307)
            return JSONResponse({"error": "Not Found"}, status_code=404)
        return FileResponse(str(_INDEX_HTML), media_type="text/html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
