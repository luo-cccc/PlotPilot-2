"""FastAPI 路由统一注册模块

将 main.py 中的路由注册逻辑提取到此处，降低 main.py 的复杂度。
"""
from fastapi import FastAPI

# Core module
from interfaces.api.v1.core import novels, chapters, scene_generation_routes, settings as llm_settings, export

# World module
from interfaces.api.v1.world import bible, cast, knowledge, knowledge_graph_routes, worldbuilding_routes

# Blueprint module
from interfaces.api.v1.blueprint import continuous_planning_routes, beat_sheet_routes, story_structure

# Engine module routes
from interfaces.api.v1.engine import (
    generation,
    context_intelligence,
    autopilot_routes,
    chronicles,
    snapshot_routes,
    workbench_context_routes,
    character_scheduler_routes,
    vector_store_routes,
)

# Audit module
from interfaces.api.v1.audit import chapter_review_routes, macro_refactor, chapter_element_routes

# Analyst module
from interfaces.api.v1.analyst import voice, narrative_state, foreshadow_ledger

# Workbench module
from interfaces.api.v1.workbench import sandbox, writer_block, monitor, llm_control
from interfaces.api.stats.routers.stats import create_stats_router
from interfaces.api.stats.services.stats_service import StatsService
from interfaces.api.stats.repositories.sqlite_stats_repository_adapter import SqliteStatsRepositoryAdapter
from infrastructure.persistence.database.connection import get_database


def register_all_routers(app: FastAPI) -> None:
    """注册所有 API 路由到 FastAPI 应用。"""
    # Core module routes
    app.include_router(novels.router, prefix="/api/v1")
    app.include_router(chapters.router, prefix="/api/v1/novels")
    app.include_router(scene_generation_routes.router)
    app.include_router(llm_settings.router, prefix="/api/v1")
    app.include_router(llm_settings.embedding_router, prefix="/api/v1")
    app.include_router(export.router, prefix="/api/v1")

    # World module routes
    app.include_router(bible.router, prefix="/api/v1")
    app.include_router(cast.router, prefix="/api/v1")
    app.include_router(knowledge.router, prefix="/api/v1")
    app.include_router(knowledge_graph_routes.router)
    app.include_router(worldbuilding_routes.router)

    # Blueprint module routes
    app.include_router(continuous_planning_routes.router)
    app.include_router(beat_sheet_routes.router)
    app.include_router(story_structure.router, prefix="/api/v1")

    # Engine module routes
    app.include_router(generation.router, prefix="/api/v1")
    app.include_router(context_intelligence.router, prefix="/api/v1")
    app.include_router(chronicles.router, prefix="/api/v1")
    app.include_router(snapshot_routes.router, prefix="/api/v1")
    app.include_router(autopilot_routes.router, prefix="/api/v1")
    app.include_router(workbench_context_routes.router, prefix="/api/v1")
    app.include_router(character_scheduler_routes.router, prefix="/api/v1")
    app.include_router(vector_store_routes.router, prefix="/api/v1")

    # Audit module routes
    app.include_router(chapter_review_routes.router)
    app.include_router(macro_refactor.router, prefix="/api/v1")
    app.include_router(chapter_element_routes.router)

    # Analyst module routes
    app.include_router(voice.router, prefix="/api/v1")
    app.include_router(narrative_state.router, prefix="/api/v1")
    app.include_router(foreshadow_ledger.router, prefix="/api/v1")

    # Workbench module routes
    app.include_router(writer_block.router, prefix="/api/v1")
    app.include_router(sandbox.router, prefix="/api/v1")
    app.include_router(monitor.router, prefix="/api/v1")
    app.include_router(llm_control.router, prefix="/api/v1")

    # 统计路由
    stats_repository = SqliteStatsRepositoryAdapter(get_database())
    stats_service = StatsService(stats_repository)
    stats_router = create_stats_router(stats_service)
    app.include_router(stats_router, prefix="/api/stats", tags=["statistics"])
