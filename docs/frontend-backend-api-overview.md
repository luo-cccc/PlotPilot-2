# aitext 前后端功能与接口总览

> 文档目的：集中说明当前 **Vue 前端**、**FastAPI 后端** 的路由、API 模块与对接状态，便于开发与迁移时查阅。  
> 路径与接口以仓库代码为准；若与 README 中端口不一致，以 `web-app/vite.config.ts`（默认 **3000**）为准。

---

## 1. 全局约定

| 约定 | 说明 |
|------|------|
| 书目标识 | 前端路由参数 **`slug`** 与后端 **`novel_id`** 使用**同一字符串**（`data/` 下目录名）。 |
| 主业务 API 前缀 | **`/api/v1`** |
| 统计 API 前缀 | **`/api/stats`**（响应包一层 `SuccessResponse`） |
| 开发代理 | 前端 `npm run dev` 时，`/api` → `http://127.0.0.1:8000`（见 `web-app/vite.config.ts`）。 |
| 直连后端 | `web-app/src/api/config.ts` 中 `apiClient` 默认 `baseURL = http://localhost:8000/api/v1`（不经 Vite 代理也可）。 |
| 环境变量 | `ANTHROPIC_API_KEY` 或 `ANTHROPIC_AUTH_TOKEN`（二选一）；可选 `ANTHROPIC_BASE_URL`。可放在 **`aitext/.env`**：`interfaces/main.py` 启动时会通过 `load_env.py` 自动加载。 |

---

## 2. 前端页面与路由（Vue Router）

| 路径 | 视图 | 主要用途 |
|------|------|----------|
| `/` | `Home.vue` | 书目列表、创建小说（`novelApi`） |
| `/book/:slug/workbench` | `Workbench.vue` | 工作台（章节列表、聊天、侧栏 Bible/知识等；组合 `useWorkbench` 等） |
| `/book/:slug/cast` | `Cast.vue` | 人物关系图（`castApi`） |
| `/book/:slug/chapter/:id` | `Chapter.vue` | 单章编辑（`chapterApi` + 部分仍用 `bookApi`） |

---

## 3. 后端 HTTP 接口（FastAPI）

### 3.1 根与健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | API 欢迎信息 |
| GET | `/health` | 健康检查 |

### 3.2 小说 `NovelService` — 前缀 `/api/v1/novels`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels` | 列出全部小说 |
| POST | `/api/v1/novels` | 创建小说（body：`novel_id`, `title`, `author`, `target_chapters`） |
| GET | `/api/v1/novels/{novel_id}` | 小说详情 |
| PUT | `/api/v1/novels/{novel_id}/stage` | 更新阶段（body：`stage`） |
| DELETE | `/api/v1/novels/{novel_id}` | 删除小说 |
| GET | `/api/v1/novels/{novel_id}/statistics` | 小说统计 |

### 3.3 章节 `ChapterService` — 前缀 `/api/v1/novels`（`chapters` 路由）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{novel_id}/chapters` | 某书全部章节 |
| GET | `/api/v1/novels/{novel_id}/chapters/{chapter_number}` | 指定章节 |
| PUT | `/api/v1/novels/{novel_id}/chapters/{chapter_number}` | 更新章节（含正文等） |

### 3.4 Bible `BibleService` — 前缀 `/api/v1/bible`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/bible/novels/{novel_id}/bible` | 创建 Bible（body：`bible_id`, `novel_id`） |
| GET | `/api/v1/bible/novels/{novel_id}/bible` | 获取 Bible |
| GET | `/api/v1/bible/novels/{novel_id}/bible/characters` | 人物列表 |
| POST | `/api/v1/bible/novels/{novel_id}/bible/characters` | 添加人物 |
| POST | `/api/v1/bible/novels/{novel_id}/bible/world-settings` | 添加世界设定 |

### 3.5 Cast `CastService`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{novel_id}/cast` | 关系图 |
| PUT | `/api/v1/novels/{novel_id}/cast` | 更新关系图 |
| GET | `/api/v1/novels/{novel_id}/cast/search` | 搜索（query：`q`） |
| GET | `/api/v1/novels/{novel_id}/cast/coverage` | 覆盖率分析 |

### 3.6 知识图谱 `KnowledgeService` — 前缀 `/api/v1/novels/{novel_id}/knowledge`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{novel_id}/knowledge` | 获取知识图谱 |
| PUT | `/api/v1/novels/{novel_id}/knowledge` | 更新知识图谱 |
| GET | `/api/v1/novels/{novel_id}/knowledge/search` | 检索（query：`q`, `k`） |

### 3.7 聊天 `ChatService`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{novel_id}/chat/messages` | 消息列表 |
| POST | `/api/v1/novels/{novel_id}/chat` | 非流式发送 |
| POST | `/api/v1/novels/{novel_id}/chat/stream` | **SSE 流式** |
| POST | `/api/v1/novels/{novel_id}/chat/clear` | 清空线程（body：`digest_too`） |

### 3.8 AI 生成 `AIGenerationService` — 前缀 `/api/v1/ai`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/ai/generate-chapter` | 按大纲生成章节正文（body：`novel_id`, `chapter_number`, `outline`） |

### 3.9 工作流（子项目 8）— `interfaces/api/v1/generation.py` + `workflowApi`

已实现（`generation` 路由，`/api/v1` 前缀）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/novels/{novel_id}/generate-chapter` | 完整工作流：上下文 + LLM + 一致性报告（body：`chapter_number`, `outline`） |
| GET | `/api/v1/novels/{novel_id}/consistency-report` | 当前为占位空报告 |
| GET / POST | `/api/v1/novels/{novel_id}/storylines` | 故事线列表 / 创建 |
| GET / POST | `/api/v1/novels/{novel_id}/plot-arc` | 情节弧读 / 创建或更新 |

**尚未在后端注册**（`workflowApi` 中已写注释，调用会 404，需补 FastAPI 路由或先隐藏 UI）：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/novels/{novel_id}/jobs/plan` | 结构规划任务 |
| POST | `/api/v1/novels/{novel_id}/jobs/write` 等 | 撰稿 / run / export |
| GET / POST | `/api/v1/jobs/{job_id}`、`/cancel` | 任务轮询与取消 |

轻量生成（无完整工作流）仍用 **§3.8** `POST /api/v1/ai/generate-chapter`（`aiApi`）。

实施清单：`docs/superpowers/plans/2026-04-02-subproject-8-frontend-extensions.md`。

### 3.10 统计 `StatsService` — 前缀 `/api/stats`

响应格式：`{ "data": <payload>, ... }`（`SuccessResponse`）。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats/global` | 全局统计 |
| GET | `/api/stats/book/{slug}` | 单书统计（参数名仍为 **slug**，与 `novel_id` 同值） |
| GET | `/api/stats/book/{slug}/chapter/{chapter_id}` | 单章统计 |
| GET | `/api/stats/book/{slug}/progress` | 写作进度时间序列（query：`days`，默认 30） |

---

## 4. 前端 API 模块与后端映射

| 文件 | `baseURL` / 方式 | 对应后端 | 对接状态 |
|------|------------------|----------|----------|
| `api/config.ts` | `apiClient` → `VITE_API_BASE_URL` 或 `http://localhost:8000/api/v1` | `/api/v1` | 已对齐 |
| `api/novel.ts` | `apiClient` | 小说 CRUD、统计 | 已对齐 |
| `api/chapter.ts` | `apiClient` | 章节列表/读写 | 已对齐 |
| `api/bible.ts` | `apiClient` | Bible CRUD | 已对齐 |
| `api/cast.ts` | `/api/v1`（axios） | Cast 全部 | 已对齐 |
| `api/knowledge.ts` | `/api/v1`（axios） | Knowledge 全部 | 已对齐 |
| `api/chat.ts` | `/api/v1`（axios + `fetch` 流式） | Chat 全部 | 已对齐 |
| `api/ai.ts` | `apiClient` | `POST .../ai/generate-chapter` | 后端有；**当前业务组件未引用** |
| `api/stats.ts` | `/api`（相对，经代理）；响应拦截器解包 `SuccessResponse.data` | `/api/stats/*` | 已对齐 |
| `api/workflow.ts` | `apiClient` | 见 §3.9 | **generate-chapter / storylines / plot-arc 已对齐**；Job 路由仍待后端 |
| `api/book.ts` | `/api`（相对） | 见下节「遗留」 | **后端无对应路由**（`jobApi` 已迁 `workflowApi`） |

---

## 5. 遗留前端 `book.ts`（后端未实现）

以下路径由 `web-app/src/api/book.ts` 定义，**当前 `interfaces/main.py` 未注册**，请求会失败（404）。用于旧版「一书一目录」工作台的部分能力；迁移方向是改用上表 **v1** 客户端或新增 Job API。

| 分组 | 方法 | 路径模式 | 说明 |
|------|------|----------|------|
| 书目 | GET/POST/DELETE | `/api/books`、`/api/jobs/create-book`、`/api/book/{slug}` | 列表/创建/删除 |
| 书桌聚合 | GET | `/api/book/{slug}/desk` | 已由 `novelApi`+`chapterApi` 等替代 |
| Cast | * | `/api/book/{slug}/cast*` | 请用 `castApi` |
| Knowledge | * | `/api/book/{slug}/knowledge*` | 请用 `knowledgeApi` |
| Bible | * | `/api/book/{slug}/bible` | 请用 `bibleApi` |
| 章节正文/审读/结构 | * | `/api/book/{slug}/chapter/...` | 请用 `chapterApi` 等 |
| 聊天（旧） | * | `/api/book/{slug}/chat*` | 请用 `api/chat.ts` |
| **任务** | POST/GET | `/api/jobs/{slug}/plan`、`/write`、`/run`、`/export`、`/api/jobs/{jobId}/*` | **后端暂无 Job 模块** |

仍从 `book.ts` 引用 **`bookApi`** 的组件（需逐步替换）：`BiblePanel.vue`、`Chapter.vue`（部分）等。  
**图表侧栏已对接 v1**：`CastGraphCompact.vue` → `castApi`；`KnowledgeTripleGraph.vue`、`KnowledgePanel.vue`（叙事/检索/保存）→ `knowledgeApi`，章标题来自 `chapterApi.listChapters`。  
**任务 API**：`workflowApi`（`useWorkbench.ts`、`JobStatusIndicator.vue`）；遗留 `book.ts` 内 `jobApi` 已不再被引用。

---

## 6. 组件与 API 使用关系（简要）

| 区域 / 组件 | 使用的 API 模块 |
|-------------|-----------------|
| `Home.vue` | `novelApi` |
| `useWorkbench.ts` | `novelApi`、`chapterApi`、`statsStore`（stats）、`workflowApi`（任务；后端待实现） |
| `ChatArea.vue` | `chat.ts` → `chatApi` |
| `Cast.vue` | `castApi` |
| `BiblePanel.vue` | `bookApi`（遗留） |
| `KnowledgePanel.vue`、`KnowledgeTripleGraph.vue` | `knowledgeApi`；章名 via `chapterApi` |
| `CastGraphCompact.vue` | `castApi` |
| `Chapter.vue` | `chapterApi` + `bookApi`（遗留） |
| `statsStore` / 侧栏统计 | `statsApi` |
| `JobStatusIndicator.vue` | `workflowApi` |

---

## 7. 后端已有但未通过 HTTP 暴露的能力

| 能力 | 代码位置 | 说明 |
|------|----------|------|
| 长篇小说生成工作流 | `application/workflows/novel_generation_workflow.py` | `NovelGenerationWorkflow`，**未挂载路由**；可与未来 Job API 结合 |
| 索引 / 向量检索等 | `application/services/indexing_service.py` 等 | **无** `interfaces` 路由；与 `docs/superpowers/plans` 中子项目规划一致 |

---

## 8. 在线文档与调试

- 启动后端后：**Swagger UI** — `http://localhost:8000/docs`  
- **ReDoc** — `http://localhost:8000/redoc`  

---

## 9. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-04-02 | 初版与图表/统计修复；子项目 8 前端扩展：`workflow.ts`、实施计划 `2026-04-02-subproject-8-frontend-extensions.md`、`workflowApi` 接线 |
