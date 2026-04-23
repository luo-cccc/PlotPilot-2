"""小说域仓储接口聚合

合并原单个接口文件到统一入口。
"""

from abc import ABC, abstractmethod
from domain.novel.entities.beat_sheet import BeatSheet
from domain.novel.entities.chapter import Chapter
from domain.novel.entities.foreshadowing_registry import ForeshadowingRegistry
from domain.novel.entities.novel import Novel, AutopilotStatus
from domain.novel.entities.plot_arc import PlotArc
from domain.novel.entities.storyline import Storyline
from domain.novel.entities.timeline_registry import TimelineRegistry
from domain.novel.value_objects.chapter_id import ChapterId
from domain.novel.value_objects.novel_id import NovelId
from typing import List, Optional

class BeatSheetRepository(ABC):
    """节拍表仓储接口"""

    @abstractmethod
    async def save(self, beat_sheet: BeatSheet) -> None:
        """保存节拍表"""
        pass

    @abstractmethod
    async def get_by_chapter_id(self, chapter_id: str) -> Optional[BeatSheet]:
        """根据章节 ID 获取节拍表"""
        pass

    @abstractmethod
    async def delete_by_chapter_id(self, chapter_id: str) -> None:
        """删除章节的节拍表"""
        pass

    @abstractmethod
    async def exists(self, chapter_id: str) -> bool:
        """检查章节是否已有节拍表"""
        pass


class ChapterRepository(ABC):
    """章节仓储接口"""

    @abstractmethod
    def save(self, chapter: Chapter) -> None:
        """保存章节"""
        pass

    @abstractmethod
    def get_by_id(self, chapter_id: ChapterId) -> Optional[Chapter]:
        """根据 ID 获取章节"""
        pass

    @abstractmethod
    def list_by_novel(self, novel_id: NovelId) -> List[Chapter]:
        """
        列出小说的所有章节

        返回的章节列表按章节序号升序排序
        """
        pass

    @abstractmethod
    def get_by_novel_and_numbers(self, novel_id: NovelId, numbers: List[int]) -> List[Chapter]:
        """根据小说 ID 和章节号列表批量获取章节"""
        pass

    @abstractmethod
    def exists(self, chapter_id: ChapterId) -> bool:
        """检查章节是否存在"""
        pass

    @abstractmethod
    def delete(self, chapter_id: ChapterId) -> None:
        """
        删除章节

        如果章节不存在，此操作不会引发错误
        """
        pass


class EntityBaseRepository(ABC):
    """实体基座仓储抽象接口"""

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[dict]:
        """根据 ID 获取实体基座

        Args:
            entity_id: 实体 ID

        Returns:
            实体字典，包含: id, novel_id, entity_type, name, core_attributes, created_at
            如果不存在返回 None
        """
        pass

    @abstractmethod
    def create(
        self,
        novel_id: str,
        entity_type: str,
        name: str,
        core_attributes: dict
    ) -> str:
        """创建新实体基座

        Args:
            novel_id: 小说 ID
            entity_type: 实体类型
            name: 实体名称
            core_attributes: 核心属性字典

        Returns:
            新创建的实体 ID
        """
        pass


class ForeshadowingRepository(ABC):
    """伏笔注册表仓储接口"""

    @abstractmethod
    def save(self, registry: ForeshadowingRegistry) -> None:
        """保存伏笔注册表"""
        pass

    @abstractmethod
    def get_by_novel_id(self, novel_id: NovelId) -> Optional[ForeshadowingRegistry]:
        """根据小说 ID 获取伏笔注册表"""
        pass

    @abstractmethod
    def delete(self, novel_id: NovelId) -> None:
        """删除伏笔注册表"""
        pass


class NarrativeEventRepository(ABC):
    """叙事事件仓储抽象接口"""

    @abstractmethod
    def list_up_to_chapter(self, novel_id: str, max_chapter_inclusive: int) -> list[dict]:
        """获取指定章节及之前的所有事件

        Args:
            novel_id: 小说 ID
            max_chapter_inclusive: 最大章节号（包含）

        Returns:
            事件列表，按 chapter_number ASC 排序
            每个事件包含: event_id, novel_id, chapter_number, event_summary, mutations, timestamp_ts
        """
        pass

    @abstractmethod
    def append_event(
        self,
        novel_id: str,
        chapter_number: int,
        event_summary: str,
        mutations: list[dict],
        tags: list[str] = None
    ) -> str:
        """追加新事件

        Args:
            novel_id: 小说 ID
            chapter_number: 章节号
            event_summary: 事件摘要
            mutations: 变更列表
            tags: 事件标签列表（可选，默认空列表）

        Returns:
            新创建的 event_id
        """
        pass

    @abstractmethod
    def get_event(self, novel_id: str, event_id: str) -> Optional[dict]:
        """获取单个事件

        Args:
            novel_id: 小说 ID
            event_id: 事件 ID

        Returns:
            事件字典，如果不存在返回 None
        """
        pass

    @abstractmethod
    def update_event(
        self,
        novel_id: str,
        event_id: str,
        event_summary: str,
        tags: list[str]
    ) -> None:
        """更新事件

        Args:
            novel_id: 小说 ID
            event_id: 事件 ID
            event_summary: 新的事件摘要
            tags: 新的标签列表
        """
        pass


class NovelRepository(ABC):
    """小说仓储接口"""

    @abstractmethod
    def save(self, novel: Novel) -> None:
        """保存小说"""
        pass

    @abstractmethod
    async def async_save(self, novel: Novel) -> None:
        """异步保存小说（守护进程使用）"""
        pass

    @abstractmethod
    def get_by_id(self, novel_id: NovelId) -> Optional[Novel]:
        """根据 ID 获取小说"""
        pass

    @abstractmethod
    def list_all(self) -> List[Novel]:
        """列出所有小说"""
        pass

    @abstractmethod
    def find_by_autopilot_status(self, status: AutopilotStatus) -> List[Novel]:
        """根据自动驾驶状态查询小说（守护进程使用）"""
        pass

    @abstractmethod
    def delete(self, novel_id: NovelId) -> None:
        """删除小说"""
        pass

    @abstractmethod
    def exists(self, novel_id: NovelId) -> bool:
        """检查小说是否存在"""
        pass


class PlotArcRepository(ABC):
    """剧情弧仓储接口"""

    @abstractmethod
    def save(self, plot_arc: PlotArc) -> None:
        """保存剧情弧"""
        pass

    @abstractmethod
    def get_by_novel_id(self, novel_id: NovelId) -> Optional[PlotArc]:
        """根据小说 ID 获取剧情弧"""
        pass

    @abstractmethod
    def delete(self, novel_id: NovelId) -> None:
        """删除剧情弧"""
        pass


class StorylineRepository(ABC):
    """故事线仓储接口"""

    @abstractmethod
    def save(self, storyline: Storyline) -> None:
        """保存故事线"""
        pass

    @abstractmethod
    def get_by_id(self, storyline_id: str) -> Optional[Storyline]:
        """根据 ID 获取故事线"""
        pass

    @abstractmethod
    def get_by_novel_id(self, novel_id: NovelId) -> List[Storyline]:
        """根据小说 ID 获取所有故事线"""
        pass

    @abstractmethod
    def delete(self, storyline_id: str) -> None:
        """删除故事线"""
        pass


class TimelineRepository(ABC):
    """时间线仓储接口"""

    @abstractmethod
    def save(self, registry: TimelineRegistry) -> None:
        """保存时间线注册表"""
        pass

    @abstractmethod
    def get_by_novel_id(self, novel_id: NovelId) -> Optional[TimelineRegistry]:
        """根据小说ID获取时间线注册表"""
        pass

    @abstractmethod
    def delete(self, novel_id: NovelId) -> None:
        """删除时间线注册表"""
        pass


class VoiceFingerprintRepository(ABC):
    """Repository for voice fingerprint data."""

    @abstractmethod
    def get_by_novel(
        self, novel_id: str, pov_character_id: Optional[str] = None
    ) -> Optional[dict]:
        """Get fingerprint by novel ID and optional POV character.

        Args:
            novel_id: Novel identifier
            pov_character_id: Optional POV character identifier

        Returns:
            Fingerprint data dict or None if not found
        """
        pass

    @abstractmethod
    def upsert(
        self,
        novel_id: str,
        fingerprint_data: dict,
        pov_character_id: Optional[str] = None,
    ) -> str:
        """Insert or update fingerprint data.

        Args:
            novel_id: Novel identifier
            fingerprint_data: Fingerprint metrics
            pov_character_id: Optional POV character identifier

        Returns:
            Fingerprint ID (UUID)
        """
        pass


class VoiceVaultRepository(ABC):
    """文风金库仓储接口"""

    @abstractmethod
    def append_sample(
        self,
        novel_id: str,
        chapter_number: int,
        scene_type: Optional[str],
        ai_original: str,
        author_refined: str,
        diff_analysis: str
    ) -> str:
        """
        添加文风样本

        Args:
            novel_id: 小说 ID
            chapter_number: 章节号
            scene_type: 场景类型（可选）
            ai_original: AI 原文
            author_refined: 作者改稿
            diff_analysis: 差异分析（JSON 字符串）

        Returns:
            sample_id: 样本 ID
        """
        pass

    @abstractmethod
    def list_samples(self, novel_id: str, limit: Optional[int] = None) -> List[dict]:
        """
        列出小说的文风样本

        Args:
            novel_id: 小说 ID
            limit: 限制返回数量（可选）

        Returns:
            样本列表
        """
        pass

    @abstractmethod
    def get_sample_count(self, novel_id: str) -> int:
        """
        获取小说的样本数量

        Args:
            novel_id: 小说 ID

        Returns:
            样本数量
        """
        pass

    @abstractmethod
    def get_by_novel(
        self, novel_id: str, pov_character_id: Optional[str] = None
    ) -> List[dict]:
        """
        获取小说的所有样本（用于指纹计算）

        Args:
            novel_id: 小说 ID
            pov_character_id: 可选的 POV 角色 ID

        Returns:
            样本列表，每个样本包含 content 字段
        """
        pass
