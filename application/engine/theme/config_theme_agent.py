"""配置化 ThemeAgent — 从 JSON 配置加载题材能力

将 application/engine/theme/configs/{genre}.json 反序列化为 ThemeAgent 实例，
替代原先每个题材一个 Python 子类的模式。
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from application.engine.theme.theme_agent import (
    BeatTemplate,
    ThemeAgent,
    ThemeAuditCriteria,
    ThemeDirectives,
)

logger = logging.getLogger(__name__)


class ConfigThemeAgent(ThemeAgent):
    """从 dict/JSON 加载的 ThemeAgent 实现。

    所有数据驱动方法（人设、规则、节拍、审计等）均从配置字典读取，
    无需为每个题材编写 Python 子类。
    """

    def __init__(self, config: Dict[str, Any]):
        self._config = config

    @property
    def genre_key(self) -> str:
        return self._config["genre_key"]

    @property
    def genre_name(self) -> str:
        return self._config["genre_name"]

    @property
    def description(self) -> str:
        return self._config.get("description", "")

    def get_system_persona(self) -> str:
        return self._config.get("system_persona", "")

    def get_writing_rules(self) -> List[str]:
        return self._config.get("writing_rules", [])

    def get_context_directives(
        self,
        novel_id: str,
        chapter_number: int,
        outline: str,
    ) -> ThemeDirectives:
        directives = self._config.get("directives", {})
        return ThemeDirectives(
            world_rules=directives.get("world_rules", ""),
            atmosphere=directives.get("atmosphere", ""),
            taboos=directives.get("taboos", ""),
            tropes_to_use=directives.get("tropes_to_use", ""),
            tropes_to_avoid=directives.get("tropes_to_avoid", ""),
        )

    def get_beat_templates(self) -> List[BeatTemplate]:
        templates = self._config.get("beat_templates", [])
        result: List[BeatTemplate] = []
        for t in templates:
            beats = [tuple(b) for b in t.get("beats", [])]
            result.append(
                BeatTemplate(
                    keywords=t.get("keywords", []),
                    beats=beats,
                    priority=t.get("priority", 50),
                )
            )
        return result

    def get_custom_focus_instructions(self) -> Dict[str, str]:
        return self._config.get("custom_focus_instructions", {})

    def get_buffer_chapter_template(self, outline: str) -> str:
        template = self._config.get("buffer_chapter_template", "")
        if template and "{outline}" in template:
            return template.replace("{outline}", outline)
        return template

    def get_audit_criteria(
        self,
        chapter_number: int,
        outline: str,
    ) -> ThemeAuditCriteria:
        audit = self._config.get("audit_criteria", {})
        # 兼容 P7 提取的 JSON schema：
        # style_rules -> required_elements, consistency_checks -> quality_checks
        return ThemeAuditCriteria(
            required_elements=audit.get("style_rules", []),
            quality_checks=audit.get("consistency_checks", []),
            tension_guidance=audit.get("quality_thresholds", {}).get("tension_guidance", ""),
        )

    def get_opening_beats(self, chapter_number: int) -> Optional[List[tuple]]:
        opening = self._config.get("opening_beats", {})
        key = str(chapter_number)
        if key in opening:
            return [tuple(b) for b in opening[key]]
        return None

    @classmethod
    def from_json_file(cls, path: str) -> "ConfigThemeAgent":
        """从 JSON 文件路径加载。"""
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return cls(config)

    @classmethod
    def load_all_from_dir(cls, configs_dir: str) -> List["ConfigThemeAgent"]:
        """扫描目录下所有 *.json 文件并加载。"""
        agents: List[ConfigThemeAgent] = []
        p = Path(configs_dir)
        for json_file in sorted(p.glob("*.json")):
            try:
                agents.append(cls.from_json_file(str(json_file)))
            except Exception as e:
                logger.warning(f"加载题材配置失败 {json_file}: {e}")
        return agents
