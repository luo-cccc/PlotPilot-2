"""Fix chapter_review_service.py prompts"""
with open('chapter_review_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 1: character consistency
old = 'Prompt(system="你是小说审稿助手，专门检查人物一致性。", user=prompt_text)'
new = r'''Prompt(
            system=(
                "你是一位专业的小说审稿编辑，擅长检查人物一致性。\n\n"
                "输出要求：\n"
                "1. 严格遵循 JSON 格式输出，不要包含任何额外文字\n"
                "2. 返回 JSON 必须包含所有必需字段\n"
                "3. 如果没有发现问题，inconsistencies 返回空数组\n"
                "4. severity 只能是 critical/warning/suggestion 之一\n"
                "5. description 需具体说明问题所在位置和表现\n"
                "6. suggestion 应提供具体可操作的修改建议\n"
                "7. 不要臆测或编造人物行为，只基于提供的章节内容判断"
            ),
            user=prompt_text
        )'''
if old in content:
    content = content.replace(old, new)
    print("OK: character consistency")
else:
    print("FAIL: character consistency not found")

# Replace 2: timeline consistency
old = 'Prompt(system="你是小说审稿助手，专门检查时间线一致性。", user=prompt_text)'
new = r'''Prompt(
            system=(
                "你是一位专业的小说审稿编辑，擅长检查时间线一致性。\n\n"
                "输出要求：\n"
                "1. 严格遵循 JSON 格式输出，不要包含任何额外文字\n"
                "2. 返回 JSON 必须包含所有必需字段\n"
                "3. 如果没有发现问题，conflicts 返回空数组\n"
                "4. severity 只能是 critical/warning 之一\n"
                "5. description 需具体说明冲突的时间点和对故事的影响\n"
                "6. suggestion 应提供具体的时间线修正建议"
            ),
            user=prompt_text
        )'''
if old in content:
    content = content.replace(old, new)
    print("OK: timeline consistency")
else:
    print("FAIL: timeline consistency not found")

# Replace 3: storyline consistency
old = 'Prompt(system="你是小说审稿助手，专门检查故事线连贯性。", user=prompt_text)'
new = r'''Prompt(
            system=(
                "你是一位专业的小说审稿编辑，擅长检查故事线连贯性。\n\n"
                "输出要求：\n"
                "1. 严格遵循 JSON 格式输出，不要包含任何额外文字\n"
                "2. 返回 JSON 必须包含所有必需字段\n"
                "3. 如果故事线连贯，gaps 返回空数组\n"
                "4. severity 只能是 warning/suggestion 之一\n"
                "5. description 需具体说明断裂或停滞的位置\n"
                "6. suggestion 应提供推进故事线的具体建议"
            ),
            user=prompt_text
        )'''
if old in content:
    content = content.replace(old, new)
    print("OK: storyline consistency")
else:
    print("FAIL: storyline consistency not found")

# Replace 4: foreshadowing usage
old = 'Prompt(system="你是小说审稿助手，专门检查伏笔使用。", user=prompt_text)'
new = r'''Prompt(
            system=(
                "你是一位专业的小说审稿编辑，擅长检查伏笔使用。\n\n"
                "输出要求：\n"
                "1. 严格遵循 JSON 格式输出，不要包含任何额外文字\n"
                "2. 返回 JSON 必须包含所有必需字段\n"
                "3. 如果没有错过机会，missed_opportunities 返回空数组\n"
                "4. description 需具体说明伏笔未被使用的机会\n"
                "5. suggestion 应提供如何在该位置使用伏笔的具体建议"
            ),
            user=prompt_text
        )'''
if old in content:
    content = content.replace(old, new)
    print("OK: foreshadowing usage")
else:
    print("FAIL: foreshadowing usage not found")

# Replace 5: improvement suggestions
old = 'Prompt(system="你是小说审稿助手，专门提供改进建议。", user=prompt_text)'
new = r'''Prompt(
            system=(
                "你是一位专业的小说审稿编辑，擅长提供改进建议。\n\n"
                "输出要求：\n"
                "1. 严格遵循 JSON 格式输出，不要包含任何额外文字\n"
                "2. 返回 JSON 必须包含所有必需字段\n"
                "3. suggestions 必须返回 3-5 条建议\n"
                "4. 每条建议必须是具体可操作的改进意见\n"
                "5. 建议应针对已发现的问题给出，非泛泛而谈\n"
                "6. 优先关注 critical 级别问题"
            ),
            user=prompt_text
        )'''
if old in content:
    content = content.replace(old, new)
    print("OK: improvement suggestions")
else:
    print("FAIL: improvement suggestions not found")

with open('chapter_review_service.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Written successfully")