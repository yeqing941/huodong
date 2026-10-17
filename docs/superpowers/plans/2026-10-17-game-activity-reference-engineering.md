# 游戏活动参考库工程开发计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于已确认的 PRD、MVP 页面结构、静态原型和 OpenAPI 3.0 契约，分阶段交付一个由 Vue 3 前端、Django 后端和 MariaDB 持久化组成的可验证游戏活动参考库。

**Architecture:** 采用前后端分离结构。Django 提供 `/api/v1` REST API、认证、权限、业务状态流转、文件上传和审计日志；Vue 负责 11 个 MVP 页面、路由权限和交互状态；MariaDB 保存用户、活动、标签、游戏类型、收藏、爬虫任务、AI 审核、批量导入和审计数据。爬虫、AI 服务在 P0 先通过后端服务边界和可替换实现接入，不能影响主活动数据的持久化与查询。

**Tech Stack:** Vue 3、TypeScript、Vite、Element Plus；Python、Django；MariaDB；Git。测试使用 Django 测试框架和前端项目既定的 TypeScript/Vite 测试方案；不额外引入未被需求要求的基础设施组件。

---

## 一、开发前必须确认的关键事项

以下事项不会阻塞本地骨架、数据库模型、权限和核心活动库开发，但会影响真实部署或外部服务集成。进入对应阶段前必须由产品/运维确认，计划不擅自替换业务决策：

1. **登录方式**：PRD 同时保留公司 SSO/飞书登录和账号密码 fallback。第一阶段先实现 OpenAPI 已定义的账号密码登录闭环；SSO/飞书接入作为独立适配层，确认身份提供方后再接入。
2. **定时频率**：PRD 建议每周 2 次，但尚未最终确认。爬虫配置保存调度表达式并支持测试环境手动触发；上线前由运营确认具体频率。
3. **初始数据**：游戏类型、一级/二级标签、管理员账号需要运营团队提供初始化清单。开发使用固定种子数据格式，不凭空扩充业务枚举。
4. **AI 服务**：AI 厂商和视觉接口尚未确定。先实现内部 AI 服务接口、失败状态和人工审核流；真实供应商只通过该接口接入。
5. **图片存储与部署**：本地开发使用 Django 文件存储验证上传和访问；上线前由运维确认对象存储、备份、访问域名和文件保留策略。
6. **爬虫合规**：上线真实来源前确认 robots、站点条款、版权和内部法务要求；未确认前仅使用可控测试来源或固定采集适配器。

---

## 二、阶段总览

| 阶段 | 可独立验证的交付物 | 主要范围 | Git 稳定版本 |
|---|---|---|---|
| 0 | 契约与开发基线 | 校验 OpenAPI、建立目录约定、定义环境变量和验收清单 | 是 |
| 1 | Django + MariaDB 可运行后端 | 工程骨架、核心模型、迁移、健康检查、统一响应 | 是 |
| 2 | Vue 可运行前端 | Vite 工程、Element Plus、路由、布局、API 客户端、登录页面骨架 | 是 |
| 3 | 认证与权限闭环 | 登录、当前用户、角色权限、前后端越权拒绝 | 是 |
| 4 | 活动浏览最小闭环 | 活动查询、标签/类型/名称筛选、详情、截图、收藏 | 是 |
| 5 | 活动写入闭环 | 手动新增、编辑、截图上传、归档恢复、批量导入结果 | 是 |
| 6 | 标签与游戏类型管理 | 三级标签树、排序、迁移/合并/停用、游戏类型管理 | 是 |
| 7 | 爬虫任务闭环 | 配置、手动触发、任务状态、失败记录、重试和统计 | 是 |
| 8 | AI 审核闭环 | AI 待打标、运营初审、管理员确认/修正/退回 | 是 |
| 9 | 用户与审计 | 用户管理、停用、审计日志查询与关键操作记录 | 是 |
| 10 | 约束与稳定性 | 限流、软删除、防导出、异常状态和权限边界补强 | 是 |
| 11 | 全量联调与回归 | 真实数据库保存验证、端到端主流程、Debug、最终回归 | 是 |

每个阶段完成后先运行该阶段验证命令，再建立稳定 Git 提交；未通过验证不得进入下一阶段。

---

## 三、详细执行计划

### Task 0：契约校验与工程基线

**Files:**
- Modify: `docs/api/openapi.yaml`（仅在语义校验发现明确契约错误时修改）
- Create: `.gitignore`
- Create: `docs/superpowers/checklists/2026-10-17-engineering-acceptance.md`

- [ ] **Step 1: 校验 OpenAPI YAML 语法、重复路径和 `$ref`**

运行：

```powershell
python -m pip install pyyaml
python -c "import yaml; from pathlib import Path; p=Path('docs/api/openapi.yaml'); d=yaml.safe_load(p.read_text(encoding='utf-8')); assert d['openapi']=='3.0.3'; assert '/activities' in d['paths']; assert set(d['paths']['/activities']) >= {'get','post'}; print('OpenAPI YAML OK')"
```

预期：输出 `OpenAPI YAML OK`。随后使用 OpenAPI 校验工具检查所有 `$ref` 可解析、路径参数已声明、响应结构合法；校验命令和版本记录在工程验证输出中。

- [ ] **Step 2: 建立忽略规则和目录约定**

`.gitignore` 必须忽略：Python 虚拟环境、Django 本地数据库文件、环境变量文件、前端依赖目录、构建产物、上传临时文件、测试缓存和编辑器缓存；不得忽略源码、迁移文件、测试夹具和 OpenAPI 文档。

- [ ] **Step 3: 建立阶段验收清单**

验收清单按 PRD 的三条主线编写：

```text
普通用户：登录 → 筛选 → 卡片 → 详情 → 收藏；
运营：登录 → 手动触发爬虫 → 查看任务 → 重试失败 → AI 初审；
管理员：最终审核 → 标签/游戏类型 → 爬虫配置 → 用户 → 审计日志。
```

- [ ] **Step 4: 建立 Git 稳定版本**

```powershell
git add .gitignore docs/api/openapi.yaml docs/superpowers/checklists/2026-10-17-engineering-acceptance.md
 git commit -m "chore: establish engineering baseline"
```

验证：`git status --short` 为空，提交包含契约和基线文件。

### Task 1：Django 后端骨架与 MariaDB 数据基础

**Files:**
- Create: `backend/manage.py`
- Create: `backend/config/settings.py`
- Create: `backend/config/urls.py`
- Create: `backend/config/wsgi.py`
- Create: `backend/config/asgi.py`
- Create: `backend/apps/core/`
- Create: `backend/apps/accounts/`
- Create: `backend/apps/activities/`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/pytest.ini` 或 Django 测试配置文件

- [ ] **Step 1: 初始化 Django 项目和应用边界**

应用边界固定为：`core` 负责统一响应、异常、分页、请求 ID 和公共权限；`accounts` 负责用户、角色、认证；`activities` 负责活动、截图、标签、游戏类型和收藏。后续爬虫、审核和审计各自使用独立 app，不把所有逻辑写入单个视图文件。

- [ ] **Step 2: 配置 MariaDB 连接和环境变量**

必须支持以下环境变量：数据库地址、端口、名称、用户、密码、Django secret、调试开关、媒体目录和 API 前缀。提交 `.env.example`，不得提交真实凭证。

- [ ] **Step 3: 添加健康检查接口**

实现 `GET /api/v1/health`，返回应用可用状态和数据库连接状态；该接口不泄露连接凭证。健康检查失败时返回统一错误结构。

- [ ] **Step 4: 运行迁移并验证数据库连接**

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

数据保存验证：创建一条最小用户或测试记录，重新查询确认记录存在；删除测试数据后再次查询确认清理完成。

- [ ] **Step 5: 建立 Git 稳定版本**

```powershell
git add backend
 git commit -m "feat: bootstrap django backend with mariadb"
```

### Task 2：核心数据模型与统一 API 基础

**Files:**
- Create: `backend/apps/accounts/models.py`
- Create: `backend/apps/activities/models.py`
- Create: `backend/apps/core/api.py`
- Create: `backend/apps/core/exceptions.py`
- Create: `backend/apps/core/pagination.py`
- Create: `backend/apps/core/middleware.py`
- Test: `backend/apps/*/tests/test_models.py`

- [ ] **Step 1: 实现用户、角色和状态模型**

角色固定为 `user`、`operator`、`admin`；用户状态固定为 `active`、`disabled`。密码必须使用 Django 安全哈希，不保存明文。用户 email 唯一，停用用户不能登录。

- [ ] **Step 2: 实现活动及关联模型**

至少包含：`Activity`、`ActivityScreenshot`、`Tag`、`GameType`、`ActivityTag`、`Favorite`。活动状态固定为 `pending_tagging`、`pending_admin_review`、`active`、`archived`；活动去重约束使用 `source_url + game_name + activity_name`，收藏使用用户和活动联合唯一约束。

- [ ] **Step 3: 实现统一响应、分页和错误结构**

成功响应使用 `{data, meta}`；错误响应使用 `{error: {code, message, details, request_id}}`。列表统一支持 `page`、`page_size`、`sort`、`order`，并限制 `page_size <= 100`。

- [ ] **Step 4: 为约束写模型测试**

覆盖：活动必需字段、截图至少一张的业务校验、标签最多三级、收藏不可重复、停用游戏类型不能用于新活动、软删除状态保留。

- [ ] **Step 5: 验证迁移和持久化**

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py test backend.apps.accounts backend.apps.activities -v 2
```

使用 Django shell 或测试夹具写入活动、截图、标签和收藏，关闭数据库连接后重新查询确认数据仍存在。

- [ ] **Step 6: 建立 Git 稳定版本**

```powershell
git add backend
 git commit -m "feat: add core domain models and api primitives"
```

### Task 3：Vue 前端骨架、布局和 API 客户端

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/layouts/AppLayout.vue`
- Create: `frontend/src/services/http.ts`
- Create: `frontend/src/types/api.ts`
- Create: `frontend/src/styles/variables.css`
- Create: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/views/ActivityLibraryView.vue`

- [ ] **Step 1: 初始化 Vue 3 + TypeScript + Vite 工程**

只安装 Vue 3、TypeScript、Vite、Element Plus 及实现路由和 API 请求所必需的最小依赖；不引入未被需求要求的状态管理、UI 框架或后台任务组件。

- [ ] **Step 2: 建立 Element Plus 后台布局和路由表**

预留 P01-P11 路由名称，先让暂未实现页面显示明确的未实现状态，不伪造业务成功结果。路由元信息包含所需角色，后续由权限守卫使用。

- [ ] **Step 3: 实现 HTTP 客户端和统一错误处理**

客户端统一添加 Bearer Token、解析 `{data, meta}`、保存 `request_id`，收到 401 清理会话并跳转登录页，收到 403 显示无权限状态。

- [ ] **Step 4: 验证前端启动和类型检查**

```powershell
npm install
npm run type-check
npm run build
npm run dev
```

验证：浏览器可打开登录页和活动库骨架；刷新页面不出现编译错误；请求失败时显示统一错误提示。

- [ ] **Step 5: 建立 Git 稳定版本**

```powershell
git add frontend
 git commit -m "feat: bootstrap vue frontend shell"
```

### Task 4：认证、角色权限和登录闭环

**Files:**
- Modify: `backend/apps/accounts/models.py`
- Create: `backend/apps/accounts/serializers.py`
- Create: `backend/apps/accounts/views.py`
- Create: `backend/apps/accounts/permissions.py`
- Modify: `backend/config/urls.py`
- Create: `frontend/src/stores/session.ts`
- Create: `frontend/src/router/guards.ts`
- Modify: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/views/ForbiddenView.vue`
- Test: `backend/apps/accounts/tests/test_auth_api.py`

- [ ] **Step 1: 实现账号密码登录、退出和当前用户接口**

实现 OpenAPI 中 `/auth/login`、`/auth/logout`、`/auth/me`、`/auth/permissions`。登录成功返回 Bearer JWT 结构；密码错误、停用用户和无效令牌返回统一错误。

- [ ] **Step 2: 实现后端角色权限类**

权限必须在 API 层执行，不能只依赖前端隐藏：普通用户只能浏览和收藏；运营增加活动录入、爬虫任务和 AI 初审；管理员拥有全部权限。

- [ ] **Step 3: 实现前端会话状态和路由守卫**

登录后保存 token 和当前用户，刷新页面调用 `/auth/me` 恢复会话；依据角色隐藏菜单但保留后端 401/403 处理。

- [ ] **Step 4: 验证三角色权限矩阵**

```powershell
python manage.py test backend.apps.accounts.tests.test_auth_api -v 2
npm run type-check
npm run build
```

手工验证：三种账号分别登录；普通用户访问运营接口得到 403；运营访问管理员接口得到 403；管理员访问全部接口成功；停用用户登录得到 401。

- [ ] **Step 5: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: implement authentication and role permissions"
```

### Task 5：活动浏览、详情和收藏闭环

**Files:**
- Modify: `backend/apps/activities/models.py`
- Create: `backend/apps/activities/serializers.py`
- Create: `backend/apps/activities/views.py`
- Create: `backend/apps/activities/filters.py`
- Modify: `backend/config/urls.py`
- Create: `frontend/src/views/ActivityDetailView.vue`
- Create: `frontend/src/views/FavoritesView.vue`
- Create: `frontend/src/components/TagTreeFilter.vue`
- Create: `frontend/src/components/ActivityCard.vue`
- Create: `frontend/src/components/ActivityFilters.vue`
- Test: `backend/apps/activities/tests/test_activity_query_api.py`

- [ ] **Step 1: 实现活动分页查询和筛选**

支持标签、游戏类型、游戏名称、活动名称、状态、归档包含标记和排序；默认隐藏归档活动。禁止新增导出、批量下载或全库 dump 路由。

- [ ] **Step 2: 实现详情、相关活动和统计接口**

详情返回截图、标签、来源、采集方式、创建者和当前用户收藏状态；相关活动最多 8 条并按共享标签相关度和入库时间排序。

- [ ] **Step 3: 实现收藏和我的收藏**

实现收藏、取消收藏和个人收藏分页查询；收藏只对当前用户可见，重复收藏返回幂等成功或明确冲突，不影响其他用户。

- [ ] **Step 4: 实现 P02-P04 页面**

活动库支持即时组合筛选、条件清除、空结果状态和卡片收藏；详情支持多图切换、来源新窗口打开、相关活动和管理员操作入口；收藏页按最近收藏时间倒序。

- [ ] **Step 5: 验证数据保存和权限**

```powershell
python manage.py test backend.apps.activities.tests.test_activity_query_api -v 2
npm run type-check
npm run build
```

使用测试账号写入活动和收藏，重新登录后确认收藏仍存在；使用另一账号确认看不到第一账号的收藏；请求 `include_archived=true` 时普通用户和运营被拒绝。

- [ ] **Step 6: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: add activity browsing details and favorites"
```

### Task 6：手动录入、编辑、截图和批量录入

**Files:**
- Create: `backend/apps/activities/importers.py`
- Create: `backend/apps/activities/upload.py`
- Modify: `backend/apps/activities/views.py`
- Create: `frontend/src/views/ActivityEntryView.vue`
- Create: `frontend/src/components/ActivityForm.vue`
- Create: `frontend/src/components/BatchImportPanel.vue`
- Test: `backend/apps/activities/tests/test_activity_write_api.py`

- [ ] **Step 1: 实现新增和编辑接口**

实现 `POST /activities` 和 `PATCH /activities/{activityId}`。新增要求来源 URL、来源站点、游戏、启用游戏类型、活动名称、至少一张截图和至少一个标签；运营只能编辑自己录入的活动，管理员可编辑任意活动。

- [ ] **Step 2: 实现截图上传**

实现 multipart 上传、文件类型和大小校验、排序字段和媒体 URL；上传失败返回统一错误，不清空已填写表单。数据库保存截图关联，活动至少保留一张截图。

- [ ] **Step 3: 实现归档和恢复**

归档仅管理员可执行，必须提交原因，状态改为 `archived` 并保留记录；恢复改回 `active`，两者均写审计日志。

- [ ] **Step 4: 实现批量录入结果闭环**

实现 CSV/Excel 上传入口、导入任务状态、有效记录和问题记录；问题至少覆盖活动名称/游戏名称缺失、标签不存在、游戏类型不存在或已停用。P0 不实现批量编辑、批量删除和批量导出。

- [ ] **Step 5: 实现 P05 页面**

单条录入支持新增和编辑回填；批量页签支持文件选择、预览、有效记录、问题记录和仅导入有效记录；保存成功返回详情或活动库。

- [ ] **Step 6: 验证持久化和失败可恢复**

```powershell
python manage.py test backend.apps.activities.tests.test_activity_write_api -v 2
npm run type-check
npm run build
```

上传截图后重新查询活动确认媒体记录存在；编辑标签和游戏类型后重新打开详情确认已保存；归档后普通列表隐藏，管理员恢复后重新出现；批量导入部分失败时有效记录存在且问题记录可查询。

- [ ] **Step 7: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: add activity entry uploads and batch import"
```

### Task 7：标签树和游戏类型管理

**Files:**
- Create: `backend/apps/taxonomy/`
- Modify: `backend/apps/activities/models.py`
- Create: `backend/apps/taxonomy/views.py`
- Create: `backend/apps/taxonomy/serializers.py`
- Modify: `backend/config/urls.py`
- Modify: `frontend/src/views/TagManagementView.vue`
- Create: `frontend/src/components/TagTreeEditor.vue`
- Create: `frontend/src/components/GameTypeManager.vue`
- Test: `backend/apps/taxonomy/tests/test_taxonomy_api.py`

- [ ] **Step 1: 实现最多三级标签树**

实现树查询、新增、编辑、排序、停用、迁移和合并；新增二级/三级标签必须有合法父级；一级标签不能删除；所有关联活动迁移完成前不得结束合并操作。

- [ ] **Step 2: 实现游戏类型管理**

实现查询、新增、编辑、排序和停用；已被活动使用的类型不能物理删除；停用类型不出现在新录入和普通筛选选项，历史活动继续显示原类型。

- [ ] **Step 3: 实现管理页面和二次确认**

P08 使用标签树与游戏类型页签；合并、迁移、停用均使用确认弹窗并要求确认字段；标签更新后活动录入和筛选选项刷新。

- [ ] **Step 4: 验证关联数据保存**

```powershell
python manage.py test backend.apps.taxonomy.tests.test_taxonomy_api -v 2
npm run type-check
npm run build
```

写入三级标签并关联活动，迁移标签后重新查询活动确认关联已更新；停用游戏类型后确认新活动不能使用但旧活动仍可查询；普通用户调用管理接口得到 403。

- [ ] **Step 5: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: add taxonomy and game type management"
```

### Task 8：爬虫配置、任务、失败记录和重试

**Files:**
- Create: `backend/apps/crawlers/`
- Create: `backend/apps/crawlers/models.py`
- Create: `backend/apps/crawlers/services.py`
- Create: `backend/apps/crawlers/views.py`
- Modify: `backend/config/urls.py`
- Create: `frontend/src/views/CrawlerTaskView.vue`
- Create: `frontend/src/views/CrawlerConfigView.vue`
- Create: `frontend/src/components/CrawlerTaskDetail.vue`
- Test: `backend/apps/crawlers/tests/test_crawler_api.py`

- [ ] **Step 1: 实现来源配置模型和管理员接口**

保存来源、规则摘要、游戏范围、调度表达式、启停状态、连续失败次数和最近运行时间；只有管理员可新增、编辑、启用或停用配置。

- [ ] **Step 2: 实现任务状态模型和手动触发接口**

任务状态固定为 `queued`、`running`、`completed`、`partial`、`failed`、`cancelled`；运营只能选择已配置来源和合法游戏范围。重复手动触发使用幂等键或状态冲突拒绝。

- [ ] **Step 3: 实现失败记录和重试**

保存 URL、错误类型、错误原因、重试次数、最近重试时间和状态；支持整任务重试和单条失败记录重试。连续 3 次失败后自动将来源配置置为 `auto_paused`。

- [ ] **Step 4: 实现可控采集适配器**

先实现固定测试适配器：返回新增、重复、失败和待打标计数，不直接接入未确认合规的外部站点。适配器失败不得回滚既有活动。

- [ ] **Step 5: 实现 P06/P09 页面**

任务中心展示状态、进度、当前阶段、来源、游戏范围、统计和失败 URL/原因；配置页仅管理员可见，支持编辑和停用确认。

- [ ] **Step 6: 验证异步状态和数据库保存**

```powershell
python manage.py test backend.apps.crawlers.tests.test_crawler_api -v 2
npm run type-check
npm run build
```

手动触发测试任务，轮询详情确认状态从 `queued/running` 到结果状态；刷新页面确认任务、失败记录和重试次数仍存在；重试单条失败记录后确认状态和统计更新；运营调用配置写接口得到 403。

- [ ] **Step 7: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: add crawler configuration tasks and retries"
```

### Task 9：AI 自动打标和人工审核

**Files:**
- Create: `backend/apps/reviews/`
- Create: `backend/apps/reviews/models.py`
- Create: `backend/apps/reviews/services.py`
- Create: `backend/apps/reviews/views.py`
- Modify: `backend/config/urls.py`
- Create: `frontend/src/views/AIReviewView.vue`
- Create: `frontend/src/components/ReviewDrawer.vue`
- Test: `backend/apps/reviews/tests/test_review_api.py`

- [ ] **Step 1: 实现 AI 审核记录和状态机**

状态固定为 `pending_tagging`、`pending_operator_review`、`pending_admin_review`、`approved`、`returned`；AI 只能从已有标签树返回 1–3 个候选标签，不得创建标签。

- [ ] **Step 2: 实现 AI 服务边界和失败保留**

定义可替换的 AI provider 接口，保存候选标签、置信度、原因和失败信息；置信度低于 0.70、冲突候选、无法识别或服务失败进入审核队列，原始活动数据保留。

- [ ] **Step 3: 实现运营初审和管理员最终审核**

运营可以接受、取消、补充标签并提交意见，但提交后必须为 `pending_admin_review`；管理员可以确认、修正或退回，最终确认后活动变为 `active`。所有状态转换校验前置状态，非法跳转返回 409。

- [ ] **Step 4: 实现 P07 页面**

展示截图、活动字段、候选标签、置信度和错误原因；运营初审和管理员审核使用不同操作按钮；退回必须填写原因；越权操作显示无权限状态。

- [ ] **Step 5: 验证状态流转和持久化**

```powershell
python manage.py test backend.apps.reviews.tests.test_review_api -v 2
npm run type-check
npm run build
```

验证：AI 失败记录仍存在并进入待处理；运营提交后查询状态为 `pending_admin_review`；运营调用管理员确认接口得到 403；管理员确认后活动状态为 `active`；刷新页面确认评论和标签均已保存。

- [ ] **Step 6: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: add ai tagging review workflow"
```

### Task 10：用户管理和审计日志

**Files:**
- Create: `backend/apps/audit/`
- Create: `backend/apps/audit/models.py`
- Create: `backend/apps/audit/services.py`
- Create: `backend/apps/audit/views.py`
- Modify: `backend/apps/accounts/views.py`
- Modify: `backend/config/urls.py`
- Create: `frontend/src/views/UserManagementView.vue`
- Create: `frontend/src/views/AuditLogView.vue`
- Test: `backend/apps/audit/tests/test_audit_api.py`

- [ ] **Step 1: 实现用户列表、新增、编辑和停用**

实现 OpenAPI 中 `/users` 和 `/users/{userId}` 接口；只有管理员可修改角色或停用用户；停用不能物理删除用户历史关联数据。

- [ ] **Step 2: 实现审计日志记录器**

记录操作者、动作、对象类型、对象 ID、成功/失败、变更前后数据、备注和时间。至少记录登录失败、角色变更、活动归档/恢复、标签迁移/合并/停用、游戏类型停用、爬虫配置变更、任务重试和审核状态变更。

- [ ] **Step 3: 实现日志查询页**

支持按时间、操作者、动作和对象类型筛选；日志详情使用抽屉；不提供批量导出和全库下载。

- [ ] **Step 4: 验证审计可追溯性**

```powershell
python manage.py test backend.apps.audit.tests.test_audit_api -v 2
npm run type-check
npm run build
```

执行一次活动归档、标签迁移、角色变更和任务重试，重新查询日志确认每个动作都有操作者、结果和对象；普通用户和运营查询审计接口得到 403。

- [ ] **Step 5: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "feat: add user management and audit logs"
```

### Task 11：限流、软删除、防导出和错误处理补强

**Files:**
- Modify: `backend/apps/core/middleware.py`
- Create: `backend/apps/core/throttling.py`
- Modify: `backend/apps/activities/views.py`
- Modify: `backend/apps/activities/models.py`
- Modify: `backend/config/settings.py`
- Test: `backend/apps/core/tests/test_security_constraints.py`

- [ ] **Step 1: 对搜索和列表接口实施账号/IP 限流**

至少覆盖活动列表、详情、收藏列表、任务列表和审核列表；超过阈值返回 429 和 `Retry-After`，阈值放在环境配置中，不能写死在视图中。

- [ ] **Step 2: 确认软删除和归档边界**

活动和配置不物理删除；活动归档默认隐藏，管理员显式查询才可查看；历史关联、审计日志和收藏记录按 PRD 规则保留。

- [ ] **Step 3: 确认无导出和无批量下载接口**

扫描路由表和前端菜单，不出现 export、dump、download-all、batch-delete 等能力；单张截图访问仍按权限和资源 URL 规则处理，不承诺阻止浏览器原生保存。

- [ ] **Step 4: 验证异常响应一致性**

```powershell
python manage.py test backend.apps.core.tests.test_security_constraints -v 2
```

验证未认证为 401、越权为 403、资源不存在为 404、状态冲突为 409、超限为 429；所有错误均包含 `code`、`message` 和 `request_id`。

- [ ] **Step 5: 建立 Git 稳定版本**

```powershell
git add backend frontend
 git commit -m "fix: enforce rate limits soft delete and api boundaries"
```

### Task 12：前后端联调、真实数据库验证和最终回归

**Files:**
- Modify: `docs/superpowers/checklists/2026-10-17-engineering-acceptance.md`
- Create: `backend/tests/integration/`
- Create: `frontend/src/__tests__/`
- Create: `docs/api/openapi-validation.md`

- [ ] **Step 1: 使用独立 MariaDB 测试库执行迁移**

```powershell
python manage.py migrate
python manage.py check --deploy
python manage.py test -v 2
```

验证迁移可重复执行，数据库表、索引、唯一约束和外键均存在；不得使用 SQLite 替代 MariaDB 作为最终验证数据库。

- [ ] **Step 2: 执行普通用户主流程**

登录 → 查询标签树 → 组合筛选 → 查看卡片 → 查看详情 → 收藏 → 进入我的收藏 → 取消收藏。关闭前端并重新登录，确认收藏结果来自 MariaDB 而非内存状态。

- [ ] **Step 3: 执行运营主流程**

登录 → 新增活动 → 上传截图 → 编辑自己录入的活动 → 触发已配置爬虫 → 查看任务 → 重试失败记录 → 处理 AI 初审。确认运营不能修改爬虫配置、标签树、用户或管理员审核结果。

- [ ] **Step 4: 执行管理员主流程**

登录 → 最终审核 → 修正标签 → 管理标签和游戏类型 → 配置爬虫 → 归档并恢复活动 → 修改用户角色 → 查询审计日志。确认每个关键动作均能在数据库中查到日志。

- [ ] **Step 5: 执行前端构建和浏览器冒烟**

```powershell
npm run type-check
npm run build
npm run dev
```

逐页检查 P01-P11：加载、空状态、错误状态、无权限状态、表单校验、弹窗二次确认、任务进度、审核状态和刷新后的持久化结果。

- [ ] **Step 6: 执行接口契约回归**

重新运行 OpenAPI 解析和 `$ref` 校验；对每个已实现路径至少验证成功响应、未认证响应、越权响应和资源不存在响应；发现契约和实现不一致时先修正实现或契约，再重新执行全量测试。

- [ ] **Step 7: 建立最终稳定版本**

```powershell
git add backend frontend docs
 git commit -m "test: complete activity reference library regression"
git status --short
```

预期：测试通过、前端构建成功、工作区无未提交变更，最终提交作为 MVP 稳定版本。

---

## 四、规格覆盖自检

- [ ] 登录、三档角色、后端越权拒绝：Task 4。
- [ ] 标签树浏览、三级限制、多维筛选、排序：Task 5、Task 7。
- [ ] 活动卡片、详情、多图、相关活动、收藏：Task 5。
- [ ] 手动录入、编辑、截图、批量导入、归档恢复：Task 6。
- [ ] 定时配置、手动触发、任务结果、失败记录、重试、连续失败自动暂停：Task 8。
- [ ] AI 自动打标、运营初审、管理员最终确认/修正/退回：Task 9。
- [ ] 用户管理和角色变更：Task 10。
- [ ] 审计日志：Task 10。
- [ ] 限流、软删除、防批量导出/全库 dump：Task 11。
- [ ] MariaDB 数据保存和重启后读取：Task 1、Task 2、Task 12。
- [ ] P01-P11 页面：Task 3、Task 5、Task 6、Task 7、Task 8、Task 9、Task 10。
- [ ] 不实现 PRD 明确排除的评论、点赞、分享、效果数据、PDF/批量图片导出、移动端 App：所有任务均未安排这些功能。

## 五、计划自检规则

执行本计划前，必须检查：

1. 计划中的文件路径与当前目录结构一致；不存在的工程文件只在对应初始化任务中创建。
2. OpenAPI 路径、状态枚举、角色枚举和响应结构与实现测试保持一致。
3. 每个阶段都有可执行命令、预期结果和数据库保存验证。
4. 每个阶段都有 Git 稳定版本，不在测试失败时提交稳定版本。
5. 不把 SSO、真实 AI 供应商、真实外部爬虫和对象存储的具体选择伪装成已确认需求。
6. 不增加 P1 功能和 PRD 明确不做的功能。
