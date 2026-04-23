"""依赖注入工厂 — World / Bible / Cast / Knowledge"""

import logging
from functools import lru_cache

from application.world.services.bible_service import BibleService
from application.world.services.cast_service import CastService
from application.world.services.knowledge_service import KnowledgeService
from domain.novel.services.storyline_manager import StorylineManager
from domain.novel.services.consistency_checker import ConsistencyChecker
from domain.bible.services.relationship_engine import RelationshipEngine

from interfaces.api.dependencies_repos import (
    get_bible_repository,
    get_novel_repository,
    get_chapter_repository,
    get_knowledge_repository,
    get_storyline_repository,
)
from interfaces.api.dependencies_ai import get_storage

logger = logging.getLogger(__name__)


@lru_cache
def get_bible_service() -> BibleService:
    """获取 Bible 服务

    Returns:
        BibleService 实例
    """
    from application.paths import get_db_path
    from application.world.services.bible_location_triple_sync import BibleLocationTripleSyncService
    from infrastructure.persistence.database.triple_repository import TripleRepository

    sync = BibleLocationTripleSyncService(TripleRepository())
    return BibleService(
        get_bible_repository(),
        novel_repository=get_novel_repository(),
        chapter_repository=get_chapter_repository(),
        location_triple_sync=sync,
    )


def get_cast_service() -> CastService:
    """获取 Cast 服务

    Returns:
        CastService 实例
    """
    storage = get_storage()
    storage_root = storage.base_path
    return CastService(storage_root, knowledge_repository=get_knowledge_repository())


def get_knowledge_service() -> KnowledgeService:
    """获取 Knowledge 服务

    Returns:
        KnowledgeService 实例
    """
    return KnowledgeService(get_knowledge_repository())


def get_storyline_manager() -> StorylineManager:
    """获取 Storyline 管理器

    Returns:
        StorylineManager 实例
    """
    return StorylineManager(get_storyline_repository())


def get_consistency_checker() -> ConsistencyChecker:
    """获取一致性检查器

    Returns:
        ConsistencyChecker 实例
    """
    return ConsistencyChecker()


def get_relationship_engine() -> RelationshipEngine:
    """获取关系引擎

    Returns:
        RelationshipEngine 实例
    """
    from domain.bible.value_objects.relationship_graph import RelationshipGraph
    return RelationshipEngine(RelationshipGraph())
