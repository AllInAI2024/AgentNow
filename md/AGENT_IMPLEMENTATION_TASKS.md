# Agent 开发执行文档

> 版本：v2.0
> 日期：2026-04-29
> 状态：开发前定稿
> 适用范围：面向大模型协作开发的 AgentNow 智能体功能执行文档

---

## 一、文档目标

这份文档不是泛泛的任务清单，而是一份**可以直接拿给大模型协作开发使用的执行文档**。

它要解决三件事：

1. 把第一版智能体功能的需求和边界写清楚
2. 把开发过程中容易模糊、容易反复讨论的细节提前定下来
3. 把整个开发拆成一小步一小步的执行计划，并给出每一步可直接使用的开发提示词

文档写法尽量贴近真实研发协作，不用太重的 AI 术语，重点是让开发过程更稳，减少返工。

为了后续开发不混淆，这份文档的定位也固定下来：

1. 这份文档负责“怎么一步一步开发”
2. 总体范围和边界，以 `AGENT_IMPLEMENTATION_SPEC.md` 为准
3. `ppt_assistant` 的模板配置细节，以 `AGENT_PPT_ASSISTANT_TEMPLATE_V1.md` 为准
4. 数据库真实结构，以 `backend/data/database.sql` 为准

---

## 二、这次到底要做什么

### 2.1 第一版目标

在 AgentNow 现有“权限管理 + Hermes 管理 + 知识库管理”的基础上，补齐员工侧智能体能力，并先落地一个首个业务案例：`ppt_assistant`。

第一版要实现的结果是：

1. 企业员工可以进入自己的智能体
2. 每个员工有自己独立的 Hermes Profile
3. 员工之间的记忆严格隔离
4. 企业公共知识可以共享给所有员工智能体使用
5. 超级管理员可以在后台维护智能体模板
6. `ppt_assistant` 能帮助用户完成从需求澄清到最终 `.pptx` 生成的闭环

### 2.2 第一版不做什么

为了控制复杂度，第一版明确不做下面这些能力：

1. 不做通用低代码工作流编排器
2. 不做图形化流程设计器
3. 不做任意业务场景零代码拼装
4. 不做复杂多模板联动作业
5. 不做高度创意化的 PPT 自动设计

### 2.3 第一版产品定位

第一版定位为：

**有一定配置能力的智能体模板平台**

它不是单纯 Prompt 管理，也不是完整流程引擎，而是：

1. 后台可配置模板
2. 支持知识范围配置
3. 支持工具白名单配置
4. 支持模板版本和快照
5. 支持围绕模板跑通业务闭环

---

## 三、已经确定的核心原则

### 3.1 Hermes 不改造

AgentNow 不去改 Hermes 源码，只通过 Hermes 原生能力接入：

1. Profile
2. API Server / Responses API
3. MEMORY.md / USER.md
4. MCP
5. 内置知识能力

### 3.2 一个员工一个 Profile

每个员工固定绑定一个 Hermes Profile。

建议命名规则：

```text
corp_{tenant_id}_user_{user_id}
```

当前即使是单租户，也保留 `tenant_id` 位，避免未来重构。

### 3.3 记忆隔离靠 Hermes，不靠 AgentNow 自己造一套

AgentNow 不自己维护员工长期记忆。

AgentNow 只负责：

1. 员工与 Profile 的映射
2. 员工只能访问自己的 Profile
3. 管理端才允许跨员工查看

### 3.4 公共知识走共享知识库

公共知识不进个人记忆，统一放共享知识库。

适合进入共享知识库的内容：

1. 公司介绍
2. 品牌规范
3. 产品资料
4. 客户案例
5. 行业方案
6. PPT 模板规范

### 3.5 模板、Skill、Tool 的统一定义

为了避免后面讨论混乱，统一按下面方式理解：

1. **模板**：定义岗位智能体怎么工作
2. **Skill**：可选的专业方法模块
3. **Tool**：真正执行动作的能力

第一版里：

1. 模板是主角
2. Tool 必须先接好
3. Skill 可以后置

### 3.7 术语口径与产品借鉴（用于引导后续开发）

为避免“Agent 这个词各说各话”，后续研发与大模型协作默认按 `md/AGENT_GLOSSARY.md` 的对照口径执行。

同时，第一版产品架构建议吸收 Hermes WebUI 的产品思路（不借鉴技术栈），优先级如下：

1. 运行态可见性
   - 会话阶段、确认点、生成状态、失败原因必须在界面上可见
   - 文件产物是一等对象：版本、下载、重试、记录完整

2. 动作与消息分离
   - “确认大纲/确认模板/生成/重试”是动作，不伪装成用户消息
   - 动作要能驱动会话状态流转，并落库可追踪

3. 渐进式披露
   - 默认让用户关注对话与产物
   - 来源引用、工具执行摘要、诊断信息允许折叠，但必须可查看

4. 澄清与确认产品化
   - 先补问，再输出；先大纲，再定稿；关键节点必须显式确认
   - 避免固定问卷式交互，按缺失信息动态追问

### 3.6 PPT 最终文件不能只靠提示词

如果目标是产出 `.pptx`，必须按下面分工：

1. 模板负责工作方式
2. Hermes 负责理解需求、查资料、生成内容
3. AgentNow 后端的 PPT 生成服务负责最终文件输出

---

## 四、第一版业务范围写死的部分

这一部分是为了让大模型开发时少猜、少脑补。

### 4.1 首个模板

第一版只正式上线一个模板：

1. `ppt_assistant`

后台结构要支持多个模板，但首个上线模板只做这一个。

### 4.2 `ppt_assistant` 的主要场景

第一版只重点支持：

1. 公司介绍 PPT
2. 产品介绍 PPT
3. 售前宣讲 PPT
4. 内部汇报 PPT
5. 简单方案说明 PPT

### 4.3 `ppt_assistant` 的输出节奏

默认节奏固定为：

1. 先补问
2. 再查资料
3. 再出大纲
4. 用户确认大纲
5. 再补逐页内容
6. 再确认风格和模板
7. 最后生成正式文件

### 4.4 用户确认点

第一版至少保留三个确认点：

1. 大纲确认
2. 模板风格确认
3. 正式生成确认

### 4.5 外部网页搜索

第一版建议：

1. 默认关闭
2. 后台可配置开启
3. 就算开启，也只能作为补充信息源，不能覆盖企业知识库

### 4.6 文件生成策略

第一版建议：

1. 支持生成 `.pptx`
2. 优先采用企业标准母版
3. 先做结构化排版，不追求复杂视觉创意

---

## 五、第一版功能需求明细

### 5.1 员工侧能力

员工侧必须具备下面这些能力：

1. 进入“我的智能体”
2. 查看自己可用的智能体模板实例
3. 首次使用时自动开通
4. 进入聊天页
5. 与自己的智能体连续对话
6. 查看自己的历史会话
7. 基于历史会话继续修改
8. 下载已生成的 PPT 文件

### 5.2 管理员侧能力

管理员侧必须具备下面这些能力：

1. 查看模板列表
2. 新增模板
3. 编辑模板
4. 启用/停用模板
5. 配置知识范围
6. 配置工具白名单
7. 配置提示词和欢迎语
8. 配置确认规则
9. 查看模板版本
10. 决定模板更新是否同步给已开通员工

### 5.3 模板能力

模板至少需要包含下面这些配置：

1. 模板基础信息
2. 模板描述
3. 角色说明
4. 系统提示词
5. 欢迎语
6. 知识范围
7. 工具策略
8. 输出要求
9. 用户确认规则
10. 模板版本
11. 模板快照
12. 扩展预留字段

### 5.4 会话能力

第一版会话能力要求：

1. 支持多轮对话
2. 支持历史列表
3. 支持按会话继续生成
4. 支持把结构化结果缓存到本地
5. 支持记录文件生成结果

### 5.5 PPT 生成能力

第一版 PPT 生成能力要求：

1. 根据确认后的内容生成 `.pptx`
2. 允许选择标准模板
3. 每一页支持标题、副标题、要点、备注
4. 允许后续基于已有结果继续修改
5. 失败后支持重试

---

## 六、详细业务规则

### 6.1 员工首次进入规则

当员工第一次进入智能体模块时：

1. 系统检查 `user_agents` 是否已有记录
2. 如果没有，则检查 `users.hermes_profile`
3. 如果没有 Hermes Profile，则自动创建
4. 自动绑定默认模板 `ppt_assistant`
5. 生成 `user_agents` 记录
6. 返回员工可用智能体列表

### 6.2 员工对话规则

员工发起对话时：

1. 员工侧接口不能接受外部传入任意 `profile_name`
2. 后端必须从当前登录用户反查绑定的 Profile
3. 后端根据 `user_agent` 和模板快照组装请求
4. 再调用 Hermes

### 6.3 模板更新规则

模板更新时：

1. 默认不直接污染历史会话
2. 员工开通后保留模板快照
3. 管理员可选择：
   - 只影响新开通员工
   - 同步到已开通员工

### 6.4 知识引用规则

涉及企业事实时：

1. 先查企业知识库
2. 有依据就尽量沿用资料原意
3. 没依据就明确说明是通用建议
4. 不允许编造公司事实

### 6.5 正式生成规则

生成正式 `.pptx` 之前，必须至少确认：

1. 页数
2. 大纲
3. 风格或模板

### 6.6 修改规则

如果用户要求修改：

1. 小改动优先局部修改
2. 结构变化很大时，再建议重做大纲
3. 不要动不动整份重写

### 6.7 管理端查看规则

1. 员工只能看自己的会话
2. 管理员可以看模板和开通情况
3. 跨员工查看敏感内容时要保留审计

---

## 七、数据模型要求

### 7.1 `agent_templates`

建议字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `code` | 模板编码 |
| `name` | 模板名称 |
| `description` | 模板说明 |
| `role_prompt` | 角色说明 |
| `system_prompt` | 系统提示词 |
| `welcome_message` | 欢迎语 |
| `knowledge_scope` | 知识范围类型 |
| `knowledge_categories` | 知识分类 JSON |
| `tool_policy` | 工具策略 JSON |
| `output_rules` | 输出要求 JSON |
| `confirmation_rules` | 确认规则 JSON |
| `interaction_rules` | 关键交互规则 JSON |
| `workflow_hints` | 轻量流程提示 JSON |
| `status` | 草稿 / 启用 / 停用 |
| `is_default` | 是否默认 |
| `version` | 当前版本号 |
| `created_by` | 创建人 |
| `updated_by` | 更新人 |

### 7.1.1 数据库落地说明（已写入 `database.sql`）

为了让后续开发不在中途反复改表，第一版智能体功能已经在 `backend/data/database.sql` 中按 MySQL 结构设计了 6 张核心表：

1. `agent_templates`：智能体模板主表
2. `agent_template_versions`：模板版本快照表
3. `user_agents`：员工智能体开通表
4. `agent_conversations`：智能体会话表
5. `agent_generated_files`：智能体生成文件表
6. `agent_operation_logs`：智能体操作日志表

这 6 张表覆盖了第一版最关键的数据闭环：模板配置、模板发布、员工开通、会话状态、文件产物、运营审计。

### 7.1.2 表关系说明

第一版核心关系建议按下面理解：

1. `users (1) -> (N) user_agents`
2. `agent_templates (1) -> (N) agent_template_versions`
3. `agent_templates (1) -> (N) user_agents`
4. `user_agents (1) -> (N) agent_conversations`
5. `agent_conversations (1) -> (N) agent_generated_files`
6. `users (1) -> (N) agent_operation_logs`

关系设计重点：

1. 用户和模板是多对多关系，通过 `user_agents` 承载
2. 会话强绑定 `user_agent`，避免后续权限串线
3. 文件强绑定会话和用户，方便追踪与下载控制
4. 日志单独成表，便于审计和排障

### 7.1.3 关键字段设计理由

为了方便开发时理解为什么这么建，关键字段理由如下：

1. `agent_templates.interaction_rules`
   - 第一版虽然不是流程引擎，但要把关键交互规则沉淀成配置

2. `agent_templates.workflow_hints`
   - 为后续升级流程编排预留，不影响第一版落地

3. `user_agents.config_snapshot`
   - 模板改了以后，历史员工实例不会被直接污染

4. `agent_conversations.current_stage`
   - 记录当前处于补问/大纲/确认/生成哪个阶段，方便前端和排障

5. `agent_conversations.outline_confirmed/template_confirmed/final_generation_confirmed`
   - 用显式布尔字段确保关键确认点可追踪，不靠文本猜测

6. `agent_generated_files.version_no`
   - 同一会话可能多次生成文件，方便版本管理与回溯

7. `agent_operation_logs.details`
   - 存 JSON 详情，便于记录模板变更、生成参数、失败上下文

### 7.1.4 索引与约束策略

第一版索引和约束采用“先稳后快”的策略：

1. 关键唯一约束：
   - `agent_templates.code`
   - `agent_template_versions (template_id, version_no)`
   - `user_agents (user_id, template_id)`
   - `agent_conversations (hermes_profile, hermes_conversation_id)`

2. 高频查询索引：
   - 按用户查智能体
   - 按智能体查会话
   - 按会话查文件
   - 按时间和动作查日志

3. 外键策略：
   - 关键业务关系保留外键，减少脏数据
   - 文件与会话关系使用 `SET NULL`，避免历史文件因会话删除直接丢失

### 7.1.5 第一版数据库注意事项

在正式进入开发前，建议先确认下面这些点：

1. MySQL 版本是否支持 JSON 字段（建议 8.0+）
2. `users.id` 等主键类型是否统一为 BIGINT
3. 线上是否允许外键约束（如果不允许，需要在服务层补强一致性校验）
4. 软删除字段是否统一采用 `deleted_at`
5. 会话和文件是否需要额外的归档策略

### 7.2 `agent_template_versions`

建议字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `template_id` | 模板 ID |
| `version_no` | 版本号 |
| `version_label` | 版本标签 |
| `change_summary` | 版本变更说明 |
| `template_snapshot` | 模板完整快照 |
| `published_by` | 发布人 |
| `published_at` | 发布时间 |
| `created_at` | 创建时间 |

### 7.3 `user_agents`

建议字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `user_id` | 员工 ID |
| `template_id` | 模板 ID |
| `display_name` | 员工看到的智能体名称 |
| `hermes_profile` | 绑定的 Hermes Profile |
| `agent_status` | 开通状态 |
| `config_snapshot` | 模板快照 |
| `template_version` | 开通时使用的模板版本号 |
| `activation_mode` | 开通方式 |
| `enabled_at` | 开通时间 |
| `last_used_at` | 最后使用时间 |
| `disabled_at` | 停用时间 |

### 7.4 `agent_conversations`

建议字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `user_id` | 员工 ID |
| `user_agent_id` | 员工智能体 ID |
| `hermes_profile` | Profile 名称 |
| `hermes_conversation_id` | Hermes 会话 ID |
| `hermes_response_id` | Hermes 响应或会话标识 |
| `title` | 会话标题 |
| `current_stage` | 当前会话阶段 |
| `status` | 会话状态 |
| `message_count` | 消息数 |
| `outline_confirmed` | 是否已确认大纲 |
| `template_confirmed` | 是否已确认模板 |
| `final_generation_confirmed` | 是否已确认正式生成 |
| `latest_user_input` | 最近一条用户输入摘要 |
| `final_file_id` | 最终生成文件 ID |
| `started_at` | 开始时间 |
| `last_message_at` | 最后消息时间 |
| `completed_at` | 完成时间 |

### 7.5 `agent_generated_files`

建议字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `user_id` | 员工 ID |
| `user_agent_id` | 员工智能体 ID |
| `conversation_id` | 来源会话 ID |
| `file_type` | 文件类型 |
| `file_name` | 文件名 |
| `file_path` | 文件路径 |
| `file_size` | 文件大小 |
| `mime_type` | MIME 类型 |
| `template_name` | 使用的母版或模板名称 |
| `source_type` | 来源类型 |
| `version_no` | 文件版本号 |
| `generation_status` | 生成状态 |
| `error_message` | 失败原因 |
| `created_at` | 创建时间 |

### 7.6 `agent_operation_logs`

建议字段：

| 字段 | 说明 |
|------|------|
| `id` | 主键 |
| `operator_user_id` | 操作人 |
| `target_type` | 目标类型 |
| `target_id` | 目标 ID |
| `action` | 操作类型 |
| `action_name` | 操作名称 |
| `result_status` | 执行结果 |
| `details` | 详情 JSON |
| `error_message` | 失败原因 |
| `ip_address` | 操作者 IP |
| `created_at` | 创建时间 |

---

## 八、接口需求

### 8.1 员工侧接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agents/me` | 获取我的智能体列表 |
| POST | `/api/agents/me/enable` | 首次开通默认智能体 |
| GET | `/api/agents/me/{agent_id}` | 获取我的智能体详情 |
| POST | `/api/agents/me/{agent_id}/chat` | 发送消息 |
| GET | `/api/agents/me/{agent_id}/conversations` | 获取会话列表 |
| GET | `/api/agents/me/{agent_id}/conversations/{id}` | 获取会话详情 |
| POST | `/api/agents/me/{agent_id}/generate-ppt` | 生成正式 PPT |
| GET | `/api/agents/me/{agent_id}/files/{file_id}` | 下载生成文件 |

### 8.2 管理端接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agent-templates` | 获取模板列表 |
| POST | `/api/agent-templates` | 新建模板 |
| GET | `/api/agent-templates/{id}` | 获取模板详情 |
| PUT | `/api/agent-templates/{id}` | 更新模板 |
| POST | `/api/agent-templates/{id}/publish` | 发布模板 |
| POST | `/api/agent-templates/{id}/enable` | 启用模板 |
| POST | `/api/agent-templates/{id}/disable` | 停用模板 |
| POST | `/api/agent-templates/{id}/sync` | 同步模板到已开通员工 |

### 8.3 Hermes 接入要求

统一封装内部服务，至少提供：

1. `ensure_profile(user)`
2. `apply_template_snapshot(profile, snapshot)`
3. `chat(profile, payload)`
4. `load_conversation(profile, conversation_id)`
5. `list_conversations(profile)`

---

## 九、页面需求

### 9.1 员工侧页面

#### 页面 1：我的智能体

必须有：

1. 模板名称
2. 模板描述
3. 最近使用时间
4. 进入对话按钮

#### 页面 2：智能体对话页

必须有：

1. 左侧会话列表
2. 主聊天区域
3. 当前模板名称
4. 当前状态提示
5. 大纲确认按钮
6. 生成 PPT 按钮

#### 页面 3：我的历史记录

必须有：

1. 会话列表
2. 会话标题
3. 更新时间
4. 文件生成结果

### 9.2 管理端页面

#### 页面 1：模板管理

必须有：

1. 模板列表
2. 新增模板
3. 编辑模板
4. 启用停用
5. 版本信息

#### 页面 2：模板编辑页

必须有：

1. 基础信息区
2. 提示词配置区
3. 知识范围区
4. 工具权限区
5. 确认规则区
6. 输出要求区

---

## 十、运行时提示词要求

这一部分是给产品、研发和后续大模型协作统一口径用的。

### 10.1 欢迎语

```text
你好，我是企业 PPT 助手。

你可以直接告诉我，这份 PPT 是做什么用的、给谁看、想做多少页、有没有必须引用的公司资料。

如果你现在信息还不完整，也没关系，我会一步一步带你把这件事理顺。
```

### 10.2 补问提示词

```text
为了把这份 PPT 做得更贴合你的实际场景，我先确认几个关键信息：

1. 这份 PPT 是给谁看的？
2. 主要用在什么场景？
3. 你希望控制在多少页左右？
4. 风格更偏正式汇报、客户介绍，还是销售展示？
5. 有没有必须引用的公司资料、产品资料或案例？

你先按你知道的部分告诉我，不完整也没关系，我会继续帮你补齐。
```

### 10.3 大纲生成提示词

```text
请先根据目前的信息整理一版适合确认的 PPT 大纲。

这版先不要写得太满，重点是把结构理顺。每一页给出标题和核心要点就行，方便用户先看方向对不对。
```

### 10.4 大纲确认提示词

```text
这是我给你整理的第一版大纲。你先看整体结构对不对。

如果你愿意，我可以继续按这个结构把每一页展开；如果哪里不合适，你直接告诉我删哪一页、补哪一页，或者整体风格往哪个方向调。
```

### 10.5 知识使用提示词

```text
只要涉及公司事实、产品能力、案例数据或品牌表述，请先查企业知识库。

有明确资料就按资料来，没有把握就直说先给通用建议，不要自己补造公司信息。
```

### 10.6 模板确认提示词

```text
内容结构已经差不多了。下一步我建议把展示风格也定下来。

你可以告诉我，是想用公司标准模板，还是更偏正式汇报、客户介绍、销售展示的风格。这个定下来以后，后面的正式文件会更稳。
```

### 10.7 正式生成提示词

```text
我准备开始生成正式 PPT 文件了。

我先最后确认三件事：
1. 页数你这边确认了
2. 大纲结构没有问题
3. 展示风格或模板已经定下来

如果你确认，我就按这个版本出正式文件。
```

### 10.8 修改提示词

```text
如果你只是想调几页内容，我建议我们先做局部修改，这样会更快，也不容易把已经定好的内容带乱。

如果你想整体换方向，比如从“公司介绍”改成“售前宣讲”，那我建议先把大纲重整理一下，再继续往下做。
```

### 10.9 失败提示词

```text
内容我已经整理得差不多了，不过正式文件这一步出了点问题。

我可以先把当前内容保留下来，再帮你重试一次；如果你愿意，也可以先确认文字版，我再继续生成文件。
```

---


**文档位置：** `md/AGENT_IMPLEMENTATION_TASKS.md`
