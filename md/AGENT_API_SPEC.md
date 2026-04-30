# Agent API 规格说明

> 版本：v1.0
> 日期：2026-04-29
> 状态：开发前定稿
> 适用范围：AgentNow 第一版智能体功能接口设计

---

## 一、文档目标

这份文档用于定义 AgentNow 第一版智能体功能的 API 规格，供后端开发、前端联调、大模型协作开发共同使用。

它主要回答下面几个问题：

1. 接口到底有哪些
2. 每个接口的用途是什么
3. 请求参数和返回结构怎么约定
4. 员工侧和管理端的权限边界怎么收口
5. 哪些状态字段需要前后端共同遵守

这份文档写的是“正式开发口径”，不是泛泛的接口建议。

---

## 二、使用边界

为了避免开发时看混，这几份文档分工如下：

1. `AGENT_IMPLEMENTATION_SPEC.md`
   - 负责整体目标、边界、架构、模块和业务方案

2. `AGENT_PPT_ASSISTANT_TEMPLATE_V1.md`
   - 负责 `ppt_assistant` 模板配置、提示词和交互规则

3. `AGENT_IMPLEMENTATION_TASKS.md`
   - 负责开发顺序和每一步给大模型的执行提示词

4. `AGENT_API_SPEC.md`
   - 负责 HTTP API 设计、请求响应格式、状态定义和接口边界

5. `backend/data/database.sql`
   - 负责数据库最终结构

如果几份文档之间有冲突，处理优先级建议如下：

1. 数据表结构以 `database.sql` 为准
2. 接口形态以本文件为准
3. 业务边界以 `AGENT_IMPLEMENTATION_SPEC.md` 为准
4. 模板交互细节以 `AGENT_PPT_ASSISTANT_TEMPLATE_V1.md` 为准

---

## 三、整体约定

### 3.1 API 前缀

项目当前后端配置使用：

```text
/api/v1
```

因此本文所有接口均以 `/api/v1` 为前缀。

### 3.2 认证方式

除登录等已有认证接口外，本文中的智能体接口默认都需要登录态。

认证方式沿用当前项目：

```text
Authorization: Bearer {token}
```

### 3.3 返回结构

项目当前接口风格主要采用统一包装：

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {}
}
```

第一版智能体接口除“文件下载”外，统一遵守这个返回结构。

### 3.4 时间格式

所有时间字段统一使用：

```text
YYYY-MM-DDTHH:mm:ss
```

如果框架默认返回时区信息，前后端统一按 ISO 8601 处理。

### 3.5 ID 类型

数据库主键统一为 `BIGINT`，接口层统一按整数处理。

### 3.6 第一版流式输出约定

第一版建议先不做流式输出，统一走普通 JSON 响应。

原因：

1. 先把链路和状态做稳
2. 先降低前后端联调复杂度
3. 后续如果要补流式输出，再增量扩展

---

## 四、权限约定

### 4.1 员工侧权限

员工侧接口默认要求当前登录用户只能访问自己的智能体数据。

建议使用以下权限码：

1. `agent:use`
2. `agent:history:view`

### 4.2 管理端权限

管理端接口默认要求系统管理员或超级管理员权限。

建议使用以下权限码：

1. `agent:template:query`
2. `agent:template:create`
3. `agent:template:update`
4. `agent:template:enable`
5. `agent:admin:view`

### 4.3 最重要的权限边界

下面这条是第一版智能体功能最重要的后端约束：

1. 员工侧接口不得允许前端传入任意 `profile_name`
2. 后端必须始终通过当前登录用户反查 `user_agents.hermes_profile`
3. 管理端如果允许跨员工查看，必须单独接口、单独权限、单独审计

---

## 五、公共数据结构

这一节不是代码 Schema，而是接口层统一字段约定。

### 5.1 `AgentTemplateSimple`

用于智能体列表和模板简要信息展示。

```json
{
  "id": 1,
  "code": "ppt_assistant",
  "name": "企业 PPT 助手",
  "description": "用于公司介绍、产品宣讲、汇报型 PPT 的内容生成与文件输出",
  "status": 1,
  "is_default": true,
  "version": 1
}
```

### 5.2 `UserAgentResponse`

用于返回员工已开通的智能体实例。

```json
{
  "id": 1,
  "user_id": 12,
  "template_id": 1,
  "display_name": "企业 PPT 助手",
  "hermes_profile": "corp_1_user_12",
  "template_version": 1,
  "agent_status": 1,
  "enabled_at": "2026-04-29T10:00:00",
  "last_used_at": "2026-04-29T10:10:00",
  "template": {
    "id": 1,
    "code": "ppt_assistant",
    "name": "企业 PPT 助手",
    "description": "用于公司介绍、产品宣讲、汇报型 PPT 的内容生成与文件输出",
    "status": 1,
    "is_default": true,
    "version": 1
  }
}
```

### 5.3 `ConversationResponse`

```json
{
  "id": 101,
  "user_agent_id": 1,
  "title": "公司介绍 10 页 PPT",
  "current_stage": "outline_draft",
  "status": 1,
  "outline_confirmed": false,
  "template_confirmed": false,
  "final_generation_confirmed": false,
  "message_count": 4,
  "latest_user_input": "帮我做一份公司介绍的 10 页 PPT",
  "final_file_id": null,
  "started_at": "2026-04-29T10:00:00",
  "last_message_at": "2026-04-29T10:06:00",
  "completed_at": null
}
```

### 5.4 `GeneratedFileResponse`

```json
{
  "id": 201,
  "conversation_id": 101,
  "file_type": "pptx",
  "file_name": "公司介绍_PPT_v1.pptx",
  "file_path": "/data/agent-files/2026/04/29/公司介绍_PPT_v1.pptx",
  "template_name": "公司标准模板",
  "version_no": 1,
  "generation_status": 1,
  "error_message": null,
  "created_at": "2026-04-29T10:20:00"
}
```

### 5.5 状态枚举约定

#### 模板状态 `agent_templates.status`

1. `0`：草稿
2. `1`：启用
3. `2`：停用

#### 员工智能体状态 `user_agents.agent_status`

1. `0`：待开通
2. `1`：可用
3. `2`：已停用
4. `3`：开通失败

#### 会话状态 `agent_conversations.status`

1. `0`：草稿
2. `1`：进行中
3. `2`：已完成
4. `3`：已归档
5. `4`：失败

#### 会话阶段 `agent_conversations.current_stage`

1. `chatting`：普通对话中
2. `outline_draft`：大纲草拟中
3. `outline_confirmed`：大纲已确认
4. `template_select`：模板选择中
5. `final_generating`：正式文件生成中
6. `completed`：已完成

#### 文件生成状态 `agent_generated_files.generation_status`

1. `0`：生成中
2. `1`：成功
3. `2`：失败

---

## 六、员工侧接口

员工侧接口只允许操作当前登录用户自己的智能体。

### 6.1 获取我的智能体列表

- 方法：`GET`
- 路径：`/api/v1/agents/me`
- 权限：`agent:use`
- 说明：获取当前员工已开通的智能体实例列表

#### 请求参数

无。

#### 响应示例

```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": 1,
      "user_id": 12,
      "template_id": 1,
      "display_name": "企业 PPT 助手",
      "hermes_profile": "corp_1_user_12",
      "template_version": 1,
      "agent_status": 1,
      "enabled_at": "2026-04-29T10:00:00",
      "last_used_at": "2026-04-29T10:10:00",
      "template": {
        "id": 1,
        "code": "ppt_assistant",
        "name": "企业 PPT 助手",
        "description": "用于公司介绍、产品宣讲、汇报型 PPT 的内容生成与文件输出",
        "status": 1,
        "is_default": true,
        "version": 1
      }
    }
  ]
}
```

### 6.2 首次开通默认智能体

- 方法：`POST`
- 路径：`/api/v1/agents/me/enable`
- 权限：`agent:use`
- 说明：员工第一次进入智能体模块时调用，自动创建或绑定 Hermes Profile，并开通默认模板

#### 请求体

第一版建议不需要复杂入参，可为空对象：

```json
{}
```

#### 响应示例

```json
{
  "code": 200,
  "message": "开通成功",
  "data": {
    "user_agent": {
      "id": 1,
      "user_id": 12,
      "template_id": 1,
      "display_name": "企业 PPT 助手",
      "hermes_profile": "corp_1_user_12",
      "template_version": 1,
      "agent_status": 1,
      "enabled_at": "2026-04-29T10:00:00",
      "last_used_at": null
    },
    "created_profile": true
  }
}
```

### 6.3 获取我的智能体详情

- 方法：`GET`
- 路径：`/api/v1/agents/me/{agent_id}`
- 权限：`agent:use`
- 说明：获取某个员工智能体实例的详细信息

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `agent_id` | int | 是 | 员工智能体 ID |

#### 响应内容建议

建议在 `UserAgentResponse` 基础上补充：

1. 模板快照摘要
2. 模板可用工具
3. 当前最近会话信息

### 6.4 发送消息

- 方法：`POST`
- 路径：`/api/v1/agents/me/{agent_id}/chat`
- 权限：`agent:use`
- 说明：向当前员工的智能体发送消息并获取回复

#### 设计说明

第一版建议仍然只保留一个聊天入口，不额外拆“确认大纲”“确认模板”成独立接口，而是在请求体中用 `action_type` 表示当前动作。

这样做的好处：

1. 前端交互更简单
2. 后端状态收口更集中
3. 后续如果需要拆接口，再演进也不晚

#### 请求体

```json
{
  "conversation_id": 101,
  "message": "帮我做一份公司介绍的 10 页 PPT",
  "action_type": "message",
  "metadata": {
    "page_count": 10,
    "audience": "客户",
    "scene": "客户拜访"
  }
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `conversation_id` | int \| null | 否 | 会话 ID，不传表示新建会话 |
| `message` | string | 否 | 用户输入文本，动作类请求时可为空 |
| `action_type` | string | 是 | 当前动作类型 |
| `metadata` | object | 否 | 辅助元数据 |

#### `action_type` 取值建议

1. `message`：普通消息
2. `confirm_outline`：确认当前大纲
3. `revise_outline`：要求重新整理大纲
4. `confirm_template`：确认模板风格
5. `confirm_generation`：确认进入正式生成
6. `revise_content`：要求修改已有内容

#### 响应示例

```json
{
  "code": 200,
  "message": "发送成功",
  "data": {
    "conversation": {
      "id": 101,
      "user_agent_id": 1,
      "title": "公司介绍 10 页 PPT",
      "current_stage": "outline_draft",
      "status": 1,
      "outline_confirmed": false,
      "template_confirmed": false,
      "final_generation_confirmed": false,
      "message_count": 2,
      "latest_user_input": "帮我做一份公司介绍的 10 页 PPT",
      "final_file_id": null,
      "started_at": "2026-04-29T10:00:00",
      "last_message_at": "2026-04-29T10:01:00",
      "completed_at": null
    },
    "assistant_message": {
      "role": "assistant",
      "content": "为了把这份 PPT 做得更贴合你的实际场景，我先确认几个关键信息……"
    },
    "structured_result": null
  }
}
```

#### `structured_result` 约定

当系统已经进入大纲或结构化内容阶段时，建议在 `data.structured_result` 返回结构化内容，便于前端渲染。

例如：

```json
{
  "type": "ppt_outline",
  "title": "公司介绍 PPT",
  "slides": [
    {
      "index": 1,
      "title": "封面",
      "bullets": ["公司名称", "宣传语"]
    }
  ]
}
```

### 6.5 获取会话列表

- 方法：`GET`
- 路径：`/api/v1/agents/me/{agent_id}/conversations`
- 权限：`agent:history:view`
- 说明：获取当前员工某个智能体的会话列表

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | int | 否 | 按会话状态筛选 |
| `limit` | int | 否 | 返回条数，默认 20 |

#### 响应示例

```json
{
  "code": 200,
  "message": "获取成功",
  "data": [
    {
      "id": 101,
      "user_agent_id": 1,
      "title": "公司介绍 10 页 PPT",
      "current_stage": "outline_confirmed",
      "status": 1,
      "outline_confirmed": true,
      "template_confirmed": false,
      "final_generation_confirmed": false,
      "message_count": 8,
      "latest_user_input": "这一页再正式一点",
      "final_file_id": null,
      "started_at": "2026-04-29T10:00:00",
      "last_message_at": "2026-04-29T10:08:00",
      "completed_at": null
    }
  ]
}
```

### 6.6 获取会话详情

- 方法：`GET`
- 路径：`/api/v1/agents/me/{agent_id}/conversations/{id}`
- 权限：`agent:history:view`
- 说明：获取某个会话的完整详情

#### 响应内容建议

建议返回：

1. 会话基础信息
2. 消息列表
3. 当前结构化结果
4. 已生成文件列表

#### 响应示例

```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "conversation": {
      "id": 101,
      "user_agent_id": 1,
      "title": "公司介绍 10 页 PPT",
      "current_stage": "template_select",
      "status": 1,
      "outline_confirmed": true,
      "template_confirmed": false,
      "final_generation_confirmed": false,
      "message_count": 10,
      "latest_user_input": "我想用更正式的模板",
      "final_file_id": null,
      "started_at": "2026-04-29T10:00:00",
      "last_message_at": "2026-04-29T10:10:00",
      "completed_at": null
    },
    "messages": [],
    "structured_result": {
      "type": "ppt_outline",
      "slides": []
    },
    "files": []
  }
}
```

### 6.7 生成正式 PPT

- 方法：`POST`
- 路径：`/api/v1/agents/me/{agent_id}/generate-ppt`
- 权限：`agent:use`
- 说明：当大纲、风格和正式生成都确认后，触发最终 `.pptx` 生成

#### 请求体

```json
{
  "conversation_id": 101,
  "template_name": "公司标准模板",
  "regenerate": false
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `conversation_id` | int | 是 | 会话 ID |
| `template_name` | string | 否 | 选择的母版名称 |
| `regenerate` | bool | 否 | 是否为重新生成 |

#### 响应示例

```json
{
  "code": 200,
  "message": "PPT 生成成功",
  "data": {
    "conversation_id": 101,
    "file": {
      "id": 201,
      "conversation_id": 101,
      "file_type": "pptx",
      "file_name": "公司介绍_PPT_v1.pptx",
      "file_path": "/data/agent-files/2026/04/29/公司介绍_PPT_v1.pptx",
      "template_name": "公司标准模板",
      "version_no": 1,
      "generation_status": 1,
      "error_message": null,
      "created_at": "2026-04-29T10:20:00"
    }
  }
}
```

### 6.8 下载生成文件

- 方法：`GET`
- 路径：`/api/v1/agents/me/{agent_id}/files/{file_id}`
- 权限：`agent:use`
- 说明：下载当前员工自己的生成文件

#### 返回说明

该接口不返回统一 JSON，而是直接返回文件流。

建议响应头：

```text
Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation
Content-Disposition: attachment; filename="公司介绍_PPT_v1.pptx"
```

---

## 七、管理端接口

管理端接口用于模板配置、模板发布、模板同步和员工开通情况查看。

### 7.1 获取模板列表

- 方法：`GET`
- 路径：`/api/v1/agent-templates`
- 权限：`agent:template:query`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `status` | int | 否 | 按状态筛选 |
| `keyword` | string | 否 | 按名称或编码搜索 |

### 7.2 新建模板

- 方法：`POST`
- 路径：`/api/v1/agent-templates`
- 权限：`agent:template:create`

#### 请求体

```json
{
  "code": "ppt_assistant",
  "name": "企业 PPT 助手",
  "description": "用于公司介绍、产品宣讲、汇报型 PPT 的内容生成与文件输出",
  "role_prompt": "你是企业内部的 PPT 助手……",
  "system_prompt": "你是企业内部的 PPT 助手，负责帮助员工快速完成……",
  "welcome_message": "你好，我是企业 PPT 助手。",
  "knowledge_scope": "category",
  "knowledge_categories": [
    "ppt/company_intro",
    "ppt/brand_guideline",
    "ppt/product_materials",
    "ppt/industry_cases"
  ],
  "tool_policy": {
    "knowledge_search": true,
    "document_read": true,
    "web_search": false,
    "ppt_generate": true
  },
  "output_rules": {
    "outline_first": true,
    "confirm_before_generate": true
  },
  "confirmation_rules": {
    "need_outline_confirm": true,
    "need_template_confirm": true,
    "need_final_confirm": true
  },
  "interaction_rules": {
    "ask_for_missing_info_first": true
  },
  "workflow_hints": {
    "steps": [
      "先补问",
      "再查资料",
      "再出大纲",
      "再确认",
      "最后生成文件"
    ]
  },
  "is_default": true
}
```

### 7.3 获取模板详情

- 方法：`GET`
- 路径：`/api/v1/agent-templates/{id}`
- 权限：`agent:template:query`

#### 响应内容建议

建议返回：

1. 模板主数据
2. 当前版本号
3. 最近版本记录
4. 是否默认模板

### 7.4 更新模板

- 方法：`PUT`
- 路径：`/api/v1/agent-templates/{id}`
- 权限：`agent:template:update`
- 说明：更新模板草稿内容，不等于发布

#### 说明

第一版建议把“更新”和“发布”拆开：

1. `PUT` 只改当前模板草稿
2. `publish` 才生成版本快照

这样做更稳，也更符合后台使用习惯。

### 7.5 发布模板

- 方法：`POST`
- 路径：`/api/v1/agent-templates/{id}/publish`
- 权限：`agent:template:update`

#### 请求体

```json
{
  "version_label": "v1.0",
  "change_summary": "补充 PPT 大纲确认规则，默认关闭网页搜索"
}
```

#### 响应内容建议

返回：

1. 当前模板信息
2. 新版本号
3. 发布快照摘要

### 7.6 启用模板

- 方法：`POST`
- 路径：`/api/v1/agent-templates/{id}/enable`
- 权限：`agent:template:enable`

### 7.7 停用模板

- 方法：`POST`
- 路径：`/api/v1/agent-templates/{id}/disable`
- 权限：`agent:template:enable`

### 7.8 同步模板到已开通员工

- 方法：`POST`
- 路径：`/api/v1/agent-templates/{id}/sync`
- 权限：`agent:template:update`

#### 请求体

```json
{
  "sync_mode": "all_enabled_users"
}
```

#### `sync_mode` 取值建议

1. `all_enabled_users`：同步给所有已开通员工
2. `selected_users`：只同步给指定员工

如果使用 `selected_users`，补充：

```json
{
  "sync_mode": "selected_users",
  "user_ids": [12, 18, 21]
}
```

### 7.9 查看员工智能体开通情况

- 方法：`GET`
- 路径：`/api/v1/agent-admin/users`
- 权限：`agent:admin:view`

#### 查询参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `keyword` | string | 否 | 员工姓名/登录名搜索 |
| `template_id` | int | 否 | 按模板筛选 |
| `agent_status` | int | 否 | 按开通状态筛选 |

#### 响应内容建议

建议每条记录至少返回：

1. 用户基础信息
2. 智能体实例信息
3. Hermes Profile
4. 最近使用时间
5. 当前模板版本

### 7.10 为指定员工开通智能体

- 方法：`POST`
- 路径：`/api/v1/agent-admin/users/{user_id}/provision`
- 权限：`agent:admin:view`

#### 请求体

```json
{
  "template_id": 1,
  "force_recreate_profile": false
}
```

---

## 八、内部服务边界

这一节不是对外 HTTP API，而是为了避免后端实现时把 Hermes 调用散落在各处。

### 8.1 建议统一封装的内部服务

建议至少封装以下内部方法：

1. `ensure_profile(user)`
2. `apply_template_snapshot(profile, snapshot)`
3. `chat(profile, payload)`
4. `list_conversations(profile)`
5. `load_conversation(profile, conversation_id)`
6. `generate_ppt(conversation, template_name)`

### 8.2 约束

1. 路由层不直接拼 Hermes 请求
2. 模板快照组装尽量在 service 层完成
3. PPT 文件生成单独 service，不和聊天 service 混在一起

---

## 九、错误码与错误口径

第一版建议先沿用 HTTP 状态码 + `detail` / `message` 的简单策略，不要急着自定义复杂业务码体系。

### 9.1 常见错误

| HTTP 状态码 | 场景 | 建议文案 |
|-------------|------|----------|
| `400` | 参数错误、当前状态不允许执行 | 请求参数不合法 |
| `401` | 未登录或登录失效 | 登录状态已失效 |
| `403` | 无权限、越权访问他人智能体 | 无权限访问该资源 |
| `404` | 智能体、模板、会话、文件不存在 | 资源不存在 |
| `409` | 状态冲突，如模板重复发布 | 当前状态不允许执行该操作 |
| `500` | 系统异常、Hermes 调用失败、文件生成失败 | 系统处理失败，请稍后重试 |

### 9.2 智能体特有错误场景

建议重点覆盖下面这些错误：

1. 员工智能体不存在
2. 模板不存在或已停用
3. 会话不属于当前员工
4. Hermes Profile 创建失败
5. Hermes 对话调用失败
6. 大纲未确认就要求正式生成
7. 文件不存在或无权限下载
8. 模板同步时目标员工实例不存在

### 9.3 生成 PPT 前的状态校验

`POST /api/v1/agents/me/{agent_id}/generate-ppt` 调用前，后端建议至少校验：

1. `conversation_id` 是否存在
2. 会话是否属于当前员工
3. `outline_confirmed` 是否为 `true`
4. `template_confirmed` 是否为 `true`
5. `final_generation_confirmed` 是否为 `true`

如果不满足，直接返回 `400` 或 `409`，不要硬生成。

---

## 十、接口实现顺序建议

如果要按最稳的方式推进，建议接口按下面顺序落地：

1. `GET /api/v1/agents/me`
2. `POST /api/v1/agents/me/enable`
3. `GET /api/v1/agents/me/{agent_id}`
4. `POST /api/v1/agents/me/{agent_id}/chat`
5. `GET /api/v1/agents/me/{agent_id}/conversations`
6. `GET /api/v1/agents/me/{agent_id}/conversations/{id}`
7. 管理端模板 CRUD
8. 模板发布 / 启停 / 同步
9. `POST /api/v1/agents/me/{agent_id}/generate-ppt`
10. `GET /api/v1/agents/me/{agent_id}/files/{file_id}`

这个顺序和当前开发执行文档保持一致：先打通员工开通和对话，再补模板后台，最后接最终文件生成。

---

## 十一、前后端联调注意事项

### 11.1 不要让前端持有 `profile_name`

前端页面不需要知道也不应该编辑 `hermes_profile`，最多只用于只读展示。

### 11.2 会话标题允许后端自动生成

第一版建议：

1. 用户不手动命名会话
2. 后端根据首轮消息自动生成标题

### 11.3 结构化结果和自然语言结果同时返回

为了让前端更好展示，建议聊天接口在适当阶段同时返回：

1. `assistant_message`
2. `structured_result`

### 11.4 生成文件后要回写会话

正式文件生成成功后，建议：

1. 新增 `agent_generated_files`
2. 更新 `agent_conversations.final_file_id`
3. 视情况把 `current_stage` 更新为 `completed`

---

## 十二、结论

第一版 Agent API 设计的核心原则只有三条：

1. 员工侧接口一律收口到“当前用户自己的智能体”
2. 模板与会话状态尽量显式化，不靠猜
3. 先把非流式、可联调、可落库的版本做稳

后续如果要做流式输出、更多模板类型、流程编排器，再在这份 API 规格上继续演进。

---

**文档位置：** `md/AGENT_API_SPEC.md`
