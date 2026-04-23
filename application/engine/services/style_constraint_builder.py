"""Style constraint builder for voice fingerprint integration."""
import re
from typing import Optional


def build_style_summary(fingerprint: Optional[dict]) -> str:
    """Build a concise style summary from voice fingerprint data.

    Args:
        fingerprint: Voice fingerprint dict with 'metrics' field containing:
            - adjective_density: float (0.0-1.0)
            - avg_sentence_length: float
            - sentence_count: int
            - dialogue_ratio: float (0.0-1.0) — optional
            - paragraph_length_std: float — optional

    Returns:
        Concise bullet-point summary (≤1K tokens) for LLM prompt injection.
        Empty string if fingerprint is None or invalid.
    """
    if not fingerprint:
        return ""

    metrics = fingerprint.get("metrics")
    if not metrics:
        return ""

    adjective_density = metrics.get("adjective_density", 0.0)
    avg_sentence_length = metrics.get("avg_sentence_length", 0.0)
    dialogue_ratio = metrics.get("dialogue_ratio", 0.0)
    paragraph_length_std = metrics.get("paragraph_length_std", 0.0)

    summary_parts = []

    # Adjective density guidance
    if adjective_density > 0:
        density_pct = adjective_density * 100
        if density_pct < 3.0:
            summary_parts.append(f"- 形容词密度：{density_pct:.1f}%（保持简洁，少用修饰）")
        elif density_pct < 6.0:
            summary_parts.append(f"- 形容词密度：{density_pct:.1f}%（适度修饰，平衡叙事）")
        else:
            summary_parts.append(f"- 形容词密度：{density_pct:.1f}%（丰富描写，注重细节）")

    # Sentence length guidance
    if avg_sentence_length > 0:
        if avg_sentence_length < 15:
            summary_parts.append(f"- 平均句长：{avg_sentence_length:.0f}字（保持短句，节奏明快）")
        elif avg_sentence_length < 25:
            summary_parts.append(f"- 平均句长：{avg_sentence_length:.0f}字（长短结合，节奏适中）")
        else:
            summary_parts.append(f"- 平均句长：{avg_sentence_length:.0f}字（偏好长句，舒缓叙事）")

    # Dialogue ratio guidance
    if dialogue_ratio > 0:
        if dialogue_ratio < 0.15:
            summary_parts.append(f"- 对话占比：{dialogue_ratio:.0%}（以叙述为主，少量对白）")
        elif dialogue_ratio < 0.35:
            summary_parts.append(f"- 对话占比：{dialogue_ratio:.0%}（叙白均衡）")
        else:
            summary_parts.append(f"- 对话占比：{dialogue_ratio:.0%}（对话驱动，注重角色互动）")

    # Paragraph rhythm guidance
    if paragraph_length_std > 0:
        if paragraph_length_std < 30:
            summary_parts.append(f"- 段落节奏：均匀（段落长度变化小，平稳推进）")
        elif paragraph_length_std < 80:
            summary_parts.append(f"- 段落节奏：起伏适中（长短段交替，张弛有度）")
        else:
            summary_parts.append(f"- 段落节奏：剧烈变化（短句急促与长段铺陈交替）")

    if not summary_parts:
        return ""

    return "\n".join(summary_parts)


def compute_extended_metrics(text: str) -> dict:
    """从章节文本计算扩展风格指标（含对话比例和段落长度标准差）。"""
    if not text:
        return {"dialogue_ratio": 0.0, "paragraph_length_std": 0.0}

    # 对话比例：引号内文本 / 总文本
    dialogue_chars = 0
    _DIALOGUE_RE = re.compile(r"[“”「『][^“”」』]*[“”」』]", re.DOTALL)
    for m in _DIALOGUE_RE.finditer(text):
        dialogue_chars += len(m.group())
    dialogue_ratio = dialogue_chars / len(text) if text else 0.0

    # 段落长度标准差
    paragraphs = [p for p in text.split("\n") if p.strip()]
    if len(paragraphs) >= 2:
        lengths = [len(p) for p in paragraphs]
        mean_len = sum(lengths) / len(lengths)
        variance = sum((l - mean_len) ** 2 for l in lengths) / len(lengths)
        paragraph_length_std = variance ** 0.5
    else:
        paragraph_length_std = 0.0

    return {"dialogue_ratio": round(dialogue_ratio, 3), "paragraph_length_std": round(paragraph_length_std, 1)}
