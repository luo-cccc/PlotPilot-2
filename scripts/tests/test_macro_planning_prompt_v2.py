"""
测试宏观规划提示词 V2 效果

运行方式:
    cd d:/CODE/aitext
    python scripts/tests/test_macro_planning_prompt_v2.py

此测试用于验证优化后的提示词效果，输出质量指标供持续优化参考。
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from application.blueprint.services.continuous_planning_service import ContinuousPlanningService
from domain.ai.services.llm_service import LLMService
from domain.ai.value_objects.prompt import Prompt


class MockLLMService:
    """模拟 LLM 服务，用于测试提示词结构"""

    def __init__(self):
        self.last_prompt = None

    async def generate(self, prompt: Prompt, config=None):
        self.last_prompt = prompt
        # 返回模拟响应
        return json.dumps({
            "parts": [
                {
                    "title": "测试部",
                    "volumes": [
                        {
                            "title": "测试卷",
                            "acts": [
                                {
                                    "title": "血染青铜门",
                                    "core_conflict": "主角 vs 反派，赌注是世界",
                                    "emotional_turn": "从希望到绝望",
                                    "description": "测试描述",
                                    "key_characters": ["主角", "反派"],
                                    "key_locations": ["青铜门"]
                                }
                            ]
                        }
                    ]
                }
            ]
        })


def test_quick_mode_prompt():
    """测试极速模式提示词 V2"""
    print("=" * 60)
    print("测试极速模式提示词 V2 (破城槌)")
    print("=" * 60)

    service = ContinuousPlanningService(
        story_node_repo=None,
        chapter_element_repo=None,
        llm_service=MockLLMService(),
        bible_service=None
    )

    # 模拟 Bible 上下文
    bible_context = {
        "worldview": "赛博朋克世界，高科技低生活，巨型企业控制一切",
        "characters": [
            {"name": "李明", "description": "底层黑客，渴望改变命运", "role": "主角", "id": "char-1"},
            {"name": " corporate_exec", "description": "企业高管，冷酷无情", "role": "反派", "id": "char-2"}
        ],
        "relationships": [
            {"character1": "李明", "character2": "corporate_exec", "relationship_type": "敌对", "description": "阶级对立"}
        ],
        "locations": [
            {"name": "霓虹贫民窟", "description": "底层人民居住地", "significance": "主角起点", "id": "loc-1"},
            {"name": "企业塔", "description": "权力中心", "significance": "终极对决地", "id": "loc-2"}
        ],
        "timeline_notes": [
            {"event": "大崩溃", "description": "旧世界秩序崩塌", "impact": "企业崛起"}
        ]
    }

    prompt = service._build_quick_macro_prompt(bible_context, target_chapters=100)

    print("\n【System Prompt 预览】(前 800 字符):")
    print("-" * 60)
    print(prompt.system[:800] + "..." if len(prompt.system) > 800 else prompt.system)

    print("\n【User Prompt 预览】(前 800 字符):")
    print("-" * 60)
    print(prompt.user[:800] + "..." if len(prompt.user) > 800 else prompt.user)

    print("\n【提示词统计】:")
    print(f"  System 长度: {len(prompt.system)} 字符")
    print(f"  User 长度: {len(prompt.user)} 字符")
    print(f"  总长度: {len(prompt.system) + len(prompt.user)} 字符")

    return prompt


def test_precise_mode_prompt():
    """测试精密模式提示词 V2"""
    print("\n" + "=" * 60)
    print("测试精密模式提示词 V2 (手术刀)")
    print("=" * 60)

    service = ContinuousPlanningService(
        story_node_repo=None,
        chapter_element_repo=None,
        llm_service=MockLLMService(),
        bible_service=None
    )

    bible_context = {
        "worldview": "修仙世界，灵气复苏，宗门林立",
        "characters": [
            {"name": "林凡", "description": "废柴少年，获得神秘传承", "role": "主角", "id": "char-1"},
            {"name": "萧长老", "description": "宗门长老，表面慈祥实则阴险", "role": "反派", "id": "char-2"}
        ],
        "locations": [
            {"name": "青云宗", "description": "九品宗门", "significance": "起点", "id": "loc-1"}
        ]
    }

    structure_preference = {
        "parts": 3,
        "volumes_per_part": 3,
        "acts_per_volume": 3
    }

    prompt = service._build_precise_macro_prompt(bible_context, target_chapters=300, structure_preference=structure_preference)

    print("\n【System Prompt 预览】(前 800 字符):")
    print("-" * 60)
    print(prompt.system[:800] + "..." if len(prompt.system) > 800 else prompt.system)

    print("\n【User Prompt 预览】(前 800 字符):")
    print("-" * 60)
    print(prompt.user[:800] + "..." if len(prompt.user) > 800 else prompt.user)

    print("\n【提示词统计】:")
    print(f"  System 长度: {len(prompt.system)} 字符")
    print(f"  User 长度: {len(prompt.user)} 字符")
    print(f"  总长度: {len(prompt.system) + len(prompt.user)} 字符")

    return prompt


def test_quality_evaluation():
    """测试质量评估功能"""
    print("\n" + "=" * 60)
    print("测试质量评估功能")
    print("=" * 60)

    service = ContinuousPlanningService(
        story_node_repo=None,
        chapter_element_repo=None,
        llm_service=MockLLMService(),
        bible_service=None
    )

    # 模拟结构数据
    structure = {
        "parts": [
            {
                "title": "起源",
                "volumes": [
                    {
                        "title": "觉醒",
                        "acts": [
                            {
                                "title": "血染青铜门",
                                "core_conflict": "李明 vs 财阀执法队，赌注是妹妹的机械心脏",
                                "emotional_turn": "从希望到绝望",
                                "description": "李明在贫民窟发现妹妹的机械心脏即将到期",
                                "key_characters": ["李明", "执法队长"],
                                "key_locations": ["贫民窟"]
                            },
                            {
                                "title": "霓虹下的交易",
                                "core_conflict": "李明 vs 黑市商人，赌注是信任",
                                "emotional_turn": "从绝望到一线希望",
                                "description": "李明冒险进入黑市寻找替代心脏",
                                "key_characters": ["李明", "黑市商人"],
                                "key_locations": ["黑市"]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    bible_context = {
        "characters": [
            {"name": "李明", "id": "char-1"},
            {"name": "黑市商人", "id": "char-2"}
        ],
        "locations": [
            {"name": "贫民窟", "id": "loc-1"},
            {"name": "黑市", "id": "loc-2"}
        ]
    }

    metrics = service._evaluate_macro_plan_quality(
        structure=structure,
        bible_context=bible_context,
        target_chapters=100,
        structure_preference=None
    )

    print("\n【质量评估结果】:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))

    return metrics


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("宏观规划提示词 V2 测试")
    print("=" * 60)

    # 测试极速模式
    test_quick_mode_prompt()

    # 测试精密模式
    test_precise_mode_prompt()

    # 测试质量评估
    test_quality_evaluation()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n提示词优化要点:")
    print("1. 极速模式: 结构自主决定 + 世界观深度融合 + 情绪曲线")
    print("2. 精密模式: 叙事理论框架 + 逻辑严密性 + 伏笔呼应")
    print("3. 质量评估: 冲突密度 + 世界观融合度 + 标题质量")


if __name__ == "__main__":
    asyncio.run(main())
