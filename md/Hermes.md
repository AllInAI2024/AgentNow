# Hermes Agent 框架文档

> 版本：v1.0  
> 日期：2026-04-28  
> 适用：Hermes Agent v0.7.0+

---

## 一、Hermes 概述

### 1.1 什么是 Hermes Agent

Hermes Agent 是由 Nous Research 开发的具有自学习能力的 AI Agent 框架。它是唯一一个内置学习循环的 Agent —— 能够从经验中创建技能、在使用中改进技能、自主持久化知识、搜索历史对话，并在会话间建立对用户的深度理解。

**核心特性**：
- **封闭学习循环**：Agent 自主管理记忆、创建技能、自我改进
- **多实例隔离（Profiles）**：每个 Profile 拥有独立的配置、记忆、会话、技能
- **内置 RAG**：知识库共享能力
- **持久化记忆**：跨会话的记忆系统
- **MCP 支持**：连接任何 MCP 服务器扩展工具能力
- **多平台支持**：CLI、Telegram、Discord、Slack、WhatsApp 等 15+ 平台
- **API Server**：OpenAI 兼容的 HTTP API 接口

### 1.2 与 AgentNow 的关系

**AgentNow 作为桥梁层**，通过 HTTP API 与 Hermes 对接，为企业用户提供统一的 Web 界面和权限管理。

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentNow Web 层（自研）                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Web 前端    │  │  权限管理    │  │  Hermes API 代理    │ │
│  │  (Vue3)     │  │  (RBAC)     │  │  (请求转发/用户映射) │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP API (OpenAI 兼容)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 Hermes Agent 层（原生，不改造）                │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Profiles 多实例隔离系统                    │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐            │    │
│  │  │ Profile A│ │ Profile B│ │ Profile N│            │    │
│  │  │ (员工A)  │ │ (员工B)  │ │ (员工N)  │            │    │
│  │  └──────────┘ └──────────┘ └──────────┘            │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 内置 RAG    │  │ 记忆系统    │  │ 工具调用/技能系统     │ │
│  │ (知识共享)  │  │ (记忆隔离)  │  │ (自进化)             │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 关键设计原则（AgentNow 必须遵守）

| 原则 | 说明 |
|------|------|
| **不对 Hermes 进行任何改造** | 完全通过 API 方式对接，两个项目完全解耦 |
| **利用 Hermes 原生能力** | 多实例隔离、内置 RAG、记忆系统等全部使用 Hermes 现有功能 |
| **Web 层只做外围封装** | 权限管理、用户界面、企业级适配 |
| **Profile 映射** | 每个企业员工映射到 Hermes 的一个独立 Profile |

---

## 二、API Server 配置与使用

### 2.1 启用 API Server

Hermes 的 HTTP API 通过 Gateway 进程暴露。需要在 `.env` 文件中配置：

```bash
# ~/.hermes/.env (每个 Profile 独立的 .env)

# 启用 API Server
API_SERVER_ENABLED=true

# 认证密钥（必填，当绑定到非 127.0.0.1 时）
API_SERVER_KEY=your-secret-key-change-me

# 端口（默认 8642）
API_SERVER_PORT=8642

# 绑定地址（默认 127.0.0.1，仅限本地访问）
# 如需远程访问，设置为 0.0.0.0（需配合 API_SERVER_KEY）
API_SERVER_HOST=127.0.0.1

# CORS 允许的来源（浏览器直接访问时需要）
# API_SERVER_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# 模型名称（显示在 /v1/models 中）
# API_SERVER_MODEL_NAME=hermes-agent
```

### 2.2 启动 API Server

```bash
# 启动 gateway（同时启动 API Server）
hermes gateway

# 输出示例：
# [API Server] API server listening on http://127.0.0.1:8642
```

### 2.3 多用户（多 Profile）API Server 配置

为每个企业员工启动独立的 API Server（使用不同端口）：

```bash
# 1. 创建 Profile（为每个用户创建独立 Profile）
hermes profile create user_1001
hermes profile create user_1002

# 2. 为每个 Profile 配置独立的 API Server
hermes -p user_1001 config set API_SERVER_ENABLED true
hermes -p user_1001 config set API_SERVER_PORT 8643
hermes -p user_1001 config set API_SERVER_KEY user_1001_secret

hermes -p user_1002 config set API_SERVER_ENABLED true
hermes -p user_1002 config set API_SERVER_PORT 8644
hermes -p user_1002 config set API_SERVER_KEY user_1002_secret

# 3. 启动每个 Profile 的 gateway
hermes -p user_1001 gateway &
hermes -p user_1002 gateway &

# 4. 访问各自的 API
# http://localhost:8643/v1/models → 模型: user_1001
# http://localhost:8644/v1/models → 模型: user_1002
```

---

## 三、HTTP API 接口列表

### 3.1 接口概览

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI 兼容聊天补全（无状态） |
| POST | `/v1/responses` | OpenAI Responses API（有状态） |
| GET | `/v1/models` | 列出可用模型 |
| GET | `/v1/responses/{id}` | 获取存储的响应 |
| DELETE | `/v1/responses/{id}` | 删除存储的响应 |
| GET | `/health` | 健康检查 |
| GET | `/v1/health` | 健康检查（带 /v1 前缀） |

### 3.2 认证方式

所有 API 请求需要通过 Bearer Token 认证：

```http
Authorization: Bearer <API_SERVER_KEY>
```

### 3.3 POST /v1/chat/completions

**标准 OpenAI Chat Completions 格式，无状态。**

每次请求都需要传递完整的对话历史。

#### 请求示例

```json
{
  "model": "hermes-agent",
  "messages": [
    {"role": "system", "content": "You are a Python expert."},
    {"role": "user", "content": "Write a fibonacci function"}
  ],
  "stream": false
}
```

#### 响应示例

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1710000000,
  "model": "hermes-agent",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Here's a fibonacci function..."},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 50, "completion_tokens": 200, "total_tokens": 250}
}
```

#### 流式响应（stream: true）

使用 Server-Sent Events (SSE) 格式。Hermes 会发出标准的 `chat.completion.chunk` 事件，以及自定义的 `hermes.tool.progress` 事件用于显示工具执行进度。

#### 图片输入

支持图片 URL 和 base64 编码的图片：

```json
{
  "model": "hermes-agent",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/cat.png", "detail": "high"}}
      ]
    }
  ]
}
```

### 3.4 POST /v1/responses

**OpenAI Responses API 格式，有状态。**

支持服务端存储对话历史，通过 `previous_response_id` 或 `conversation` 参数保持上下文。

#### 请求示例（首次对话）

```json
{
  "model": "hermes-agent",
  "input": "What files are in my project?",
  "instructions": "You are a helpful coding assistant.",
  "store": true
}
```

#### 响应示例

```json
{
  "id": "resp_abc123",
  "object": "response",
  "status": "completed",
  "model": "hermes-agent",
  "output": [
    {"type": "function_call", "name": "terminal", "arguments": "{\"command\": \"ls\"}", "call_id": "call_1"},
    {"type": "function_call_output", "call_id": "call_1", "output": "README.md src/ tests/"},
    {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "Your project has..."}]}
  ],
  "usage": {"input_tokens": 50, "output_tokens": 200, "total_tokens": 250}
}
```

#### 多轮对话（使用 previous_response_id）

```json
{
  "input": "Now show me the README",
  "previous_response_id": "resp_abc123"
}
```

#### 命名对话（使用 conversation 参数）

使用 `conversation` 参数自动关联对话：

```json
// 第一次请求
{"input": "Hello", "conversation": "my-project", "store": true}

// 第二次请求（自动关联）
{"input": "What's in src/?", "conversation": "my-project", "store": true}

// 第三次请求
{"input": "Run the tests", "conversation": "my-project", "store": true}
```

### 3.5 会话连续性（X-Hermes-Session-Id）

使用 `X-Hermes-Session-Id` 请求头保持会话连续性：

```http
POST /v1/chat/completions
Authorization: Bearer your-secret-key
X-Hermes-Session-Id: session-uuid-12345

{
  "model": "hermes-agent",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

**说明**：
- 当客户端传递 `X-Hermes-Session-Id` 时，对话历史从 SessionDB 加载，而非请求体中的 `messages` 数组
- 会话 ID 会在响应头中回显，客户端可在首次请求后捕获并复用
- 不传递该 header 时，行为不变（每次请求新 UUID，无状态）

### 3.6 GET /v1/models

列出可用模型：

```bash
curl http://localhost:8642/v1/models \
  -H "Authorization: Bearer your-secret-key"
```

响应：
```json
{
  "object": "list",
  "data": [
    {
      "id": "hermes-agent",
      "object": "model",
      "created": 1710000000,
      "owned_by": "hermes-agent"
    }
  ]
}
```

### 3.7 健康检查

```bash
# 方式 1
curl http://localhost:8642/health

# 方式 2（带 /v1 前缀）
curl http://localhost:8642/v1/health
```

响应：
```json
{"status": "ok"}
```

---

## 四、Profiles 系统（多实例隔离）

### 4.1 什么是 Profiles

Profiles 是 Hermes 的多实例隔离机制。**每个 Profile 拥有独立的 `HERMES_HOME` 目录**，包括：

- 独立的配置（config.yaml, .env）
- 独立的 API keys 和 secrets
- 独立的记忆系统（MEMORY.md, USER.md）
- 独立的会话数据库（state.db）
- 独立的技能（skills/ 目录）
- 独立的 Gateway 服务和 Bot Token
- 独立的定时任务（cron/）

### 4.2 AgentNow 中的应用

**每个企业员工对应一个独立的 Profile**，实现：
- 记忆隔离：每个员工的对话历史和偏好独立存储
- 配置隔离：可为不同岗位配置不同的模型、工具权限
- 会话隔离：员工之间的会话完全独立

**映射方式**：
```
企业员工A (user_id: 1001)  →  Hermes Profile: "user_1001"
企业员工B (user_id: 1002)  →  Hermes Profile: "user_1002"
企业员工C (user_id: 1003)  →  Hermes Profile: "user_1003"
```

### 4.3 Profile 管理命令

```bash
# 创建新 Profile
hermes profile create <profile_name>

# 列出所有 Profile
hermes profile list

# 切换当前 Profile（设置默认）
hermes profile switch <profile_name>

# 删除 Profile
hermes profile delete <profile_name>

# 重命名 Profile
hermes profile rename <old_name> <new_name>

# 导出 Profile（用于备份/分享）
hermes profile export <profile_name> <output_file>

# 导入 Profile
hermes profile import <input_file>

# 使用指定 Profile 运行命令
hermes -p <profile_name> <command>
# 示例：
hermes -p user_1001 chat          # 以 user_1001 身份聊天
hermes -p user_1001 gateway       # 启动 user_1001 的 gateway
hermes -p user_1001 config set ... # 为 user_1001 设置配置
```

### 4.4 Profile 目录结构

每个 Profile 的数据存储在独立目录中：

```
~/.hermes-profiles/
├── user_1001/
│   ├── config.yaml      # 配置
│   ├── .env             # API keys
│   ├── SOUL.md          # Agent 角色定义
│   ├── memories/        # 记忆
│   │   ├── MEMORY.md    # Agent 笔记
│   │   └── USER.md      # 用户画像
│   ├── sessions/        # 网关会话
│   ├── skills/          # 技能
│   ├── cron/            # 定时任务
│   ├── logs/            # 日志
│   └── state.db         # 会话数据库
├── user_1002/
│   └── ...
└── user_1003/
    └── ...
```

---

## 五、记忆系统

### 5.1 记忆系统概述

Hermes 拥有边界清晰、自主管理的持久化记忆系统，跨会话保持用户偏好、项目信息和学到的知识。

### 5.2 记忆文件结构

| 文件 | 用途 | 字符限制 | 典型条目数 |
|------|------|----------|------------|
| `MEMORY.md` | Agent 个人笔记 — 环境事实、约定、学到的知识 | 2,200 字符（~800 tokens） | 8-15 条 |
| `USER.md` | 用户画像 — 偏好、沟通风格、期望 | 1,375 字符（~500 tokens） | 5-10 条 |

**存储位置**：`~/.hermes/memories/`（每个 Profile 独立）

### 5.3 记忆在系统提示中的注入

每次会话开始时，记忆内容会被加载并注入到系统提示中：

```
══════════════════════════════════════════════
MEMORY (your personal notes) [67% — 1,474/2,200 chars]
══════════════════════════════════════════════
User's project is a Rust web service at ~/code/myapi using Axum + SQLx
§
This machine runs Ubuntu 22.04, has Docker and Podman installed
§
User prefers concise responses, dislikes verbose explanations
```

**重要特性**：
- **冻结快照模式**：系统提示注入在会话开始时捕获一次，会话期间不再变化（保留 LLM 前缀缓存以提高性能）
- Agent 在会话中添加/删除记忆条目时，更改会立即持久化到磁盘，但要到下一次会话才会出现在系统提示中

### 5.4 记忆管理工具

Agent 通过 `memory` 工具自主管理记忆，支持以下操作：

| 操作 | 描述 |
|------|------|
| `add` | 添加新的记忆条目 |
| `replace` | 替换现有条目（通过子字符串匹配） |
| `remove` | 删除不再相关的条目（通过子字符串匹配） |

**无 read 操作**：记忆内容会自动在会话开始时注入到系统提示中，Agent 作为对话上下文的一部分看到其记忆。

### 5.5 两个记忆目标

#### memory — Agent 个人笔记

用于 Agent 需要记住的关于环境、工作流和学到的知识：

- 环境事实（操作系统、工具、项目结构）
- 项目约定和配置
- 发现的工具特性和变通方法
- 已完成任务的日记条目
- 有效的技能和技术

#### user — 用户画像

用于关于用户身份、偏好和沟通风格的信息：

- 姓名、角色、时区
- 沟通偏好（简洁 vs 详细、格式偏好）
- 忌讳和需要避免的事情
- 工作流习惯
- 技术技能水平

### 5.6 什么该存什么不该存

**应该保存（自动）**：
- 用户偏好："I prefer TypeScript over JavaScript" → 保存到 user
- 环境事实："This server runs Debian 12 with PostgreSQL 16" → 保存到 memory
- 修正："Don't use sudo for Docker commands, user is in docker group" → 保存到 memory
- 约定："Project uses tabs, 120-char line width, Google-style docstrings" → 保存到 memory
- 已完成工作："Migrated database from MySQL to PostgreSQL on 2026-01-15" → 保存到 memory
- 显式请求："Remember that my API key rotation happens monthly" → 保存到 memory

**应该跳过**：
- 琐碎/明显信息："User asked about Python" — 太模糊无用
- 容易重新发现的事实："Python 3.12 supports f-string nesting" — 可以通过网络搜索
- 原始数据转储：大代码块、日志文件、数据表 — 太大不适合记忆
- 会话特定的临时信息：临时文件路径、一次性调试上下文
- 已在上下文文件中的信息：SOUL.md 和 AGENTS.md 内容

---

## 六、会话系统

### 6.1 会话存储

所有 CLI 和消息平台会话存储在 SQLite 数据库 `~/.hermes/state.db` 中，具有全文搜索能力：

- 每个会话存储完整消息历史，包括模型配置和系统提示快照
- FTS5 全文搜索，通过 `session_search` 工具搜索历史对话（配合 Gemini Flash 摘要）
- 压缩触发的会话分割 — 当上下文被压缩时，创建新会话

### 6.2 会话搜索

Agent 可以使用 `session_search` 工具搜索历史对话：

```python
# 工具调用示例
session_search(
    query="database migration",
    days=7  # 可选，限制搜索范围
)
```

### 6.3 AgentNow 中的会话管理

AgentNow 可以通过以下方式管理会话：

1. **使用 `X-Hermes-Session-Id` header**：保持跨 API 请求的会话连续性
2. **使用 `/v1/responses` 接口的 `conversation` 参数**：命名对话自动关联
3. **使用 `previous_response_id`**：链式多轮对话

---

## 七、工具集与能力

### 7.1 内置工具集

Hermes 提供 47+ 内置工具，按功能分组：

| 工具集 | 包含工具 | 描述 |
|--------|----------|------|
| **terminal** | terminal | 终端命令执行 |
| **filesystem** | Read, Write, Edit, Glob, LS | 文件系统操作 |
| **web** | web_search, browser_* | 网络搜索和浏览 |
| **memory** | memory | 记忆管理 |
| **skill** | skill_manage | 技能管理 |
| **session** | session_search | 会话搜索 |
| **vision** | image_analyze | 图像分析 |
| **voice** | tts, stt | 语音合成和识别 |
| **mcp** | (动态) | MCP 服务器工具 |

### 7.2 终端后端

Hermes 支持 6 种终端后端，决定 Agent 的 shell 命令实际执行位置：

| 后端 | 命令执行位置 | 隔离级别 | 适用场景 |
|------|--------------|----------|----------|
| `local` | 直接在本机执行 | 无隔离 | 开发、个人使用 |
| `docker` | Docker 容器内 | 完全隔离 | 安全沙箱、CI/CD |
| `ssh` | 通过 SSH 连接到远程服务器 | 网络边界 | 远程服务器管理 |
| `modal` | Modal 云沙箱 | 完全隔离 | Serverless 执行 |
| `daytona` | Daytona 工作区 | 完全隔离 | Serverless 持久化 |
| `singularity` | Singularity/Apptainer 容器 | 完全隔离 | HPC 环境 |

**配置示例**（config.yaml）：
```yaml
terminal:
  backend: docker          # local | docker | ssh | modal | daytona | singularity
  cwd: "."                  # 工作目录
  timeout: 180              # 每个命令的超时（秒）
  env_passthrough: []       # 转发到沙箱执行的环境变量名
```

### 7.3 MCP 支持

Hermes 支持 Model Context Protocol (MCP)，可连接任何 MCP 服务器扩展工具能力。

**MCP 服务器模式**：
```bash
# 将 Hermes 作为 MCP 服务器暴露给 Claude Desktop、Cursor 等
hermes mcp serve
```

**功能**：
- 浏览对话
- 读取消息
- 跨会话搜索
- 管理附件

---

## 八、配置与环境变量

### 8.1 配置文件结构

```
~/.hermes/
├── config.yaml     # 主配置文件（模型、终端、TTS、压缩等）
├── .env            # API keys 和 secrets
├── auth.json       # OAuth 提供商凭证
├── SOUL.md         # 主要 Agent 身份定义
├── memories/       # 持久化记忆
├── skills/         # Agent 创建的技能
├── cron/           # 定时任务
├── sessions/       # 网关会话
└── logs/           # 日志
```

### 8.2 配置优先级

设置按以下顺序解析（优先级从高到低）：

1. **CLI 参数** — 例如 `hermes chat --model anthropic/claude-sonnet-4`（单次调用覆盖）
2. **~/.hermes/config.yaml** — 所有非秘密设置的主配置文件
3. **~/.hermes/.env** — 环境变量后备；secrets（API keys、tokens、密码）必需
4. **内置默认值** — 未设置时的硬编码安全默认值

**经验法则**：
- Secrets（API keys、bot tokens、密码）放在 `.env`
- 其他所有内容（模型、终端后端、压缩设置、内存限制、工具集）放在 `config.yaml`
- 两者都设置时，`config.yaml` 对非秘密设置优先

### 8.3 配置管理命令

```bash
# 查看当前配置
hermes config

# 用编辑器打开 config.yaml
hermes config edit

# 设置特定值
hermes config set KEY VAL

# 检查缺失选项（更新后）
hermes config check

# 交互式添加缺失选项
hermes config migrate

# 示例：
hermes config set model anthropic/claude-opus-4
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...  # 保存到 .env
```

**提示**：`hermes config set` 命令自动将值路由到正确的文件 — API keys 保存到 `.env`，其他所有内容保存到 `config.yaml`。

### 8.4 API Server 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `API_SERVER_ENABLED` | `false` | 启用 API Server |
| `API_SERVER_PORT` | `8642` | HTTP 服务器端口 |
| `API_SERVER_HOST` | `127.0.0.1` | 绑定地址（默认仅限本地） |
| `API_SERVER_KEY` | (无) | 认证用的 Bearer Token |
| `API_SERVER_CORS_ORIGINS` | (无) | 逗号分隔的允许浏览器来源列表 |
| `API_SERVER_MODEL_NAME` | (Profile 名称) | `/v1/models` 中显示的模型名称 |

---

## 九、AgentNow 对接方案

### 9.1 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         AgentNow 后端                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    HermesAPIClient                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │    │
│  │  │ Profile 管理 │  │ 对话接口    │  │ 会话管理    │    │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                            │                                      │
│            ┌───────────────┼───────────────┐                    │
│            ▼               ▼               ▼                    │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │ Profile: user_1 │ │ Profile: user_2 │ │ Profile: user_N │  │
│  │ Port: 8643      │ │ Port: 8644      │ │ Port: 8645      │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 核心模块设计

#### 1. Profile 映射服务

```python
# backend/app/services/profile_service.py

class ProfileService:
    """用户与 Hermes Profile 映射管理"""
    
    def __init__(self):
        self.profile_base_port = 8643  # 从 8643 开始分配
    
    def get_profile_name(self, user_id: int) -> str:
        """根据用户 ID 生成 Profile 名称"""
        return f"user_{user_id}"
    
    def get_profile_port(self, user_id: int) -> int:
        """根据用户 ID 分配端口（简单策略）"""
        # 实际生产环境需要更复杂的端口管理
        return self.profile_base_port + user_id % 1000
    
    def get_profile_api_url(self, user_id: int) -> str:
        """获取用户 Profile 的 API URL"""
        port = self.get_profile_port(user_id)
        return f"http://127.0.0.1:{port}"
    
    async def create_profile_if_not_exists(self, user_id: int) -> bool:
        """
        用户首次登录时自动创建 Profile
        1. 检查 Profile 是否存在
        2. 不存在则创建
        3. 配置 API Server
        4. 启动 Gateway
        """
        pass
```

#### 2. Hermes API 客户端

```python
# backend/app/services/hermes_client.py

class HermesAPIClient:
    """Hermes API 客户端封装"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completions(
        self,
        messages: list,
        stream: bool = False,
        session_id: str | None = None
    ) -> dict | AsyncGenerator:
        """
        发送聊天请求
        
        Args:
            messages: 对话历史
            stream: 是否流式响应
            session_id: 会话 ID（用于保持连续性）
        """
        url = f"{self.base_url}/v1/chat/completions"
        
        headers = self.headers.copy()
        if session_id:
            headers["X-Hermes-Session-Id"] = session_id
        
        payload = {
            "model": "hermes-agent",
            "messages": messages,
            "stream": stream
        }
        
        # 发送请求...
        pass
    
    async def create_response(
        self,
        input_text: str,
        conversation: str | None = None,
        previous_response_id: str | None = None,
        instructions: str | None = None
    ) -> dict:
        """
        使用 Responses API（有状态）
        
        Args:
            input_text: 用户输入
            conversation: 对话名称（自动关联）
            previous_response_id: 上一个响应 ID
            instructions: 系统提示
        """
        url = f"{self.base_url}/v1/responses"
        
        payload = {
            "model": "hermes-agent",
            "input": input_text,
            "store": True
        }
        
        if conversation:
            payload["conversation"] = conversation
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
        if instructions:
            payload["instructions"] = instructions
        
        # 发送请求...
        pass
    
    async def list_models(self) -> list:
        """获取可用模型列表"""
        url = f"{self.base_url}/v1/models"
        # 发送请求...
        pass
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            url = f"{self.base_url}/health"
            # 发送请求...
            return True
        except Exception:
            return False
```

### 9.3 用户 - Profile 映射流程

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户首次登录流程                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 用户登录系统    │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ 检查用户是否有  │
                    │ Hermes Profile  │
                    └────────┬────────┘
                              │
              ┌───────────────┼───────────────┐
              │ 已存在        │               │ 不存在
              ▼               │               ▼
    ┌─────────────────┐       │     ┌─────────────────┐
    │ 获取 Profile    │       │     │ 创建 Profile    │
    │ 配置信息        │       │     │ (hermes profile  │
    └────────┬────────┘       │     │ create user_xxx)│
              │                │     └────────┬────────┘
              │                │              │
              │                │              ▼
              │                │     ┌─────────────────┐
              │                │     │ 配置 API Server │
              │                │     │ (端口、密钥等)  │
              │                │     └────────┬────────┘
              │                │              │
              │                │              ▼
              │                │     ┌─────────────────┐
              │                │     │ 启动 Gateway    │
              │                │     │ (hermes -p xxx  │
              │                │     │  gateway)       │
              │                │     └────────┬────────┘
              │                │              │
              │                ▼              │
              │       ┌─────────────────┐     │
              └──────►│ 返回用户        │◄────┘
                      │ Profile 信息    │
                      └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │ 用户可开始对话  │
                      └─────────────────┘
```

### 9.4 对话接口设计

#### 方案 A：无状态 Chat Completions（简单）

**优点**：实现简单，客户端完全控制对话历史
**缺点**：每次请求都要传递完整历史，无服务器端会话

```python
# backend/app/routers/chat.py

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    对话接口（无状态）
    
    - 前端传递完整对话历史
    - 后端转发到对应 Profile 的 Hermes API
    """
    profile_name = profile_service.get_profile_name(current_user.id)
    api_url = profile_service.get_profile_api_url(current_user.id)
    
    client = HermesAPIClient(
        base_url=api_url,
        api_key=get_profile_api_key(current_user.id)
    )
    
    # 转换消息格式
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.messages
    ]
    
    response = await client.chat_completions(
        messages=messages,
        stream=request.stream
    )
    
    return response
```

#### 方案 B：有状态 Responses API（推荐）

**优点**：服务器端存储对话历史，支持工具调用回放
**缺点**：需要管理 response_id 或 conversation

```python
# backend/app/routers/chat.py

@router.post("/chat/stateful")
async def chat_stateful(
    request: StatefulChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    对话接口（有状态）
    
    - 使用 conversation 参数自动关联对话
    - Hermes 服务器端存储完整历史
    """
    api_url = profile_service.get_profile_api_url(current_user.id)
    
    client = HermesAPIClient(
        base_url=api_url,
        api_key=get_profile_api_key(current_user.id)
    )
    
    # 使用 conversation 参数（格式：user_{user_id}_conv_{conv_id}）
    conversation = f"user_{current_user.id}_conv_{request.conversation_id}"
    
    response = await client.create_response(
        input_text=request.message,
        conversation=conversation,
        instructions=request.system_prompt
    )
    
    return response
```

### 9.5 端口管理策略

**挑战**：每个 Profile 需要独立的端口，需要合理管理。

**方案**：

```python
# backend/app/services/port_manager.py

class PortManager:
    """Hermes Profile 端口管理器"""
    
    def __init__(self):
        self.start_port = 8643
        self.max_ports = 1000  # 支持最多 1000 个并发用户
        
        # 实际生产环境可能需要：
        # 1. 数据库存储端口分配
        # 2. 端口健康检查
        # 3. 闲置端口回收
    
    def allocate_port(self, user_id: int) -> int:
        """
        为用户分配端口
        
        简单策略：user_id 取模 + 起始端口
        实际生产环境需要更复杂的策略
        """
        return self.start_port + (user_id % self.max_ports)
    
    def is_port_available(self, port: int) -> bool:
        """检查端口是否可用（未被占用）"""
        # 实现端口检查逻辑
        pass
    
    def get_health_status(self, port: int) -> dict:
        """检查指定端口的 Hermes API 健康状态"""
        try:
            url = f"http://127.0.0.1:{port}/health"
            # 发送健康检查请求
            return {"status": "healthy"}
        except Exception:
            return {"status": "unhealthy"}
```

### 9.6 Gateway 进程管理

**挑战**：每个 Profile 的 Gateway 需要独立管理（启动、停止、重启）。

**方案**：

```python
# backend/app/services/gateway_manager.py

import subprocess
import asyncio
from typing import Dict, Optional

class GatewayManager:
    """Hermes Gateway 进程管理器"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
    
    def start_gateway(self, profile_name: str, port: int) -> bool:
        """
        启动指定 Profile 的 Gateway
        
        实际生产环境建议：
        1. 使用 systemd 管理服务
        2. 或使用 supervisord
        3. 或使用 Docker 容器
        """
        try:
            # 方式 1：直接启动（开发环境）
            cmd = f"hermes -p {profile_name} gateway"
            
            process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # 创建新进程组
            )
            
            self.processes[profile_name] = process
            return True
            
        except Exception as e:
            print(f"Failed to start gateway for {profile_name}: {e}")
            return False
    
    def stop_gateway(self, profile_name: str) -> bool:
        """停止指定 Profile 的 Gateway"""
        if profile_name in self.processes:
            process = self.processes[profile_name]
            process.terminate()
            # 等待进程结束
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            del self.processes[profile_name]
            return True
        return False
    
    def restart_gateway(self, profile_name: str, port: int) -> bool:
        """重启 Gateway"""
        self.stop_gateway(profile_name)
        return self.start_gateway(profile_name, port)
    
    def get_gateway_status(self, profile_name: str) -> str:
        """获取 Gateway 状态"""
        if profile_name in self.processes:
            process = self.processes[profile_name]
            if process.poll() is None:
                return "running"
            else:
                return f"exited (code: {process.returncode})"
        return "not_started"
```

---

## 十、参考资源

### 10.1 官方资源

- **GitHub**: https://github.com/NousResearch/hermes-agent
- **官方文档**: https://hermes-agent.nousresearch.com/docs/
- **中文社区文档**: https://hermesagent.org.cn/docs/

### 10.2 关键文档链接

| 主题 | 链接 |
|------|------|
| API Server | https://hermes-agent.nousresearch.com/docs/user-guide/features/api-server/ |
| Profiles | https://github.com/NousResearch/hermes-agent/pull/3681 |
| 记忆系统 | https://hermes-agent.nousresearch.com/docs/user-guide/memory/ |
| 配置 | https://hermes-agent.nousresearch.com/docs/user-guide/configuration/ |
| Open WebUI 集成 | https://hermes-agent.nousresearch.com/docs/user-guide/messaging/open-webui/ |

### 10.3 CLI 命令速查

```bash
# 基础
hermes              # 启动交互式 CLI
hermes setup        # 完整设置向导
hermes doctor       # 诊断问题
hermes update       # 更新到最新版本

# 模型配置
hermes model        # 选择 LLM 提供商和模型
hermes config set model <model>  # 设置模型

# Profile 管理
hermes profile create <name>     # 创建 Profile
hermes profile list              # 列出 Profile
hermes profile switch <name>     # 切换 Profile
hermes -p <name> <command>       # 使用指定 Profile

# API Server
hermes gateway      # 启动 Gateway（同时启动 API Server）
# 需要在 .env 中设置 API_SERVER_ENABLED=true

# 工具配置
hermes tools        # 配置启用的工具

# 配置管理
hermes config              # 查看配置
hermes config edit         # 编辑配置
hermes config set KEY VAL  # 设置配置值
```

---

## 十一、待确认问题

以下问题需要进一步验证或探索：

1. **Profile 创建的 API 方式**：目前只能通过 CLI 创建 Profile，是否有 HTTP API？
   - 如果没有，AgentNow 后端需要调用系统命令 `hermes profile create`

2. **Gateway 进程管理**：生产环境如何管理多个 Profile 的 Gateway 进程？
   - 建议使用 systemd 或 supervisord
   - 或使用 Docker 容器隔离

3. **RAG/知识库功能**：Hermes 的内置 RAG 如何通过 API 管理？
   - 需要进一步探索文档或源码
   - 是否有文档上传、列表、删除的 API？

4. **技能系统**：如何通过 API 管理技能？
   - 需要进一步探索

5. **记忆管理**：如何通过 API 读取或修改记忆？
   - 目前记忆由 Agent 自主管理
   - 是否有外部 API 可干预？

---

## 十二、版本历史

| 版本 | 日期 | 修改内容 |
|------|------|----------|
| v1.0 | 2026-04-28 | 初始版本，整理 Hermes 核心功能、API、Profiles 系统 |
