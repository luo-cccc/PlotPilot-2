# 子项目 8 前端扩展 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步实施。步骤使用 `- [ ]` 勾选追踪。

**Goal:** 在子项目 8 后端工作流就绪后，将 **HTTP 能力** 以类型安全的 `workflow` API 客户端接入 Vue（工作台、任务轮询、一致性/故事线展示），并淘汰遗留 `jobApi` 对不存在路由的依赖。

**Architecture:** 沿用现有 `apiClient`（`config.ts`）与 **`slug === novel_id`** 约定；新增 `api/workflow.ts` 封装 `/api/v1/novels/{id}/...` 与 `/api/v1/jobs/...`；`useWorkbench` / `JobStatusIndicator` 改为调用 `workflowApi`，轮询逻辑保留；新 UI 以 **抽屉/侧栏卡片** 渐进增加，避免一次性改写 `Workbench.vue`。

**Tech Stack:** Vue 3、TypeScript、axios、Naive UI、Pinia（统计沿用既有 store）。

**设计说明（brainstorming 摘要）:** 后端路由尚未全部实现时，前端先 **对齐路径与类型**，调用失败时在 UI 提示「功能即将开放」或由集成测试在子项目 8 合并后点亮。

---

## 文件映射

| 职责 | 路径 |
|------|------|
| Workflow / 生成 / Job HTTP 客户端 | `web-app/src/api/workflow.ts` |
| 工作流相关 DTO（可选拆分） | `web-app/src/types/workflow.ts` |
| 工作台任务与轮询 | `web-app/src/composables/useWorkbench.ts` |
| 顶栏任务状态 | `web-app/src/components/stats/JobStatusIndicator.vue` |
| 聚合导出 | `web-app/src/api/index.ts` |
| 接口总览文档 | `docs/frontend-backend-api-overview.md` |

---

### Task 1: API 层 `workflow.ts` 与类型

**Files:**
- Create: `web-app/src/api/workflow.ts`
- Create（可选）: `web-app/src/types/workflow.ts`
- Modify: `web-app/src/api/index.ts`

- [x] **Step 1:** 实现 `workflowApi`，方法覆盖（路径与 `2026-04-01-subprojects-3-8-overview.md` 对齐）：
  - `POST /novels/{novel_id}/generation/chapter` — 带上下文的章节生成（body：`chapter_number`, `outline`, 可选 `max_tokens`）
  - `GET /novels/{novel_id}/consistency-report` — query：`chapter` 可选
  - `GET /novels/{novel_id}/storylines`
  - `POST /novels/{novel_id}/plot-arc` — body 与后端 DTO 一致
  - `POST /novels/{novel_id}/jobs/plan` — `dry_run`, `mode`
  - `POST /novels/{novel_id}/jobs/write` — `from_chapter`, `to_chapter`, 等
  - `GET /jobs/{job_id}` — 任务状态（若后端挂在 `/novels/.../jobs/{id}` 则改路径并更新本文档）
  - `POST /jobs/{job_id}/cancel`
- [x] **Step 2:** 全部使用 `apiClient`，响应拦截器与 `novel.ts` 一致（已是 `data` 直出）。
- [x] **Step 3:** `export * from './workflow'` 写入 `api/index.ts`。
- [ ] **Step 4:** `npm run build`（或 `vue-tsc`）无类型错误。

---

### Task 2: 替换遗留 `jobApi` 调用

**Files:**
- Modify: `web-app/src/composables/useWorkbench.ts`
- Modify: `web-app/src/components/stats/JobStatusIndicator.vue`

- [x] **Step 1:** `import { workflowApi } from '../api/workflow'`（路径按目录调整）。
- [x] **Step 2:** `confirmPlan` / `startWrite` / `cancelRunningTask` / 轮询 `getStatus` 改为 `workflowApi` 对应方法。
- [x] **Step 3:** 删除对 `../api/book` 的 `jobApi` 依赖（若 `book.ts` 仅余 job，可后续 Task 4 清理）。
- [ ] **Step 4:** 手动验证：后端未实现时 Network 为 404 — 预期；实现后应 2xx 且轮询结束。

---

### Task 3: 工作台 UI 扩展（渐进）

**Files:**
- Modify: `web-app/src/views/Workbench.vue` 或子组件
- Create（可选）: `web-app/src/components/workbench/ConsistencyReportCard.vue`

- [ ] **Step 1:** 「结构规划 / 撰稿」按钮已存在时，仅确保绑定的是 `workflowApi` 触发的 composable 方法（无重复逻辑）。
- [ ] **Step 2:** 增加「一致性」入口：按钮或 `SettingsPanel` 内 tab，调用 `workflowApi.getConsistencyReport(slug)`，结果用 `n-card` + `n-code` 或 JSON 预览（先 MVP）。
- [ ] **Step 3:** （可选）故事线列表：`getStorylines` 结果用 `n-list` 展示。

---

### Task 4: 清理与文档

**Files:**
- Modify: `web-app/src/api/book.ts`（仅删除 `jobApi` 若已无引用）
- Modify: `docs/frontend-backend-api-overview.md`

- [ ] **Step 1:** 全仓 `grep jobApi` 确认无引用。
- [ ] **Step 2:** 在总览文档中增加 **Workflow** 小节，列出上表路径。
- [ ] **Step 3:** 更新 `EXECUTION-PROGRESS.md` 中「阶段 0 / 子项目 8 前端」一句状态。

---

### Task 5: 验证

- [ ] **Step 1:** `cd web-app && npm run build`
- [ ] **Step 2:** 后端实现对应路由后，跑一条：创建 job → 轮询 → 取消（若有）

---

## 依赖

- 后端：`interfaces/api/v1` 下实际注册与本文路径一致（或提供环境变量 `VITE_WORKFLOW_API_PREFIX` 做前缀切换 —— **YAGNI，默认不做**）。

## 参考

- `docs/superpowers/plans/2026-04-01-subprojects-3-8-overview.md` 子项目 8
- `docs/frontend-backend-api-overview.md`
