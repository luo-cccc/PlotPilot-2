"""依赖注入工厂 — Core / Engine / Workflow"""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Optional

from domain.ai.services.llm_service import LLMService

if TYPE_CHECKING:
    from application.engine.services.scene_director_service import SceneDirectorService

from application.core.services.novel_service import NovelService
from application.core.services.chapter_service import ChapterService
from application.engine.services.context_builder import ContextBuilder
from application.world.services.auto_bible_generator import AutoBibleGenerator
from application.world.services.auto_knowledge_generator import AutoKnowledgeGenerator
from application.analyst.services.state_extractor import StateExtractor
from application.analyst.services.state_updater import StateUpdater
from application.workflows.auto_novel_generation_workflow import AutoNovelGenerationWorkflow
from application.engine.services.hosted_write_service import HostedWriteService

from infrastructure.persistence.database.connection import get_database

from interfaces.api.dependencies_repos import (
    get_novel_repository,
    get_chapter_repository,
    get_story_node_repository,
    get_bible_repository,
    get_foreshadowing_repository,
    get_plot_arc_repository,
    get_chapter_element_repository,
    get_beat_sheet_repository,
    get_timeline_repository,
    get_storyline_repository,
)
from interfaces.api.dependencies_ai import (
    get_llm_service,
    get_vector_store,
    get_embedding_service,
    get_chapter_indexing_service,
    llm_runtime_is_mock,
)
from interfaces.api.dependencies_world import (
    get_bible_service,
    get_knowledge_service,
    get_storyline_manager,
    get_consistency_checker,
    get_relationship_engine,
)
from interfaces.api.dependencies_audit import (
    get_voice_drift_service,
    get_voice_fingerprint_service,
)

logger = logging.getLogger(__name__)


@lru_cache
def get_novel_service() -> NovelService:
    """获取 Novel 服务

    Returns:
        NovelService 实例
    """
    return NovelService(
        get_novel_repository(),
        get_chapter_repository(),
        get_story_node_repository()
    )


def get_chapter_renumber_coordinator():
    """删章后章号侧车数据（伏笔 JSON、快照内嵌 JSON、向量元数据）重排编排。"""
    from application.novel.chapter_renumber.coordinator import (
        build_default_chapter_renumber_coordinator,
    )

    return build_default_chapter_renumber_coordinator(
        db=get_database(),
        foreshadowing_repository=get_foreshadowing_repository(),
        vector_store=get_vector_store(),
    )


def get_chapter_service() -> ChapterService:
    """获取 Chapter 服务

    Returns:
        ChapterService 实例
    """
    from infrastructure.persistence.database.sqlite_chapter_review_repository import SqliteChapterReviewRepository

    review_repo = SqliteChapterReviewRepository(get_database())
    return ChapterService(
        get_chapter_repository(),
        get_novel_repository(),
        review_repo,
        chapter_renumber_coordinator=get_chapter_renumber_coordinator(),
    )


@lru_cache
def get_background_task_service():
    """单例后台任务队列（API 进程内）：文风；章末 bundle（叙事+三元组+伏笔+故事线+张力+对话+剧情点）与管线同源单次 LLM。"""
    from application.engine.services.background_task_service import BackgroundTaskService
    from infrastructure.persistence.database.triple_repository import TripleRepository
    from infrastructure.persistence.database.sqlite_storyline_repository import SqliteStorylineRepository
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository

    return BackgroundTaskService(
        voice_drift_service=get_voice_drift_service(),
        llm_service=get_llm_service(),
        foreshadowing_repo=get_foreshadowing_repository(),
        triple_repository=TripleRepository(),
        knowledge_service=get_knowledge_service(),
        chapter_indexing_service=get_chapter_indexing_service(),
        storyline_repository=SqliteStorylineRepository(get_database()),
        chapter_repository=get_chapter_repository(),
        plot_arc_repository=get_plot_arc_repository(),
        narrative_event_repository=SqliteNarrativeEventRepository(get_database()),
    )


def get_chapter_aftermath_pipeline():
    """章节保存后统一管线：叙事/向量、文风、KG 推断；三元组与伏笔、故事线、张力、对话、剧情点在叙事同步中一次 LLM 落库。"""
    from application.engine.services.chapter_aftermath_pipeline import ChapterAftermathPipeline
    from infrastructure.persistence.database.triple_repository import TripleRepository
    from infrastructure.persistence.database.sqlite_storyline_repository import SqliteStorylineRepository
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository

    return ChapterAftermathPipeline(
        knowledge_service=get_knowledge_service(),
        chapter_indexing_service=get_chapter_indexing_service(),
        llm_service=get_llm_service(),
        voice_drift_service=get_voice_drift_service(),
        triple_repository=TripleRepository(),
        foreshadowing_repository=get_foreshadowing_repository(),
        storyline_repository=SqliteStorylineRepository(get_database()),
        chapter_repository=get_chapter_repository(),
        plot_arc_repository=get_plot_arc_repository(),
        narrative_event_repository=SqliteNarrativeEventRepository(get_database()),
    )


def get_hosted_write_service() -> HostedWriteService:
    """托管连写：自动大纲 + 多章流式生成 + 可选落库。"""
    return HostedWriteService(
        get_auto_workflow(),
        get_chapter_service(),
        get_novel_service(),
        chapter_aftermath_pipeline=get_chapter_aftermath_pipeline(),
    )


@lru_cache
def get_setup_main_plot_suggestion_service():
    """向导 Step 4：主线候选推演服务。"""
    from application.blueprint.services.setup_main_plot_suggestion_service import (
        SetupMainPlotSuggestionService,
    )

    return SetupMainPlotSuggestionService(
        llm_service=get_llm_service(),
        bible_service=get_bible_service(),
        novel_service=get_novel_service(),
    )


def get_context_builder() -> ContextBuilder:
    """获取上下文构建器

    Returns:
        ContextBuilder 实例
    """
    from infrastructure.persistence.database.triple_repository import TripleRepository
    return ContextBuilder(
        bible_service=get_bible_service(),
        storyline_manager=get_storyline_manager(),
        relationship_engine=get_relationship_engine(),
        vector_store=get_vector_store(),
        novel_repository=get_novel_repository(),
        chapter_repository=get_chapter_repository(),
        plot_arc_repository=get_plot_arc_repository(),
        embedding_service=get_embedding_service(),
        foreshadowing_repository=get_foreshadowing_repository(),
        chapter_element_repository=get_chapter_element_repository(),
        triple_repository=TripleRepository(),
    )


def build_auto_workflow(llm_service: LLMService) -> AutoNovelGenerationWorkflow:
    """用指定 LLM 实例构造章节工作流（与守护进程、API 共用同一 provider 时注入同一实例）。"""
    from application.audit.services.conflict_detection_service import ConflictDetectionService
    from application.audit.services.cliche_scanner import ClicheScanner

    return AutoNovelGenerationWorkflow(
        context_builder=get_context_builder(),
        consistency_checker=get_consistency_checker(),
        storyline_manager=get_storyline_manager(),
        plot_arc_repository=get_plot_arc_repository(),
        llm_service=llm_service,
        state_extractor=get_state_extractor(),
        state_updater=get_state_updater(),
        bible_repository=get_bible_repository(),
        foreshadowing_repository=get_foreshadowing_repository(),
        voice_fingerprint_service=get_voice_fingerprint_service(),
        conflict_detection_service=ConflictDetectionService(),
        cliche_scanner=ClicheScanner(),
    )


def get_auto_workflow() -> AutoNovelGenerationWorkflow:
    """获取自动小说生成工作流

    Returns:
        AutoNovelGenerationWorkflow 实例
    """
    llm_service = get_llm_service()
    if llm_runtime_is_mock(llm_service):
        logger.warning("No API key found, using MockProvider for workflow")
    else:
        logger.info(f"Using {llm_service.__class__.__name__} for workflow")

    return build_auto_workflow(llm_service)


def get_auto_bible_generator() -> AutoBibleGenerator:
    """获取自动 Bible 生成器

    Returns:
        AutoBibleGenerator 实例
    """
    llm_service = get_llm_service()
    if llm_runtime_is_mock(llm_service):
        logger.warning("No API key found, using MockProvider for Bible generation")
    else:
        logger.info(f"Using {llm_service.__class__.__name__} for Bible generation")

    from application.world.services.worldbuilding_service import WorldbuildingService
    from infrastructure.persistence.database.worldbuilding_repository import WorldbuildingRepository
    from infrastructure.persistence.database.triple_repository import TripleRepository
    from application.paths import get_db_path

    db_path = get_db_path()
    worldbuilding_repo = WorldbuildingRepository(db_path)
    worldbuilding_service = WorldbuildingService(worldbuilding_repo)
    triple_repo = TripleRepository()

    return AutoBibleGenerator(
        llm_service=llm_service,
        bible_service=get_bible_service(),
        worldbuilding_service=worldbuilding_service,
        triple_repository=triple_repo
    )


def get_state_extractor() -> StateExtractor:
    """获取状态提取器

    Returns:
        StateExtractor 实例
    """
    return StateExtractor(llm_service=get_llm_service())


def get_auto_knowledge_generator() -> AutoKnowledgeGenerator:
    """获取自动 Knowledge 生成器

    Returns:
        AutoKnowledgeGenerator 实例
    """
    return AutoKnowledgeGenerator(
        llm_service=get_llm_service(),
        knowledge_service=get_knowledge_service()
    )


def get_state_updater() -> StateUpdater:
    """获取状态更新器

    Returns:
        StateUpdater 实例
    """
    return StateUpdater(
        bible_repository=get_bible_repository(),
        foreshadowing_repository=get_foreshadowing_repository(),
        timeline_repository=get_timeline_repository(),
        storyline_repository=get_storyline_repository(),
        knowledge_service=get_knowledge_service()
    )


def get_beat_sheet_service():
    """获取节拍表生成服务

    Returns:
        BeatSheetService 实例
    """
    from application.blueprint.services.beat_sheet_service import BeatSheetService

    llm_service = get_llm_service()
    if llm_runtime_is_mock(llm_service):
        logger.warning("No API key found, using MockProvider for beat sheet generation")
    else:
        logger.info(f"Using {llm_service.__class__.__name__} for beat sheet generation")

    return BeatSheetService(
        beat_sheet_repo=get_beat_sheet_repository(),
        chapter_repo=get_chapter_repository(),
        storyline_repo=get_storyline_repository(),
        llm_service=llm_service,
        vector_store=get_vector_store(),
        bible_service=get_bible_service()
    )


def get_scene_generation_service():
    """获取场景生成服务

    Returns:
        SceneGenerationService 实例
    """
    from application.core.services.scene_generation_service import SceneGenerationService

    llm_service = get_llm_service()
    if llm_runtime_is_mock(llm_service):
        logger.warning("No API key found, using MockProvider for scene generation")
    else:
        logger.info(f"Using {llm_service.__class__.__name__} for scene generation")

    return SceneGenerationService(
        llm_service=llm_service,
        scene_director=get_scene_director_service(),
        vector_store=get_vector_store(),
        embedding_service=get_embedding_service()
    )


def get_scene_director_service() -> "SceneDirectorService":
    """获取场景导演服务

    Returns:
        SceneDirectorService 实例
    """
    from application.engine.services.scene_director_service import SceneDirectorService

    llm_service = get_llm_service()
    if llm_runtime_is_mock(llm_service):
        logger.warning("No API key found, using MockProvider for scene director")
    else:
        logger.info(f"Using {llm_service.__class__.__name__} for scene director")

    return SceneDirectorService(llm_service=llm_service)
