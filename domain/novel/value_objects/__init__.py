"""Novel 领域值对象（聚合文件）

本模块合并了原先分散在 domain/novel/value_objects/ 目录下的所有值对象，
以减少碎片化文件数量。各子模块保留为兼容包装器，可逐步迁移到直接从本包导入。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from domain.bible.entities.bible import Bible
    from domain.bible.entities.character_registry import CharacterRegistry
    from domain.novel.entities.foreshadowing_registry import ForeshadowingRegistry
    from domain.novel.entities.plot_arc import PlotArc
    from domain.bible.value_objects.relationship_graph import RelationshipGraph

# -- 枚举（无包内依赖）--


class TensionLevel(int, Enum):
    """张力等级"""
    LOW = 1      # 平缓
    MEDIUM = 2   # 中等
    HIGH = 3     # 紧张
    PEAK = 4     # 极度紧张


class EventType(str, Enum):
    """事件类型枚举"""
    CHARACTER_INTRODUCTION = "character_introduction"  # 角色介绍
    RELATIONSHIP_CHANGE = "relationship_change"        # 关系变化
    CONFLICT = "conflict"                              # 冲突
    REVELATION = "revelation"                          # 揭示
    DECISION = "decision"                              # 决定


class ForeshadowingStatus(str, Enum):
    """伏笔状态"""
    PLANTED = "planted"      # 已埋下
    RESOLVED = "resolved"    # 已解决
    ABANDONED = "abandoned"  # 已放弃


class ImportanceLevel(int, Enum):
    """重要性级别"""
    LOW = 1        # 低
    MEDIUM = 2     # 中等
    HIGH = 3       # 高
    CRITICAL = 4   # 关键


class PlotPointType(str, Enum):
    """剧情点类型"""
    OPENING = "opening"              # 开端
    RISING_ACTION = "rising"         # 上升
    TURNING_POINT = "turning"        # 转折
    CLIMAX = "climax"                # 高潮
    FALLING_ACTION = "falling"       # 下降
    RESOLUTION = "resolution"        # 结局


class StorylineType(Enum):
    """故事线类型枚举"""
    MAIN_PLOT = "main_plot"
    ROMANCE = "romance"
    REVENGE = "revenge"
    MYSTERY = "mystery"
    GROWTH = "growth"
    POLITICAL = "political"
    ADVENTURE = "adventure"
    FAMILY = "family"
    FRIENDSHIP = "friendship"


class StorylineStatus(Enum):
    """故事线状态枚举"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class IssueType(str, Enum):
    """一致性问题类型"""
    CHARACTER_INCONSISTENCY = "character_inconsistency"
    RELATIONSHIP_INCONSISTENCY = "relationship_inconsistency"
    EVENT_LOGIC_ERROR = "event_logic_error"
    FORESHADOWING_ERROR = "foreshadowing_error"
    TIMELINE_ERROR = "timeline_error"


class Severity(str, Enum):
    """问题严重性级别"""
    CRITICAL = "critical"
    IMPORTANT = "important"
    MINOR = "minor"


# -- 简单数据类 --


@dataclass(frozen=True)
class ChapterId:
    """章节 ID 值对象"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Chapter ID cannot be empty")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ChapterId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class NovelId:
    """小说 ID 值对象"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Novel ID cannot be empty")

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NovelId):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class WordCount:
    """字数值对象"""
    value: int

    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Word count cannot be negative")

    def __add__(self, other: "WordCount") -> "WordCount":
        return WordCount(self.value + other.value)

    def __lt__(self, other: "WordCount") -> bool:
        return self.value < other.value

    def __le__(self, other: "WordCount") -> bool:
        return self.value <= other.value

    def __gt__(self, other: "WordCount") -> bool:
        return self.value > other.value

    def __ge__(self, other: "WordCount") -> bool:
        return self.value >= other.value

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, WordCount):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __str__(self) -> str:
        return f"{self.value}"


@dataclass(frozen=True)
class ChapterContent:
    """章节内容值对象"""
    raw_text: str

    def __post_init__(self):
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError("Chapter content cannot be None or empty")

    def word_count(self) -> int:
        """计算字数（简单实现）"""
        return len(self.raw_text)

    def __str__(self) -> str:
        preview_length = 50
        if len(self.raw_text) <= preview_length:
            return self.raw_text
        return f"{self.raw_text[:preview_length]}..."


@dataclass(frozen=True)
class TimelineEvent:
    """时间线事件"""
    id: str
    chapter_number: int
    event: str  # 事件描述
    timestamp: str  # 时间戳（如"第三年春"、"2024-03-15"、"午夜"）
    timestamp_type: str  # 时间类型：absolute/relative/vague

    def __post_init__(self):
        if self.chapter_number < 1:
            raise ValueError("chapter_number must be >= 1")
        if not self.event or not self.event.strip():
            raise ValueError("event cannot be empty")
        if not self.timestamp or not self.timestamp.strip():
            raise ValueError("timestamp cannot be empty")
        if self.timestamp_type not in ("absolute", "relative", "vague"):
            raise ValueError("timestamp_type must be one of: absolute, relative, vague")


@dataclass(frozen=True)
class Scene:
    """场景值对象（章节的基本组成单元，用于节拍表）"""
    title: str  # 场景标题
    goal: str  # 场景目标
    pov_character: str  # POV 角色名称
    location: Optional[str]  # 地点
    tone: Optional[str]  # 情绪基调
    estimated_words: int  # 预估字数
    order_index: int  # 场景顺序

    def __post_init__(self):
        if not self.title:
            raise ValueError("Scene title cannot be empty")
        if not self.goal:
            raise ValueError("Scene goal cannot be empty")
        if not self.pov_character:
            raise ValueError("Scene POV character cannot be empty")
        if self.estimated_words <= 0:
            raise ValueError("Estimated words must be positive")
        if self.order_index < 0:
            raise ValueError("Order index must be non-negative")


@dataclass(frozen=True)
class ChapterRenumberSpec:
    """删章并重排序号后，各层「章号引用」的统一变换规则。"""
    novel_id: str
    deleted_chapter_number: int

    def shift_chapter_ref(self, chapter_number: int) -> int:
        """将「仍指向旧编号体系」的章号映射到删章后的新编号。"""
        d = self.deleted_chapter_number
        n = int(chapter_number)
        if n > d:
            return n - 1
        if n == d:
            return max(1, d - 1)
        return n

    def shift_optional_chapter_ref(self, chapter_number: Optional[int]) -> Optional[int]:
        if chapter_number is None:
            return None
        return self.shift_chapter_ref(chapter_number)


@dataclass(frozen=True)
class TensionDimensions:
    """多维张力分析结果（所有分值范围 0-100）"""
    plot_tension: float
    emotional_tension: float
    pacing_tension: float
    composite_score: float

    _WEIGHTS = (0.40, 0.30, 0.30)

    def __post_init__(self) -> None:
        for name in (
            "plot_tension",
            "emotional_tension",
            "pacing_tension",
            "composite_score",
        ):
            val = getattr(self, name)
            if not isinstance(val, (int, float)):
                raise TypeError(f"{name} must be numeric, got {type(val).__name__}")
            if not (0.0 <= float(val) <= 100.0):
                raise ValueError(f"{name} must be 0-100, got {val}")

    @classmethod
    def from_raw_scores(
        cls,
        plot: float,
        emotional: float,
        pacing: float,
    ) -> "TensionDimensions":
        """从三个维度原始分值构造实例，自动计算加权综合分。"""
        plot = max(0.0, min(100.0, float(plot)))
        emotional = max(0.0, min(100.0, float(emotional)))
        pacing = max(0.0, min(100.0, float(pacing)))
        composite = round(
            plot * cls._WEIGHTS[0]
            + emotional * cls._WEIGHTS[1]
            + pacing * cls._WEIGHTS[2],
            1,
        )
        return cls(
            plot_tension=plot,
            emotional_tension=emotional,
            pacing_tension=pacing,
            composite_score=composite,
        )

    @classmethod
    def neutral(cls) -> "TensionDimensions":
        """返回全维度 50.0 的中性结果（用于兜底）。"""
        return cls(50.0, 50.0, 50.0, 50.0)


# -- 中等数据类（依赖上方枚举） --


@dataclass(frozen=True)
class NovelEvent:
    """小说事件值对象"""
    chapter_number: int
    event_type: EventType
    description: str
    involved_characters: Tuple[Any, ...]  # CharacterId from domain.bible

    def __post_init__(self):
        if self.chapter_number < 1:
            raise ValueError("Chapter number must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")


@dataclass(frozen=True)
class Foreshadowing:
    """伏笔值对象"""
    id: str
    planted_in_chapter: int
    description: str
    importance: ImportanceLevel
    status: ForeshadowingStatus
    suggested_resolve_chapter: Optional[int] = None
    resolved_in_chapter: Optional[int] = None

    def __post_init__(self):
        if self.planted_in_chapter < 1:
            raise ValueError("planted_in_chapter must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")
        if self.status == ForeshadowingStatus.RESOLVED and self.resolved_in_chapter is None:
            raise ValueError("RESOLVED status requires resolved_in_chapter")
        if self.suggested_resolve_chapter is not None and self.suggested_resolve_chapter < 1:
            raise ValueError("suggested_resolve_chapter must be >= 1")
        if self.resolved_in_chapter is not None and self.resolved_in_chapter < 1:
            raise ValueError("resolved_in_chapter must be >= 1")
        if self.resolved_in_chapter is not None and self.resolved_in_chapter < self.planted_in_chapter:
            raise ValueError("resolved_in_chapter must be >= planted_in_chapter")
        if self.suggested_resolve_chapter is not None and self.suggested_resolve_chapter < self.planted_in_chapter:
            raise ValueError("suggested_resolve_chapter must be >= planted_in_chapter")


@dataclass(frozen=True)
class PlotPoint:
    """剧情点值对象"""
    chapter_number: int
    point_type: PlotPointType
    description: str
    tension: TensionLevel

    def __post_init__(self):
        if self.chapter_number < 1:
            raise ValueError("Chapter number must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("Description cannot be empty")


@dataclass(frozen=True)
class StorylineMilestone:
    """故事线里程碑值对象"""
    order: int
    title: str
    description: str
    target_chapter_start: int
    target_chapter_end: int
    prerequisites: List[str]
    triggers: List[str]

    def __post_init__(self):
        if self.order < 0:
            raise ValueError("Order must be non-negative")
        if self.target_chapter_start < 1 or self.target_chapter_end < 1:
            raise ValueError("Chapter numbers must be positive")
        if self.target_chapter_end < self.target_chapter_start:
            raise ValueError("target_chapter_end must be >= target_chapter_start")


@dataclass(frozen=True)
class Issue:
    """一致性问题值对象"""
    type: IssueType
    severity: Severity
    description: str
    location: int  # chapter_number

    def __post_init__(self):
        if self.location < 1:
            raise ValueError("location must be >= 1")
        if not self.description or not self.description.strip():
            raise ValueError("description cannot be empty")


@dataclass(frozen=True)
class ConsistencyReport:
    """一致性检查报告值对象"""
    issues: List[Issue]
    warnings: List[Issue]
    suggestions: List[str]

    def has_critical_issues(self) -> bool:
        """检查是否有严重问题"""
        return any(issue.severity == Severity.CRITICAL for issue in self.issues)

    def get_issues_by_type(self, issue_type: IssueType) -> List[Issue]:
        """按类型获取问题"""
        return [issue for issue in self.issues if issue.type == issue_type]

    def get_issues_by_severity(self, severity: Severity) -> List[Issue]:
        """按严重性获取问题"""
        return [issue for issue in self.issues if issue.severity == severity]


@dataclass(frozen=True)
class ChapterState:
    """章节状态值对象"""
    new_characters: List[Dict[str, Any]]
    character_actions: List[Dict[str, Any]]
    relationship_changes: List[Dict[str, Any]]
    foreshadowing_planted: List[Dict[str, Any]]
    foreshadowing_resolved: List[Dict[str, Any]]
    events: List[Dict[str, Any]]
    timeline_events: List[Dict[str, Any]] = field(default_factory=list)
    advanced_storylines: List[Dict[str, Any]] = field(default_factory=list)
    new_storylines: List[Dict[str, Any]] = field(default_factory=list)

    def has_new_characters(self) -> bool:
        return len(self.new_characters) > 0

    def has_relationship_changes(self) -> bool:
        return len(self.relationship_changes) > 0

    def has_foreshadowing_activity(self) -> bool:
        return len(self.foreshadowing_planted) > 0 or len(self.foreshadowing_resolved) > 0

    def has_timeline_events(self) -> bool:
        return len(self.timeline_events) > 0

    def has_storyline_activity(self) -> bool:
        return len(self.advanced_storylines) > 0 or len(self.new_storylines) > 0


# -- 复杂类（依赖上方数据类） --


class EventTimeline:
    """事件时间线"""

    def __init__(self):
        self._events: List[NovelEvent] = []

    @property
    def events(self) -> List[NovelEvent]:
        """返回事件列表的副本"""
        return self._events.copy()

    def add_event(self, event: NovelEvent) -> None:
        """添加事件并自动按章节号排序。"""
        if event is None:
            raise ValueError("Event cannot be None")
        self._events.append(event)
        self._events.sort(key=lambda e: e.chapter_number)

    def get_events_before(self, chapter_number: int) -> List[NovelEvent]:
        """获取指定章节之前的事件（不包括该章节）。"""
        if chapter_number < 1:
            raise ValueError("Chapter number must be >= 1")
        return [e for e in self._events if e.chapter_number < chapter_number]

    def get_events_involving(self, character_id: Any) -> List[NovelEvent]:
        """获取涉及特定角色的事件。"""
        return [e for e in self._events if character_id in e.involved_characters]


@dataclass(frozen=True)
class ConsistencyContext:
    """一致性检查上下文聚合器"""
    bible: "Bible"
    character_registry: "CharacterRegistry"
    foreshadowing_registry: "ForeshadowingRegistry"
    plot_arc: "PlotArc"
    event_timeline: EventTimeline
    relationship_graph: "RelationshipGraph"


__all__ = [
    "ChapterContent",
    "ChapterId",
    "ChapterRenumberSpec",
    "ChapterState",
    "ConsistencyContext",
    "ConsistencyReport",
    "EventTimeline",
    "EventType",
    "Foreshadowing",
    "ForeshadowingStatus",
    "ImportanceLevel",
    "Issue",
    "IssueType",
    "NovelEvent",
    "NovelId",
    "PlotPoint",
    "PlotPointType",
    "Scene",
    "Severity",
    "StorylineMilestone",
    "StorylineStatus",
    "StorylineType",
    "TensionDimensions",
    "TensionLevel",
    "TimelineEvent",
    "WordCount",
]
