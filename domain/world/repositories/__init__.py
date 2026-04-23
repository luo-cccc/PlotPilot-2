"""World 域仓储接口聚合

合并 Bible、Cast、Knowledge 仓储接口到统一入口。
ForeshadowingRepository 保留在 domain.novel.repositories（与小说叙事紧耦合）。
"""

from domain.bible.repositories.bible_repository import BibleRepository
from domain.cast.repositories.cast_repository import CastRepository
from domain.knowledge.repositories.knowledge_repository import KnowledgeRepository

__all__ = ["BibleRepository", "CastRepository", "KnowledgeRepository"]
