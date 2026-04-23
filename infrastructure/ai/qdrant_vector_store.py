"""Qdrant 向量存储实现

基于 Qdrant Cloud / 自托管 Qdrant 的向量存储。
使用 qdrant-client 与 Qdrant 交互。
"""
from typing import List, Optional

from domain.ai.services.vector_store import VectorStore

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError as e:
    raise ImportError(
        "检测到您正在尝试使用 Qdrant 向量存储，但缺少必要的依赖包！\n\n"
        "请安装 qdrant-client：\n"
        "  pip install qdrant-client\n\n"
        f"原始错误: {e}"
    ) from e


class QdrantVectorStore(VectorStore):
    """Qdrant 向量存储实现

    支持 Qdrant Cloud 和自托管 Qdrant 实例。
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        url: Optional[str] = None,
    ):
        """
        初始化 Qdrant 客户端

        Args:
            host: Qdrant 主机地址（当 url 未指定时使用）
            port: Qdrant 端口（当 url 未指定时使用）
            api_key: Qdrant API Key（Qdrant Cloud 需要）
            url: 完整的 Qdrant URL（优先于 host/port）
        """
        if url:
            self.client = QdrantClient(url=url, api_key=api_key, prefer_grpc=False, check_compatibility=False)
        else:
            self.client = QdrantClient(host=host, port=port, api_key=api_key, prefer_grpc=False, check_compatibility=False)

    async def insert(
        self,
        collection: str,
        id: str,
        vector: List[float],
        payload: dict,
    ) -> None:
        """插入或更新向量到集合"""
        try:
            self.client.upsert(
                collection_name=collection,
                points=[
                    models.PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
        except Exception as e:
            raise Exception(f"Failed to insert vector: {e}") from e

    async def search(
        self,
        collection: str,
        query_vector: List[float],
        limit: int,
    ) -> List[dict]:
        """搜索相似向量"""
        try:
            results = self.client.query_points(
                collection_name=collection,
                query=query_vector,
                limit=limit,
            )
            output = []
            for point in results.points:
                output.append({
                    "id": str(point.id),
                    "score": point.score,
                    "payload": point.payload or {},
                })
            return output
        except Exception as e:
            raise Exception(f"Failed to search vectors: {e}") from e

    async def delete(
        self,
        collection: str,
        id: str,
    ) -> None:
        """删除向量"""
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(points=[id]),
            )
        except Exception as e:
            raise Exception(f"Failed to delete vector: {e}") from e

    async def create_collection(
        self,
        collection: str,
        dimension: int,
    ) -> None:
        """创建集合（若已存在则跳过）"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            if collection in collection_names:
                return
            self.client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(
                    size=dimension,
                    distance=models.Distance.COSINE,
                ),
            )
        except Exception as e:
            raise Exception(f"Failed to create collection: {e}") from e

    async def delete_collection(
        self,
        collection: str,
    ) -> None:
        """删除集合"""
        try:
            self.client.delete_collection(collection_name=collection)
        except Exception as e:
            raise Exception(f"Failed to delete collection: {e}") from e

    async def list_collections(self) -> List[str]:
        """列出所有集合"""
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]
        except Exception as e:
            raise Exception(f"Failed to list collections: {e}") from e
