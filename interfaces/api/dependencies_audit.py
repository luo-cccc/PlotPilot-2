"""依赖注入工厂 — Audit / Voice / 叙事分析"""

import logging
from functools import lru_cache

from application.analyst.services.voice_sample_service import VoiceSampleService
from application.analyst.services.voice_fingerprint_service import VoiceFingerprintService
from application.analyst.services.voice_drift_service import VoiceDriftService

from interfaces.api.dependencies_repos import (
    get_voice_vault_repository,
    get_voice_fingerprint_repository,
    get_chapter_repository,
    get_plot_arc_repository,
    get_foreshadowing_repository,
)
from interfaces.api.dependencies_ai import get_llm_service, get_vector_store, llm_runtime_is_mock

logger = logging.getLogger(__name__)


def get_narrative_entity_state_service() -> "NarrativeEntityStateService":
    """获取叙事实体状态服务

    Returns:
        NarrativeEntityStateService 实例
    """
    from application.analyst.services.narrative_entity_state_service import NarrativeEntityStateService
    from infrastructure.persistence.database.sqlite_entity_base_repository import SqliteEntityBaseRepository
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository
    from infrastructure.persistence.database.connection import get_database

    entity_base_repo = SqliteEntityBaseRepository(get_database())
    narrative_event_repo = SqliteNarrativeEventRepository(get_database())

    return NarrativeEntityStateService(entity_base_repo, narrative_event_repo)


def get_voice_sample_service() -> VoiceSampleService:
    """获取文风样本服务

    Returns:
        VoiceSampleService 实例
    """
    return VoiceSampleService(
        get_voice_vault_repository(),
        fingerprint_service=get_voice_fingerprint_service()
    )


def get_voice_fingerprint_service() -> VoiceFingerprintService:
    """获取文风指纹服务

    Returns:
        VoiceFingerprintService 实例
    """
    return VoiceFingerprintService(
        get_voice_fingerprint_repository(),
        get_voice_vault_repository()
    )


def get_voice_drift_service() -> VoiceDriftService:
    """获取文风漂移监控服务"""
    from infrastructure.persistence.database.sqlite_chapter_style_score_repository import (
        SqliteChapterStyleScoreRepository,
    )
    from infrastructure.persistence.database.connection import get_database
    score_repo = SqliteChapterStyleScoreRepository(get_database())
    return VoiceDriftService(score_repo, get_voice_fingerprint_repository())


def get_macro_refactor_scanner():
    """获取宏观重构扫描器

    Returns:
        MacroRefactorScanner 实例
    """
    from application.audit.services.macro_refactor_scanner import MacroRefactorScanner
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository
    from infrastructure.persistence.database.connection import get_database

    narrative_event_repo = SqliteNarrativeEventRepository(get_database())
    return MacroRefactorScanner(narrative_event_repo)


def get_macro_refactor_proposal_service():
    """获取宏观重构提案服务

    Returns:
        MacroRefactorProposalService 实例
    """
    from application.audit.services.macro_refactor_proposal_service import MacroRefactorProposalService

    llm_service = get_llm_service()
    if llm_runtime_is_mock(llm_service):
        logger.warning("No API key found, using MockProvider for macro refactor proposals")
    else:
        logger.info(f"Using {llm_service.__class__.__name__} for macro refactor proposals")

    return MacroRefactorProposalService(llm_service)


def get_mutation_applier():
    """获取 Mutation 应用器

    Returns:
        MutationApplier 实例
    """
    from application.audit.services.mutation_applier import MutationApplier
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository
    from infrastructure.persistence.database.connection import get_database

    narrative_event_repo = SqliteNarrativeEventRepository(get_database())
    return MutationApplier(narrative_event_repo)


def get_macro_diagnosis_service():
    """获取宏观诊断服务

    Returns:
        MacroDiagnosisService 实例
    """
    from application.audit.services.macro_diagnosis_service import MacroDiagnosisService
    from application.audit.services.macro_refactor_scanner import MacroRefactorScanner
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository
    from infrastructure.persistence.database.connection import get_database

    db = get_database()
    narrative_event_repo = SqliteNarrativeEventRepository(db)
    scanner = MacroRefactorScanner(narrative_event_repo)
    return MacroDiagnosisService(db, scanner)


def get_tension_analyzer():
    """获取张力分析器

    Returns:
        TensionAnalyzer 实例
    """
    from application.analyst.services.tension_analyzer import TensionAnalyzer
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository
    from infrastructure.persistence.database.connection import get_database

    llm_provider = get_llm_service()
    if llm_runtime_is_mock(llm_provider):
        logger.warning("No API key found, using MockProvider for tension analyzer")
    else:
        logger.info(f"Using {llm_provider.__class__.__name__} for tension analyzer")

    narrative_event_repo = SqliteNarrativeEventRepository(get_database())
    return TensionAnalyzer(
        narrative_event_repo,
        llm_provider,
        chapter_repository=get_chapter_repository(),
        plot_arc_repository=get_plot_arc_repository(),
    )


def get_sandbox_dialogue_service():
    """获取沙盘对白服务

    Returns:
        SandboxDialogueService 实例
    """
    from application.workbench.services.sandbox_dialogue_service import SandboxDialogueService
    from infrastructure.persistence.database.sqlite_narrative_event_repository import SqliteNarrativeEventRepository
    from infrastructure.persistence.database.connection import get_database

    narrative_event_repo = SqliteNarrativeEventRepository(get_database())
    return SandboxDialogueService(narrative_event_repo)


def get_chapter_review_service():
    """获取章节审稿服务

    Returns:
        ChapterReviewService 实例
    """
    from application.audit.services.chapter_review_service import ChapterReviewService
    from infrastructure.persistence.database.sqlite_chapter_repository import SqliteChapterRepository
    from infrastructure.persistence.database.sqlite_cast_repository import SqliteCastRepository
    from infrastructure.persistence.database.sqlite_timeline_repository import SqliteTimelineRepository
    from infrastructure.persistence.database.sqlite_storyline_repository import SqliteStorylineRepository
    from infrastructure.persistence.database.sqlite_foreshadowing_repository import SqliteForeshadowingRepository
    from infrastructure.persistence.database.connection import get_database

    db = get_database()
    chapter_repo = SqliteChapterRepository(db)
    cast_repo = SqliteCastRepository(db)
    timeline_repo = SqliteTimelineRepository(db)
    storyline_repo = SqliteStorylineRepository(db)
    foreshadowing_repo = SqliteForeshadowingRepository(db)
    vector_store = get_vector_store()
    llm_service = get_llm_service()

    return ChapterReviewService(
        chapter_repo=chapter_repo,
        cast_repo=cast_repo,
        timeline_repo=timeline_repo,
        storyline_repo=storyline_repo,
        foreshadowing_repo=foreshadowing_repo,
        vector_store=vector_store,
        llm_service=llm_service
    )


def get_foreshadow_ledger_service():
    """获取伏笔台账服务

    Returns:
        伏笔台账服务实例
    """
    from application.analyst.services.foreshadow_ledger_service import ForeshadowLedgerService
    return ForeshadowLedgerService(get_foreshadowing_repository())
