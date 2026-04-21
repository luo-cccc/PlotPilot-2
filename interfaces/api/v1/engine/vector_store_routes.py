"""向量存储管理 API（系统维护用）"""
import logging
import os
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, status

from interfaces.api.dependencies import get_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/vector-store", tags=["vector-store-admin"])


@router.get("/collections", response_model=List[str])
async def list_vector_collections() -> List[str]:
    """列出所有向量 collection 名称。"""
    vs = get_vector_store()
    if vs is None:
        return []
    try:
        if hasattr(vs, "list_collections"):
            return await vs.list_collections()
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="当前向量存储不支持列举 collection"
        )
    except Exception as e:
        logger.error(f"列出 vector collections 失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/collections", response_model=dict)
async def clear_all_vector_collections() -> dict:
    """删除所有向量 collection（清理本地向量数据和 Qdrant 数据）。"""
    vs = get_vector_store()
    if vs is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="向量存储未启用")
    try:
        if not hasattr(vs, "list_collections") or not hasattr(vs, "delete_collection"):
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="当前向量存储不支持删除 collection"
            )
        collections = await vs.list_collections()
        deleted: List[str] = []
        for coll in collections:
            try:
                await vs.delete_collection(coll)
                deleted.append(coll)
            except Exception as e:
                logger.warning(f"删除 collection {coll} 失败: {e}")
        return {"deleted": deleted, "total": len(deleted)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空向量存储失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/collections/{collection}", response_model=dict)
async def delete_vector_collection(collection: str) -> dict:
    """删除指定 collection。"""
    vs = get_vector_store()
    if vs is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="向量存储未启用")
    try:
        if not hasattr(vs, "delete_collection"):
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="当前向量存储不支持删除 collection"
            )
        await vs.delete_collection(collection)
        return {"collection": collection, "deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除 collection {collection} 失败: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/embedding-cache", response_model=dict)
async def clear_embedding_cache() -> dict:
    """清理 HuggingFace embedding 模型缓存（~/.cache/huggingface/）。

    清理后再次生成向量时需重新下载模型（约 100MB～数 GB）。
    """
    cache_dirs: List[str] = []
    cleared: List[str] = []
    errors: List[str] = []

    hf_cache = Path.home() / ".cache" / "huggingface"
    if hf_cache.exists():
        cache_dirs.append(str(hf_cache))
        try:
            shutil.rmtree(hf_cache)
            cleared.append(str(hf_cache))
        except Exception as e:
            errors.append(f"HuggingFace cache: {e}")
            logger.warning(f"清理 HuggingFace cache 失败: {e}")

    return {
        "cache_dirs": cache_dirs,
        "cleared": cleared,
        "errors": errors,
    }


@router.delete("/all", response_model=dict)
async def clear_all_vector_and_cache() -> dict:
    """清理所有向量数据和 embedding 缓存（一次性全部清理）。"""
    results: dict = {"vector_collections": {}, "embedding_cache": {}, "chromadb_dir": {}}

    vs = get_vector_store()
    if vs is not None and hasattr(vs, "list_collections") and hasattr(vs, "delete_collection"):
        try:
            collections = await vs.list_collections()
            deleted: List[str] = []
            for coll in collections:
                try:
                    await vs.delete_collection(coll)
                    deleted.append(coll)
                except Exception as e:
                    logger.warning(f"删除 collection {coll} 失败: {e}")
            results["vector_collections"] = {"deleted": deleted, "total": len(deleted)}
        except Exception as e:
            results["vector_collections"] = {"error": str(e)}
            logger.error(f"清空向量 collections 失败: {e}")
    else:
        results["vector_collections"] = {"skipped": "vector store unavailable or not supported"}

    hf_cache = Path.home() / ".cache" / "huggingface"
    try:
        if hf_cache.exists():
            shutil.rmtree(hf_cache)
            results["embedding_cache"] = {"cleared": str(hf_cache)}
        else:
            results["embedding_cache"] = {"skipped": "cache not found"}
    except Exception as e:
        results["embedding_cache"] = {"error": str(e)}
        logger.warning(f"清理 HuggingFace cache 失败: {e}")

    chromadb_dir = Path(os.getenv("VECTOR_STORE_PATH", "./data/chromadb"))
    try:
        if chromadb_dir.exists():
            shutil.rmtree(chromadb_dir)
            results["chromadb_dir"] = {"cleared": str(chromadb_dir)}
        else:
            results["chromadb_dir"] = {"skipped": "directory not found"}
    except Exception as e:
        results["chromadb_dir"] = {"error": str(e)}
        logger.warning(f"清理 ChromaDB 目录失败: {e}")

    return results
