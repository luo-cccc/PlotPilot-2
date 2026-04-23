"""依赖注入工厂 — Repository 仓储层"""

import logging
from functools import lru_cache

from application.paths import DATA_DIR
from infrastructure.persistence.database.connection import get_database
from infrastructure.persistence.database.sqlite_novel_repository import SqliteNovelRepository
from infrastructure.persistence.database.sqlite_chapter_repository import SqliteChapterRepository
from infrastructure.persistence.database.sqlite_knowledge_repository import SqliteKnowledgeRepository
from infrastructure.persistence.database.sqlite_bible_repository import SqliteBibleRepository
from infrastructure.persistence.database.sqlite_storyline_repository import SqliteStorylineRepository
from infrastructure.persistence.database.sqlite_plot_arc_repository import SqlitePlotArcRepository
from infrastructure.persistence.database.sqlite_voice_vault_repository import SqliteVoiceVaultRepository
from infrastructure.persistence.database.sqlite_voice_fingerprint_repository import SQLiteVoiceFingerprintRepository
from infrastructure.persistence.database.story_node_repository import StoryNodeRepository
from infrastructure.persistence.database.sqlite_cast_repository import SqliteCastRepository
from infrastructure.persistence.database.sqlite_foreshadowing_repository import SqliteForeshadowingRepository
from infrastructure.persistence.database.sqlite_timeline_repository import SqliteTimelineRepository

logger = logging.getLogger(__name__)


@lru_cache
def get_novel_repository() -> SqliteNovelRepository:
    """获取 Novel 仓储（SQLite）

    Returns:
        SqliteNovelRepository 实例
    """
    return SqliteNovelRepository(get_database())


def get_chapter_repository() -> SqliteChapterRepository:
    """获取 Chapter 仓储（SQLite）

    Returns:
        SqliteChapterRepository 实例
    """
    return SqliteChapterRepository(get_database())


def get_chapter_element_repository():
    """获取章节元素仓储

    Returns:
        ChapterElementRepository 实例
    """
    from infrastructure.persistence.database.chapter_element_repository import ChapterElementRepository
    from application.paths import get_db_path
    return ChapterElementRepository(get_db_path())


def get_bible_repository() -> SqliteBibleRepository:
    """获取 Bible 仓储（SQLite 唯一数据源）。"""
    return SqliteBibleRepository(get_database())


def get_cast_repository() -> SqliteCastRepository:
    """获取 Cast 仓储（SQLite JSON Blob）

    Returns:
        SqliteCastRepository 实例
    """
    return SqliteCastRepository(get_database())


def get_knowledge_repository() -> SqliteKnowledgeRepository:
    """获取 Knowledge 仓储（SQLite）

    Returns:
        SqliteKnowledgeRepository 实例
    """
    return SqliteKnowledgeRepository(get_database())


def get_storyline_repository() -> SqliteStorylineRepository:
    """获取 Storyline 仓储（SQLite）。"""
    return SqliteStorylineRepository(get_database())


def get_plot_arc_repository() -> SqlitePlotArcRepository:
    """获取 PlotArc 仓储（SQLite）。"""
    return SqlitePlotArcRepository(get_database())


def get_foreshadowing_repository() -> SqliteForeshadowingRepository:
    """伏笔与潜台词账本仓储（SQLite，与 novels 同库；不再使用 foreshadowings/*.json）。"""
    return SqliteForeshadowingRepository(get_database())


def get_snapshot_service():
    """语义快照服务（novel_snapshots；用于编年史 BFF 与回滚）。"""
    from application.snapshot.services.snapshot_service import SnapshotService

    return SnapshotService(
        get_database(),
        get_chapter_repository(),
        get_foreshadowing_repository(),
    )


def get_timeline_repository() -> SqliteTimelineRepository:
    """获取时间线仓储"""
    return SqliteTimelineRepository(get_database())


def get_beat_sheet_repository():
    """获取节拍表仓储"""
    from infrastructure.persistence.database.sqlite_beat_sheet_repository import SqliteBeatSheetRepository
    return SqliteBeatSheetRepository(get_database())


def get_story_node_repository() -> StoryNodeRepository:
    """获取 StoryNode 仓储

    Returns:
        StoryNodeRepository 实例
    """
    db_path = str(DATA_DIR / "aitext.db")
    return StoryNodeRepository(db_path)


def get_voice_vault_repository() -> SqliteVoiceVaultRepository:
    """获取 Voice Vault 仓储（SQLite）

    Returns:
        SqliteVoiceVaultRepository 实例
    """
    return SqliteVoiceVaultRepository(get_database())


def get_voice_fingerprint_repository() -> SQLiteVoiceFingerprintRepository:
    """获取 Voice Fingerprint 仓储（SQLite）

    Returns:
        SQLiteVoiceFingerprintRepository 实例
    """
    return SQLiteVoiceFingerprintRepository(get_database())
