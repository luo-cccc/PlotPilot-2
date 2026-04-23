"""安全字符串格式化工具

提供 SafeDict，用于模板变量替换时保留未定义的关键字。
"""


class SafeDict(dict):
    """在 format_map 中保留未定义的关键字，而非抛出 KeyError。"""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"
