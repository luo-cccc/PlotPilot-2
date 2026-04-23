"""依赖注入工厂 — AI / LLM / 基础设施层"""

import logging
import os
from functools import lru_cache
from typing import Optional

from application.paths import DATA_DIR
from infrastructure.persistence.storage.file_storage import FileStorage
from infrastructure.ai.config.settings import Settings
from infrastructure.ai.provider_factory import DynamicLLMService, LLMProviderFactory
from application.ai.llm_control_service import LLMControlService
from domain.ai.services.llm_service import LLMService
from domain.ai.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

# 全局存储实例
_storage = None


def _anthropic_api_key() -> Optional[str]:
    """优先 ANTHROPIC_API_KEY，否则 ANTHROPIC_AUTH_TOKEN（与部分代理/IDE 配置命名一致）。"""
    raw = os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
    if raw is None:
        return None
    key = raw.strip()
    return key or None


def _anthropic_base_url() -> Optional[str]:
    u = os.getenv("ANTHROPIC_BASE_URL")
    return u.strip() if u and u.strip() else None


def _anthropic_settings(require_key: bool = True) -> Optional[Settings]:
    """构建 Anthropic Settings；require_key=False 时无密钥返回 None。"""
    key = _anthropic_api_key()
    if not key:
        if require_key:
            raise ValueError(
                "Set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN (optional: ANTHROPIC_BASE_URL)"
            )
        return None
    return Settings(
        api_key=key,
        base_url=_anthropic_base_url(),
        default_model=os.getenv("WRITING_MODEL", ""),
    )


def _openai_api_key() -> Optional[str]:
    raw = os.getenv("OPENAI_API_KEY")
    if raw is None:
        return None
    key = raw.strip()
    return key or None


def _openai_base_url() -> Optional[str]:
    u = os.getenv("OPENAI_BASE_URL")
    return u.strip() if u and u.strip() else None


def _openai_settings(require_key: bool = True) -> Optional[Settings]:
    """构建 OpenAI Settings；require_key=False 时无密钥返回 None。"""
    key = _openai_api_key()
    if not key:
        if require_key:
            raise ValueError(
                "Set OPENAI_API_KEY (optional: OPENAI_BASE_URL)"
            )
        return None
    return Settings(
        api_key=key,
        base_url=_openai_base_url(),
        default_model=os.getenv("WRITING_MODEL") or os.getenv("ARK_MODEL", ""),
    )


@lru_cache
def get_llm_control_service() -> LLMControlService:
    return LLMControlService()


@lru_cache
def get_llm_provider_factory() -> LLMProviderFactory:
    return LLMProviderFactory(get_llm_control_service())


def llm_runtime_is_mock(llm_service: Optional[LLMService] = None) -> bool:
    runtime = get_llm_control_service().get_runtime_summary()
    return runtime.using_mock


def get_storage() -> FileStorage:
    """获取存储后端实例

    Returns:
        FileStorage 实例
    """
    global _storage
    if _storage is None:
        _storage = FileStorage(DATA_DIR)
    return _storage


def get_llm_service():
    """获取动态 LLM 服务实例。

    返回长生命周期包装器：每次 generate/stream_generate 时重新读取当前激活配置，
    因此前台控制面板修改后无需重启 API / 守护进程即可生效。
    """
    return DynamicLLMService(get_llm_provider_factory())


def get_embedding_service():
    """获取 Embedding 服务（优先从数据库读取配置，环境变量作为 fallback）。

    配置优先级：
    1. 数据库 embedding_config 表中的 mode / api_key / base_url / model / model_path / use_gpu
    2. 环境变量 EMBEDDING_SERVICE / EMBEDDING_MODEL_PATH 等
    3. 环境变量 EMBEDDING_MODEL / EMBEDDING_MODEL_PATH（无代码内写死的模型名）

    如果 VECTOR_STORE_ENABLED=false，返回 None。
    """
    if os.getenv("VECTOR_STORE_ENABLED", "true").lower() != "true":
        return None

    _mode = "local"
    _api_key = ""
    _base_url = ""
    _model = ""
    _model_path = ""
    _use_gpu = True

    try:
        from application.ai.embedding_config_service import get_embedding_config_service
        cfg_svc = get_embedding_config_service()
        cfg = cfg_svc.get_config()
        _mode = cfg.mode
        _api_key = cfg.api_key
        _base_url = cfg.base_url
        _model = (cfg.model or "").strip()
        _model_path = (cfg.model_path or "").strip()
        _use_gpu = cfg.use_gpu
        logger.info(
            "Embedding 配置来源: 数据库 | mode=%s, model=%s, path=%s",
            _mode, _model, _model_path,
        )
        if not _model and not _model_path:
            logger.info("数据库配置为空，回退到环境变量")
            _mode = os.getenv("EMBEDDING_SERVICE", "local").lower()
            _api_key = os.getenv("EMBEDDING_API_KEY") or ""
            _base_url = os.getenv("EMBEDDING_BASE_URL") or ""
            _model = (os.getenv("EMBEDDING_MODEL") or "").strip()
            _model_path = (os.getenv("EMBEDDING_MODEL_PATH") or "").strip()
            _use_gpu = os.getenv("EMBEDDING_USE_GPU", "true").lower() == "true"
    except Exception as exc:
        _mode = os.getenv("EMBEDDING_SERVICE", "local").lower()
        _api_key = os.getenv("EMBEDDING_API_KEY") or ""
        _base_url = os.getenv("EMBEDDING_BASE_URL") or ""
        _model = (os.getenv("EMBEDDING_MODEL") or "").strip()
        _model_path = (os.getenv("EMBEDDING_MODEL_PATH") or "").strip()
        _use_gpu = os.getenv("EMBEDDING_USE_GPU", "true").lower() == "true"
        logger.warning("读取嵌入配置失败，回退到环境变量: %s", exc)

    try:
        if _mode == "openai":
            key = _api_key or os.getenv("EMBEDDING_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
            _is_local = _base_url and ("localhost" in _base_url or "127.0.0.1" in _base_url)
            if not key and not _is_local:
                logger.warning("embedding mode=openai 但未配置 API Key，向量检索已禁用")
                return None
            if not (_model or "").strip():
                logger.warning("embedding mode=openai 但未配置模型 ID（model / EMBEDDING_MODEL），向量检索已禁用")
                return None
            from infrastructure.ai.openai_embedding_service import OpenAIEmbeddingService
            logger.info("使用 OpenAI 嵌入服务 (DB配置): base_url=%s, model=%s", _base_url, _model)
            return OpenAIEmbeddingService(
                api_key=key,
                base_url=_base_url or None,
                model=_model,
            )
        else:
            if not (_model_path or "").strip():
                logger.warning("embedding mode=local 但未配置 model_path，向量检索已禁用")
                return None
            from infrastructure.ai.local_embedding_service import LocalEmbeddingService
            logger.info("使用本地嵌入服务 (DB配置): path=%s, gpu=%s", _model_path, _use_gpu)
            return LocalEmbeddingService(model_name=_model_path, use_gpu=_use_gpu)
    except Exception as e:
        logger.warning("EmbeddingService 初始化失败: %s", e)
        return None


def get_chapter_indexing_service():
    """获取章节索引服务（依赖 VectorStore + Embedding，任一不可用则返回 None）。"""
    vs = get_vector_store()
    es = get_embedding_service()
    if vs is None or es is None:
        return None
    from application.analyst.services.chapter_indexing_service import ChapterIndexingService
    return ChapterIndexingService(vs, es)


def get_triple_indexing_service():
    """获取三元组索引服务（依赖 VectorStore + Embedding，任一不可用则返回 None）。

    用于将三元组向量化并支持语义检索。
    """
    vs = get_vector_store()
    es = get_embedding_service()
    if vs is None or es is None:
        return None
    from application.analyst.services.triple_indexing_service import TripleIndexingService
    return TripleIndexingService(vs, es)


_vector_store_singleton: Optional[VectorStore] = None


def get_vector_store() -> Optional[VectorStore]:
    """获取向量存储（单例，整个进程共享同一实例）

    根据 VECTOR_STORE_TYPE 自动选择实现：
    - "qdrant" → QdrantVectorStore（推荐，需外部 Qdrant 服务）
    - "chromadb" 或其他 → ChromaDBVectorStore（本地 FAISS，需 faiss 依赖）

    Returns:
        VectorStore 实例或 None
    """
    global _vector_store_singleton
    if _vector_store_singleton is not None:
        return _vector_store_singleton

    enabled = os.getenv("VECTOR_STORE_ENABLED", "true").lower() == "true"
    if not enabled:
        return None

    store_type = os.getenv("VECTOR_STORE_TYPE", "chromadb").lower()
    qdrant_enabled = os.getenv("QDRANT_ENABLED", "").lower() in {"1", "true", "yes", "on"}
    use_qdrant = store_type == "qdrant" or qdrant_enabled

    if use_qdrant:
        try:
            from infrastructure.ai.qdrant_vector_store import QdrantVectorStore
            kwargs = {
                "host": os.getenv("QDRANT_HOST", "localhost"),
                "port": int(os.getenv("QDRANT_PORT", "6333")),
                "api_key": os.getenv("QDRANT_API_KEY") or None,
            }
            qdrant_url = os.getenv("QDRANT_URL")
            if qdrant_url:
                kwargs["url"] = qdrant_url
            _vector_store_singleton = QdrantVectorStore(**kwargs)
            return _vector_store_singleton
        except Exception as e:
            logger.warning(f"Failed to initialize Qdrant vector store: {e}")
            return None

    try:
        from infrastructure.ai.chromadb_vector_store import ChromaDBVectorStore
        persist_dir = os.getenv("VECTOR_STORE_PATH", "./data/chromadb")
        _vector_store_singleton = ChromaDBVectorStore(persist_directory=persist_dir)
        return _vector_store_singleton
    except Exception as e:
        logger.warning(f"Failed to initialize vector store: {e}")
        return None
