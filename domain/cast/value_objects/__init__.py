"""Cast 领域值对象（聚合文件）

本模块合并了原先分散在 domain/cast/value_objects/ 目录下的值对象。
各子模块保留为兼容包装器，可逐步迁移到直接从本包导入。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterId:
    """Character ID value object"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Character ID cannot be empty")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RelationshipId:
    """Relationship ID value object"""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("Relationship ID cannot be empty")

    def __str__(self) -> str:
        return self.value


__all__ = ["CharacterId", "RelationshipId"]
