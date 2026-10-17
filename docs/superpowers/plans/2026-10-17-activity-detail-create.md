# 活动详情与新建活动 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为游戏活动参考库补齐活动详情查看、收藏操作和运营/管理员新建活动的前端闭环。

**Architecture:** 沿用现有 Vue 3 + TypeScript + Element Plus 前端、Django `/api/v1` API 和 JWT 会话。新增详情页与新建页作为两个独立视图，由路由元信息完成角色限制；后端继续使用现有活动详情、收藏、类型、标签和创建接口，不改动认证协议。

**Tech Stack:** Vue 3、TypeScript、Vue Router、Element Plus、Vite、Django REST 风格 JSON API、Django TestCase。

---

## 文件职责

- Modify: `frontend/src/router/index.ts`：注册详情页和新建页路由及角色元信息。
- Modify: `frontend/src/types/api.ts`：补充 `GameType`、`Tag` 和创建响应所需类型。
- Modify: `frontend/src/views/ActivityLibraryView.vue`：新增入口跳转、卡片详情跳转、按角色显示新增按钮。
- Create: `frontend/src/views/ActivityDetailView.vue`：加载并展示单个活动，处理收藏切换。
- Create: `frontend/src/views/ActivityCreateView.vue`：加载选项、校验表单并创建活动。
- Modify: `frontend/src/router/guards.ts`：确认角色不满足路由要求时回到活动库，保持现有守卫行为。
- Test: `backend/apps/activities/tests/test_write_api.py`：补充创建后可通过详情接口读取的 API 回归验证（如现有测试结构允许则扩展现有测试类）。

## Task 1: 扩展前端类型并注册路由

**Files:**
- Modify: `frontend/src/types/api.ts`
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 添加 API 选项类型**

在 `api.ts` 中定义：

```typescript
export interface GameTypeOption {
  id: string;
  name: string;
}

export interface TagOption {
  id: string;
  name: string;
  parent_id: string | null;
  level: number;
}
```

- [ ] **Step 2: 注册两个路由**

在 `router/index.ts` 引入两个新视图，并在现有布局子路由中加入：

```typescript
{
  path: "activities/new",
  name: "activity-create",
  component: ActivityCreateView,
  meta: { roles: ["operator", "admin"] },
},
{
  path: "activities/:id",
  name: "activity-detail",
  component: ActivityDetailView,
  meta: { roles: ["user", "operator", "admin"] },
},
```

将静态 `activities/new` 放在动态 `activities/:id` 之前，避免 `new` 被当作活动 ID。

- [ ] **Step 3: 运行类型检查**

运行：`npm run type-check`

预期：新路由组件尚未创建时会失败；失败用于确认下一任务需要创建视图。

## Task 2: 实现活动详情页

**Files:**
- Create: `frontend/src/views/ActivityDetailView.vue`

- [ ] **Step 1: 编写详情页数据加载逻辑**

使用 `useRoute`、`useRouter`、`onMounted` 和现有 `request`，调用：

```typescript
request<Activity>(`/activities/${route.params.id}`)
```

将返回数据保存到 `activity`，请求失败时通过 `ElMessage.error` 显示错误并允许返回活动库。

- [ ] **Step 2: 编写收藏切换逻辑**

根据 `activity.is_favorite` 选择 `POST` 或 `DELETE`：

```typescript
await request<never>(`/activities/${activity.id}/favorite`, {
  method: activity.is_favorite ? "DELETE" : "POST",
});
activity.is_favorite = !activity.is_favorite;
```

- [ ] **Step 3: 实现详情模板**

展示标题、游戏信息、状态、时间、描述、标签、截图、来源站点和来源链接；截图为空时显示空状态；提供返回按钮和收藏按钮。

- [ ] **Step 4: 运行前端检查**

运行：`npm run type-check` 和 `npm run build`

预期：通过。

## Task 3: 实现新建活动表单

**Files:**
- Create: `frontend/src/views/ActivityCreateView.vue`

- [ ] **Step 1: 定义表单状态和选项加载**

表单字段使用：

```typescript
const form = reactive({
  source_url: "",
  source_site: "manual",
  game_name: "",
  game_type_id: "",
  activity_name: "",
  description: "",
  tag_ids: [] as string[],
  screenshot: "",
});
```

页面加载时并行调用：

```typescript
const [gameTypes, tags] = await Promise.all([
  request<GameTypeOption[]>("/game-types"),
  request<TagOption[]>("/tags"),
]);
```

- [ ] **Step 2: 添加客户端校验**

提交前确保活动名称、游戏名称、来源 URL、游戏类型、至少一个标签和截图路径不为空；校验失败只显示提示，不发送请求。

- [ ] **Step 3: 提交创建请求**

调用：

```typescript
const response = await request<Activity>("/activities", {
  method: "POST",
  body: JSON.stringify(form),
});
await router.push(`/activities/${response.data.id}`);
```

提交期间使用 `submitting` 禁用按钮，避免重复创建；失败时展示 API 错误。

- [ ] **Step 4: 实现表单模板**

使用 Element Plus 表单组件完成活动名称、游戏名称、来源 URL、来源站点、游戏类型、标签多选、描述、截图路径、取消和提交按钮。

- [ ] **Step 5: 运行前端检查**

运行：`npm run type-check` 和 `npm run build`

预期：通过。

## Task 4: 接入活动库入口

**Files:**
- Modify: `frontend/src/views/ActivityLibraryView.vue`

- [ ] **Step 1: 增加路由和会话引用**

使用 `useRouter` 和 `session`，新增：

```typescript
const canCreate = computed(() =>
  session.user?.role === "operator" || session.user?.role === "admin",
);
```

- [ ] **Step 2: 连接新增活动按钮**

仅 `canCreate` 时显示按钮，点击跳转 `/activities/new`。

- [ ] **Step 3: 连接活动卡片详情**

活动卡片增加点击或详情按钮，跳转 `/activities/${activity.id}`；收藏按钮点击时阻止卡片点击事件，继续执行现有收藏逻辑。

- [ ] **Step 4: 运行前端检查**

运行：`npm run type-check` 和 `npm run build`

预期：通过。

## Task 5: 增加后端 API 回归测试

**Files:**
- Modify: `backend/apps/activities/tests/test_write_api.py`

- [ ] **Step 1: 添加创建后详情读取测试**

使用运营用户创建活动，读取返回 ID，再以普通用户调用详情接口，断言 HTTP 200、活动名称、游戏名称、标签和截图字段正确。

测试形态：

```python
def test_created_activity_can_be_loaded_by_detail_api(self):
    response = self.client.post(
        reverse("activities"),
        {
            "source_url": "https://example.com/activity-detail",
            "game_name": "测试游戏",
            "game_type_id": self.game_type.pk,
            "activity_name": "详情测试活动",
            "tag_ids": [self.tag.pk],
            "screenshot": "screenshots/detail.png",
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token_for(self.operator)}",
    )
    activity_id = response.json()["data"]["id"]
    detail = self.client.get(
        reverse("activity-detail", args=[activity_id]),
        HTTP_AUTHORIZATION=f"Bearer {token_for(self.user)}",
    )
    self.assertEqual(detail.status_code, 200)
    self.assertEqual(detail.json()["data"]["activity_name"], "详情测试活动")
```

- [ ] **Step 2: 运行后端活动测试**

运行：`py -3.12 manage.py test apps.activities -v 2`，工作目录为 `backend`。

预期：全部通过。

## Task 6: 浏览器端到端验证

**Files:** 无新增文件。

- [ ] **Step 1: 启动后端和前端开发服务**

确认 Django 在 `127.0.0.1:8000`，Vite 使用已配置代理的端口。

- [ ] **Step 2: 验证普通用户流程**

使用现有测试账号登录，确认活动库可打开；点击活动卡片进入详情；确认收藏和取消收藏请求正常；访问 `/activities/new` 后被路由守卫带回活动库。

- [ ] **Step 3: 验证运营创建流程**

使用运营账号进入 `/activities/new`，确认类型和标签动态加载，提交完整表单后跳转详情并显示创建内容。

- [ ] **Step 4: 运行最终检查**

运行：

```powershell
npm run type-check
npm run build
py -3.12 manage.py test apps.accounts apps.activities -v 2
```

预期：全部通过，浏览器控制台无新增错误。

- [ ] **Step 5: 提交稳定版本**

```powershell
git add frontend/src/router/index.ts frontend/src/types/api.ts frontend/src/views/ActivityLibraryView.vue frontend/src/views/ActivityDetailView.vue frontend/src/views/ActivityCreateView.vue backend/apps/activities/tests/test_write_api.py docs/superpowers/plans/2026-10-17-activity-detail-create.md
git commit -m "feat: add activity detail and creation flow"
```
