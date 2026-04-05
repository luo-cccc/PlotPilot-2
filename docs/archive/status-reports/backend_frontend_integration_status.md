# 后端功能与前端对接分析

## 后端路由模块（12个）

### ✅ 已对接的模块

1. **novels.py** → `web-app/src/api/novel.ts`
   - 小说CRUD、章节管理

2. **chapters.py** → `web-app/src/api/chapter.ts`
   - 章节详情、审阅

3. **bible.py** → `web-app/src/api/bible.ts`
   - 世界观设定管理

4. **cast.py** → `web-app/src/api/cast.ts`
   - 角色关系图谱

5. **knowledge.py** → `web-app/src/api/knowledge.ts`
   - 知识图谱（旧版）

6. **generation.py** → `web-app/src/api/workflow.ts`
   - 章节生成工作流

7. **story_structure.py** → `web-app/src/api/structure.ts`
   - 故事结构树管理

8. **stats.py** → `web-app/src/api/stats.ts`
   - 统计数据

9. **planning_routes.py** → `web-app/src/api/planning.ts` ✅
   - 宏观规划、幕级规划（已部分对接）

### ❌ 未对接的模块（3个）

1. **continuous_planning_routes.py** - 连续规划API
   - `/api/v1/planning/novels/{novel_id}/continue` - AI续规划
   - `/api/v1/planning/acts/{act_id}/create-next` - 创建下一幕
   - `/api/v1/planning/acts/{act_id}/plan` - 幕级详细规划

2. **chapter_element_routes.py** - 章节元素管理API
   - `/api/v1/chapters/{chapter_id}/elements` - 章节元素CRUD
   - `/api/v1/knowledge-graph/elements/{element_type}/{element_id}/chapters` - 元素关联查询
   - `/api/v1/knowledge-graph/elements/{element_type}/{element_id}/relations` - 元素关系查询

3. **knowledge_graph_routes.py** - 新版知识图谱API
   - `/api/v1/knowledge-graph/novels/{novel_id}/infer` - 推断知识图谱
   - `/api/v1/knowledge-graph/chapters/{chapter_id}/infer` - 推断章节知识
   - `/api/v1/knowledge-graph/novels/{novel_id}/triples` - 三元组管理
   - `/api/v1/knowledge-graph/chapters/{chapter_id}/triples` - 章节三元组
   - `/api/v1/knowledge-graph/triples/{triple_id}/confirm` - 确认三元组

## 详细功能缺失

### 1. 连续规划功能（continuous_planning_routes.py）
**后端已实现：**
- AI 自动续规划（根据当前进度生成后续章节规划）
- 创建下一幕（自动规划下一个幕的结构）
- 幕级详细规划（为每一幕生成详细的章节规划）

**前端缺失：**
- 无 UI 入口触发 AI 续规划
- 无自动创建下一幕的功能
- 无幕级详细规划的交互界面

### 2. 章节元素管理（chapter_element_routes.py）
**后端已实现：**
- 章节元素关联（角色、地点、物品、组织、事件）
- 元素重要性标记（major/normal/minor）
- 元素出场顺序管理
- 批量更新章节元素
- 查询元素在哪些章节出现
- 查询元素之间的关系

**前端缺失：**
- 无章节元素管理界面
- 无法标记章节中出现的角色/地点
- 无法查看元素的章节分布
- 无法可视化元素关系网络

### 3. 新版知识图谱（knowledge_graph_routes.py）
**后端已实现：**
- 基于三元组的知识图谱（subject-predicate-object）
- 自动推断章节知识（从章节内容提取关系）
- 自动推断整部小说知识图谱
- 三元组确认/编辑/删除
- 全局知识图谱查询

**前端缺失：**
- 无三元组可视化界面
- 无自动推断知识图谱的入口
- 无三元组编辑/确认界面
- 无知识图谱关系网络可视化

## 建议优先级

### 高优先级（核心功能）
1. **连续规划功能** - 提升写作效率的关键功能
   - 在工作台添加"AI 续规划"按钮
   - 在故事结构树中添加"创建下一幕"功能

### 中优先级（增强功能）
2. **章节元素管理** - 提升内容组织能力
   - 在章节编辑器中添加元素标记功能
   - 创建元素管理面板

### 低优先级（高级功能）
3. **新版知识图谱** - 高级分析功能
   - 创建知识图谱可视化页面
   - 添加自动推断入口

## 实施建议

### 第一阶段：连续规划功能
1. 创建 `web-app/src/api/continuousPlanning.ts`
2. 在 `StoryStructureTree.vue` 中添加"创建下一幕"按钮
3. 在工作台添加"AI 续规划"功能

### 第二阶段：章节元素管理
1. 创建 `web-app/src/api/chapterElements.ts`
2. 创建 `ChapterElementsPanel.vue` 组件
3. 在章节编辑器中集成元素标记功能

### 第三阶段：新版知识图谱
1. 创建 `web-app/src/api/knowledgeGraph.ts`
2. 创建知识图谱可视化页面
3. 集成三元组编辑功能
