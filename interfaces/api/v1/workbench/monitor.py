"""监控大盘 API endpoints - 提供张力曲线、人声漂移、伏笔统计等监控数据"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from domain.novel.value_objects.novel_id import NovelId
from interfaces.api.dependencies import (
    get_novel_repository,
    get_chapter_repository,
    get_foreshadowing_repository,
    get_voice_drift_service,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/novels", tags=["monitor"])


class TensionPoint(BaseModel):
    chapter: int
    tension: float
    title: str


class TensionCurveResponse(BaseModel):
    novel_id: str
    points: List[TensionPoint]


class VoiceDriftResponse(BaseModel):
    character_id: str
    character_name: str
    drift_score: float
    status: str  # "normal" | "warning" | "critical"
    sample_count: int


class ForeshadowStatsResponse(BaseModel):
    total_planted: int
    total_resolved: int
    pending: int
    forgotten_risk: int
    resolution_rate: float


@router.get("/{novel_id}/monitor/tension-curve", response_model=TensionCurveResponse)
async def get_tension_curve(novel_id: str):
    """
    获取章节张力曲线数据

    返回每章的张力值（0-10），用于绘制张力曲线图
    """
    try:
        chapter_repo = get_chapter_repository()
        chapters = chapter_repo.list_by_novel(NovelId(novel_id))

        points = []
        for ch in chapters:
            # 从章节元数据中获取张力值（0-100），转换为 0-10 范围
            # 注意：不能用 `or 50`，否则合法值 0 会被当成「缺省」误判为 5.0
            raw = getattr(ch, "tension_score", None)
            if raw is None:
                raw_tension = 50.0
            else:
                raw_tension = float(raw)
            tension = raw_tension / 10.0
            points.append(TensionPoint(
                chapter=ch.number,
                tension=tension,
                title=ch.title or f"第{ch.number}章"
            ))

        # 按章节号排序
        points.sort(key=lambda p: p.chapter)

        return TensionCurveResponse(
            novel_id=novel_id,
            points=points
        )

    except Exception as e:
        logger.error(f"Error fetching tension curve: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch tension curve")


@router.get("/{novel_id}/monitor/voice-drift", response_model=List[VoiceDriftResponse])
async def get_voice_drift(novel_id: str):
    """
    获取人声漂移检测数据

    返回最近章节的文风漂移指数（0-1），超过 0.3 为异常。
    当前按章节粒度返回（数据库模型暂不支持按角色细分）。
    """
    try:
        novel_repo = get_novel_repository()
        novel = novel_repo.get_by_id(NovelId(novel_id))

        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")

        voice_drift_service = get_voice_drift_service()
        report = voice_drift_service.get_drift_report(novel_id)
        scores = report.get("scores", [])

        results = []
        # 取最近 10 个章节的评分
        for score in scores[-10:]:
            similarity = score.get("similarity_score", 1.0)
            # drift = 1 - similarity（similarity 越低，drift 越高）
            drift_score = max(0.0, min(1.0, 1.0 - similarity))
            status = "normal"
            if drift_score > 0.5:
                status = "critical"
            elif drift_score > 0.3:
                status = "warning"

            chapter_num = score.get("chapter_number", 0)
            results.append(VoiceDriftResponse(
                character_id=f"chapter_{chapter_num}",
                character_name=f"第{chapter_num}章",
                drift_score=round(drift_score, 3),
                status=status,
                sample_count=score.get("sentence_count", 0),
            ))

        # 无数据时回退到空列表（前端可处理）
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching voice drift: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch voice drift data")


@router.get("/{novel_id}/monitor/foreshadow-stats", response_model=ForeshadowStatsResponse)
async def get_foreshadow_stats(novel_id: str):
    """
    获取伏笔统计数据

    返回已埋伏笔、已回收、待回收、遗忘风险等统计信息
    """
    try:
        foreshadowing_repo = get_foreshadowing_repository()
        chapter_repo = get_chapter_repository()

        # 获取伏笔注册表
        registry = foreshadowing_repo.get_by_novel_id(NovelId(novel_id))
        if not registry:
            # 如果没有伏笔数据，返回空统计
            return ForeshadowStatsResponse(
                total_planted=0,
                total_resolved=0,
                pending=0,
                forgotten_risk=0,
                resolution_rate=0.0
            )

        # 获取所有潜台词条目（伏笔）
        entries = registry.subtext_entries

        total_planted = len(entries)
        total_resolved = sum(1 for e in entries if e.status == "consumed")
        pending = total_planted - total_resolved

        # 获取当前最新章节号
        chapters = chapter_repo.list_by_novel(NovelId(novel_id))
        current_chapter = max((ch.number for ch in chapters), default=0)

        # 计算遗忘风险：超过10章未回收的伏笔
        forgotten_risk = 0
        for entry in entries:
            if entry.status == "pending":
                planted_chapter = entry.chapter
                if current_chapter - planted_chapter > 10:
                    forgotten_risk += 1

        resolution_rate = (total_resolved / total_planted * 100) if total_planted > 0 else 0.0

        return ForeshadowStatsResponse(
            total_planted=total_planted,
            total_resolved=total_resolved,
            pending=pending,
            forgotten_risk=forgotten_risk,
            resolution_rate=round(resolution_rate, 1)
        )

    except Exception as e:
        logger.error(f"Error fetching foreshadow stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch foreshadow statistics")
