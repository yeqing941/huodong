# 游戏活动参考库规格与原型调整实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将已确认的六项调整同步到 PRD、页面结构规划和纯静态 Web 原型中，并验证新增核心路径。

**Architecture:** 保持现有单文件原型架构，在 `prototype/index.html` 内扩展模拟状态、页面渲染和弹窗交互。文档层更新为同一套规则：活动编辑、批量录入、模拟爬虫进度、管理员归档、三级标签和游戏类型配置；不接入真实后端、爬虫或文件解析。

**Tech Stack:** Markdown、原生 HTML/CSS/JavaScript、Python 静态 HTTP 服务、Node 语法检查。

---

### Task 1: 更新产品规格与页面结构文档

**Files:**
- Modify: `e:/huodong/docs/superpowers/specs/2026-10-17-game-activity-reference-library-prd-1.0.md`
- Modify: `e:/huodong/docs/superpowers/specs/页面结构规划-V1.0.md`

- [ ] **Step 1: 在 PRD 中补充六项确认变更**

补充活动编辑回填、批量录入、爬虫进度/失败 URL/单条重试、管理员活动归档恢复、三级标签管理、游戏类型配置，并同步权限矩阵和验收标准。

- [ ] **Step 2: 在页面结构规划中补充页面内交互**

在活动录入、活动详情、爬虫任务、标签树管理页面中说明新增页签、抽屉、确认弹窗和状态流转，不新增独立业务页面。

- [ ] **Step 3: 检查文档一致性**

确认文档不引入真实后端、真实文件解析、真实外部爬虫或批量编辑/删除/导出等未确认能力。

### Task 2: 实现活动编辑、归档与批量录入

**Files:**
- Modify: `e:/huodong/prototype/index.html`

- [ ] **Step 1: 扩展活动数据模型**

为活动增加 `owner`、`archived`、`archiveReason` 字段；新增可配置的 `gameTypes` 和三级 `tagTree` 模拟数据。

- [ ] **Step 2: 回填编辑表单并保存修改**

`openEntry(id)` 打开编辑状态时回填活动字段和标签；保存时更新原记录而不是新增记录，并根据角色限制运营只能编辑自己录入的活动。

- [ ] **Step 3: 增加批量录入页签**

活动录入页增加“单条录入/批量录入”页签。批量页展示预设导入文件、有效记录、问题记录和导入有效记录按钮；导入后把预设有效记录加入活动库并提示统计结果。

- [ ] **Step 4: 增加管理员归档/恢复**

超级管理员在详情页看到“归档活动”；确认后将活动标记为归档并从正常列表隐藏。管理员可从活动库的归档筛选中恢复，普通用户和运营不显示入口。

### Task 3: 实现爬虫采集与审核体验

**Files:**
- Modify: `e:/huodong/prototype/index.html`

- [ ] **Step 1: 扩展任务状态和失败记录展示**

任务详情抽屉展示进度、新增、重复、失败、待打标、失败 URL 和失败原因；任务表展示执行中状态。

- [ ] **Step 2: 实现模拟采集状态流转**

触发后依次显示任务已创建、执行中和部分完成预设结果；完成后将预设待打标记录加入 AI 待审核队列。

- [ ] **Step 3: 实现单条失败重试**

失败记录提供单条重试按钮，点击后更新该记录状态并显示反馈，不开放来源规则编辑给运营。

### Task 4: 实现三级标签和游戏类型管理

**Files:**
- Modify: `e:/huodong/prototype/index.html`

- [ ] **Step 1: 为标签树增加层级新增入口**

超级管理员可在标签树页新增一级、二级、三级标签；新增二级/三级时选择父级；新增后立即显示在树中，最多三级。

- [ ] **Step 2: 增加游戏类型页签**

标签树管理页增加“活动形式标签/游戏类型”页签，展示类型名称、说明、关联活动数量和启用状态；支持新增、编辑和停用预设反馈。

- [ ] **Step 3: 让录入和筛选读取配置**

单条/批量录入的游戏类型选项来自启用中的 `gameTypes`；活动库筛选仅展示启用类型；历史活动保留停用类型。

### Task 5: 静态检查、启动预览和冒烟验证

**Files:**
- Modify: `e:/huodong/prototype/index.html`

- [ ] **Step 1: 运行 JavaScript 语法检查**

提取 script 并执行 `node --check`，预期输出无语法错误。

- [ ] **Step 2: 检查关键入口和外部依赖**

确认主要函数、页面分支、角色入口均存在，且没有新增真实 API、外部 CDN 或持久化依赖。

- [ ] **Step 3: 启动 HTTP 预览并检查 200**

在 `e:/huodong/prototype` 启动 `python -m http.server 4173`，请求首页确认返回 200。

- [ ] **Step 4: 冒烟验证四条路径**

验证活动编辑、批量录入、模拟爬虫进度/重试、超级管理员标签/类型管理和归档入口可到达；完成后停止，不进入正式工程开发。
