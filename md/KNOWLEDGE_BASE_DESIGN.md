# 知识库管理功能设计文档（最终版）

> 版本：v3.0（最终方案）\
> 日期：2026-04-28\
> 状态：已确认

---

## 一、方案概述

### 1.1 核心方案

**使用现成的 MCP Server：[@wirux/mcp-markdown-vault](https://www.npmjs.com/package/@wirux/mcp-markdown-vault)**

这是一个成熟、开箱即用的解决方案，由 wirux 开发，最近 2 天发布 v1.8.2 版本。

### 1.2 为什么选择这个方案？

| 优势 | 说明 |
|------|------|
| ❌ **不需要 Obsidian** | 直接读写 .md 文件，不需要任何应用或插件 |
| 🧠 **内置语义搜索** | 混合检索：向量相似度 + TF-IDF + 词邻近度 |
| ⚡ **零配置嵌入** | 本地模型 all-MiniLM-L6-v2，第一次运行自动下载，无 API key |
| 🔧 **AST 精细编辑** | 基于 remark AST 的精确编辑，不会意外修改文件其他部分 |
| 📦 **单包运行** | `npx @wirux/mcp-markdown-vault` 一个命令启动 |
| 🐳 **Docker 支持** | 支持多客户端的 HTTP/SSE 传输方式 |
| 🔓 **数据开放** | 所有数据都是纯 .md 文件，可随时导入 Obsidian |

---

## 二、整体架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AgentNow 前端                                        │
│                      (知识库管理界面 - Vue3)                                   │
│                                                                                 │
│  功能：                                                                         │
│  - 文档列表、搜索、筛选                                                          │
│  - 上传文件 / 创建 Markdown                                                     │
│  - 编辑元数据 / 编辑内容                                                        │
│  - 下载 / 删除                                                                  │
│  - 统计信息 / 存储信息                                                          │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼ REST API
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AgentNow 后端                                         │
│                                                                                 │
│  职责：                                                                         │
│  - 用户认证、权限控制                                                            │
│  - 文档元数据管理（MySQL）                                                       │
│  - 文件系统操作（直接读写 ~/.agentnow/knowledge/docs/）                         │
│                                                                                 │
│  与 mcp-markdown-vault 的关系：                                                 │
│  - 两者共享同一个目录：~/.agentnow/knowledge/docs/                              │
│  - AgentNow 通过文件系统读写                                                     │
│  - mcp-markdown-vault 也直接读写同一个目录                                       │
│  - 不需要任何同步机制，自动共享                                                   │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ├───► 文件系统：~/.agentnow/knowledge/docs/
                                │              (AgentNow 与 mcp-markdown-vault 共享)
                                │
                                │ MCP (stdio 或 HTTP/SSE)
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    @wirux/mcp-markdown-vault                                  │
│                         (MCP Server)                                           │
│                                                                                 │
│  核心特性（开箱即用）：                                                          │
│                                                                                 │
│  📁 vault 操作：                                                                │
│  - list, read, create, update, delete, stat, create_from_template              │
│                                                                                 │
│  ✏️ edit 精细编辑：                                                             │
│  - append, prepend, replace, line_replace, string_replace,                     │
│  - frontmatter_set, batch (支持 dryRun 预览)                                  │
│                                                                                 │
│  👁️ view 搜索与查看：                                                           │
│  - search, global_search, **semantic_search** (混合检索！),                   │
│  - outline, read, frontmatter_get, bulk_read, backlinks                        │
│                                                                                 │
│  🔬 语义搜索（零配置）：                                                          │
│  - 混合检索：向量相似度 + TF-IDF + 词邻近度                                       │
│  - 本地嵌入模型：all-MiniLM-L6-v2 (384d)                                      │
│  - 第一次运行自动下载，无 API key，完全本地                                       │
│  - Ollama 可选（更高质量）                                                       │
│                                                                                 │
│  🔄 workflow 工作流追踪：                                                        │
│  - status, transition, history, reset                                           │
│                                                                                 │
│  ⚙️ system 系统管理：                                                           │
│  - status, reindex, overview                                                    │
│                                                                                 │
│  部署方式：                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐      │
│  │ 方式 1：npx（本地开发，最简单）                                        │      │
│  │   VAULT_PATH=~/.agentnow/knowledge/docs npx @wirux/mcp-markdown-vault  │      │
│  │                                                                      │      │
│  │ 方式 2：Docker（推荐，服务器部署）                                      │      │
│  │   docker run -d \                                                    │      │
│  │     --name markdown-vault \                                          │      │
│  │     -v ~/.agentnow/knowledge/docs:/vault:rw \                       │      │
│  │     -p 3000:3000 \                                                  │      │
│  │     -e VAULT_PATH=/vault \                                          │      │
│  │     ghcr.io/wirux/mcp-markdown-vault:latest                         │      │
│  └─────────────────────────────────────────────────────────────────────┘      │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
                                ▼ MCP (stdio 或 HTTP/SSE)
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Hermes 智能体系统                                  │
│                                                                                 │
│  配置 ~/.hermes/config.yaml：                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │  mcp_servers:                                                             │  │
│  │    agentnow_knowledge:                                                    │  │
│  │      command: npx                                                         │  │
│  │      args:                                                                │  │
│  │        - "-y"                                                             │  │
│  │        - "@wirux/mcp-markdown-vault"                                     │  │
│  │      env:                                                                 │  │
│  │        VAULT_PATH: "/Users/yourname/.agentnow/knowledge/docs"           │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│  智能体自主调用 MCP 工具：                                                       │
│  - 搜索：view_search, view_semantic_search, view_global_search                │
│  - 读取：vault_read, view_read, view_bulk_read, view_outline                  │
│  - 创建：vault_create, vault_create_from_template                              │
│  - 更新：vault_update, edit_append, edit_prepend, edit_replace,               │
│          edit_frontmatter_set, edit_batch                                      │
│  - 删除：vault_delete                                                          │
│  - 其他：view_frontmatter_get, view_backlinks, system_overview                 │
│                                                                                 │
│  设计原则：                                                                      │
│  ✅ 全局知识库共享：所有智能体访问同一个 ~/.agentnow/knowledge/docs/          │
│  ✅ 个人记忆隔离：Hermes MEMORY.md 保持独立                                    │
│  ✅ 智能体自主：智能体自己决定何时调用 MCP 工具                                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **复用成熟组件** | 使用现成的 @wirux/mcp-markdown-vault，不重复造轮子 |
| **文件系统共享** | AgentNow 和 mcp-markdown-vault 共享同一个目录，无需同步 |
| **权限分层** | AgentNow 负责用户认证和权限控制，MCP Server 只处理文件操作 |
| **数据开放** | 所有文档都是纯 Markdown 文件，可随时导入 Obsidian |
| **零配置语义搜索** | mcp-markdown-vault 内置语义搜索，自动下载本地嵌入模型 |
| **最小可用** | Demo 版本，实现核心闭环即可 |

### 2.3 全局共享 vs 个人记忆

| 层级 | 存储位置 | 访问权限 | 容量 | 用途 |
|------|----------|----------|------|------|
| **全局知识库** | `~/.agentnow/knowledge/docs/` | 所有智能体共享 | 无限制 | 企业知识、公共文档 |
| **个人记忆** | Hermes `MEMORY.md` | 仅该智能体 | ~2200 字符 | 个人偏好、工作习惯 |
| **用户配置** | Hermes `USER.md` | 仅该用户 | ~1375 字符 | 用户偏好、沟通风格 |

**设计思路：**
- 企业级公共知识 → **全局知识库**（AgentNow 管理，mcp-markdown-vault 检索）
- 个人工作习惯、偏好 → **个人记忆**（Hermes 管理）
- 智能体自主决定：是从个人记忆查找，还是从全局知识库搜索

---

## 三、数据库设计（简化版）

### 3.1 数据表结构

AgentNow 的数据库主要用于：
- 用户认证和权限控制
- 文档元数据缓存（避免每次都读文件）
- 操作日志记录

**不存储：**
- 文档实际内容（存在文件系统）
- 索引（mcp-markdown-vault 自己管理）

#### 3.1.1 知识库文档表 (knowledge_docs)

```sql
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    title VARCHAR(500) NOT NULL COMMENT '文档标题',
    file_name VARCHAR(500) NOT NULL COMMENT '文件名',
    file_path VARCHAR(1000) NOT NULL COMMENT '相对存储路径（相对于知识库根目录）',
    
    file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
    file_type VARCHAR(50) COMMENT '文件类型/扩展名',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    content_hash VARCHAR(64) COMMENT '文件内容哈希值（SHA256）',
    
    description TEXT COMMENT '文档描述/摘要',
    tags JSON COMMENT '标签列表，JSON数组格式',
    category VARCHAR(100) COMMENT '文档分类',
    
    created_by BIGINT COMMENT '创建者用户ID',
    updated_by BIGINT COMMENT '最后更新者用户ID',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开',
    
    word_count BIGINT DEFAULT 0 COMMENT '字数统计（仅文本文件）',
    file_modified_at DATETIME COMMENT '文件最后修改时间',
    
    deleted_at DATETIME COMMENT '删除时间（软删除）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_title (title),
    INDEX idx_file_name (file_name),
    INDEX idx_category (category),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档表';
```

#### 3.1.2 知识库配置表 (knowledge_configs)

```sql
CREATE TABLE IF NOT EXISTS knowledge_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '配置描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库配置表';

INSERT INTO knowledge_configs (config_key, config_value, description) VALUES
('storage.base_path', '~/.agentnow/knowledge/docs', '知识库文档存储根目录'),
('file.max_size', '104857600', '单文件最大大小（字节，默认100MB）'),
('file.allowed_types', '.pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml', '允许上传的文件类型'),
('mcp.enabled', 'true', '是否启用MCP服务（供Hermes调用）');
```

### 3.2 权限设计

| 权限码 | 权限名称 | 超级管理员 | 系统管理员 | 普通用户 |
|--------|----------|-------------|-----------|---------|
| `knowledge:doc:query` | 文档查询 | ✅ | ✅ | ✅ |
| `knowledge:doc:detail` | 文档详情 | ✅ | ✅ | ✅ |
| `knowledge:doc:create` | 文档上传/创建 | ✅ | ✅ | ✅ |
| `knowledge:doc:update` | 文档编辑 | ✅ | ✅ | ⚠️ 仅自己创建的 |
| `knowledge:doc:delete` | 文档删除 | ✅ | ✅ | ⚠️ 仅自己创建的 |
| `knowledge:doc:download` | 文档下载 | ✅ | ✅ | ✅ |
| `knowledge:config:view` | 配置查看 | ✅ | ✅ | ❌ |
| `knowledge:config:edit` | 配置编辑 | ✅ | ✅ | ❌ |

**权限最小可用原则：**
- 普通用户只能编辑/删除自己创建的文档
- 只有管理员可以查看和编辑系统配置

---

## 四、文件存储设计

### 4.1 目录结构

```
~/.agentnow/knowledge/
└── docs/                          # 文档目录（与 mcp-markdown-vault 共享）
    ├── product/                   # 按分类分目录（可选）
    │   ├── 2026-04-28-product-overview.md
    │   └── 2026-04-29-roadmap.md
    ├── tech/
    │   └── 2026-04-28-api-design.md
    ├── archive/                   # 归档目录
    │   └── ...
    └── ...
```

**说明：**
- 这个目录由 AgentNow 和 mcp-markdown-vault 共享
- 两者都直接读写这个目录，无需任何同步机制
- 目录结构可以简单，也可以按分类组织

### 4.2 文档命名规范

**推荐格式：** `{YYYY-MM-DD}-{slugified-title}.{ext}`

**示例：**
- `2026-04-28-知识库系统设计文档.md`
- `2026-04-28-product-roadmap-2026.pdf`

**优点：**
- 按日期排序，方便查找
- 标题 slug 化，避免特殊字符问题
- 可随时导入 Obsidian

### 4.3 Markdown 文档格式

推荐使用标准 Markdown + YAML Frontmatter（mcp-markdown-vault 完全支持）：

```markdown
---
title: 知识库系统设计文档
description: AgentNow 知识库系统的完整设计方案
tags:
  - 设计
  - 知识库
  - 系统架构
category: tech
author: 张三
created_at: 2026-04-28
updated_at: 2026-04-28
version: 1.0
status: draft
---

# 知识库系统设计文档

## 一、背景

...

## 二、架构设计

...
```

**优点：**
- 标准格式，mcp-markdown-vault 完全兼容
- Frontmatter 包含元数据，便于解析
- 可直接在 Obsidian 中编辑

---

## 五、API 设计

### 5.1 后端 API（AgentNow 提供）

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/api/v1/knowledge/docs` | 获取文档列表（分页、筛选） | `knowledge:doc:query` |
| GET | `/api/v1/knowledge/docs/{id}` | 获取文档详情（可包含 content） | `knowledge:doc:detail` |
| POST | `/api/v1/knowledge/docs` | 上传文件并创建文档 | `knowledge:doc:create` |
| POST | `/api/v1/knowledge/docs/markdown` | 直接创建 Markdown 文档 | `knowledge:doc:create` |
| PUT | `/api/v1/knowledge/docs/{id}` | 更新文档元数据 | `knowledge:doc:update` |
| PUT | `/api/v1/knowledge/docs/{id}/content` | 更新文档内容（文本文件） | `knowledge:doc:update` |
| DELETE | `/api/v1/knowledge/docs/{id}` | 删除文档（软删除） | `knowledge:doc:delete` |
| GET | `/api/v1/knowledge/docs/{id}/download` | 下载文档 | `knowledge:doc:download` |
| GET | `/api/v1/knowledge/categories` | 获取所有分类 | `knowledge:doc:query` |
| GET | `/api/v1/knowledge/tags` | 获取所有标签 | `knowledge:doc:query` |
| GET | `/api/v1/knowledge/statistics` | 获取统计信息 | `knowledge:config:view` |
| GET | `/api/v1/knowledge/storage` | 获取存储信息 | `knowledge:config:view` |
| GET | `/api/v1/knowledge/configs` | 获取配置列表 | `knowledge:config:view` |
| PUT | `/api/v1/knowledge/configs/{id}` | 更新配置 | `knowledge:config:edit` |

### 5.2 MCP 工具（由 mcp-markdown-vault 提供）

智能体通过 MCP 协议调用这些工具，**AgentNow 不需要开发这些**：

#### 📁 vault 工具

| 工具 | 动作 | 描述 |
|------|------|------|
| `vault` | `list` | 列出目录内容 |
| `vault` | `read` | 读取文件内容 |
| `vault` | `create` | 创建新文件 |
| `vault` | `update` | 更新文件 |
| `vault` | `delete` | 删除文件 |
| `vault` | `stat` | 获取文件元信息 |
| `vault` | `create_from_template` | 从模板创建 |

#### ✏️ edit 工具

| 工具 | 动作 | 描述 |
|------|------|------|
| `edit` | `append` | 追加内容 |
| `edit` | `prepend` | 前置内容 |
| `edit` | `replace` | 替换内容 |
| `edit` | `line_replace` | 按行号替换 |
| `edit` | `string_replace` | 字符串替换 |
| `edit` | `frontmatter_set` | 设置 YAML frontmatter |
| `edit` | `batch` | 批量编辑（支持 dryRun 预览） |

#### 👁️ view 工具（搜索与查看）

| 工具 | 动作 | 描述 |
|------|------|------|
| `view` | `search` | 关键词搜索 |
| `view` | `global_search` | 全局搜索 |
| `view` | `semantic_search` | **混合检索（向量 + TF-IDF）** |
| `view` | `outline` | 获取大纲（标题结构） |
| `view` | `read` | 读取内容（支持按标题读取） |
| `view` | `frontmatter_get` | 读取 frontmatter |
| `view` | `bulk_read` | 批量读取 |
| `view` | `backlinks` | 查找反向链接 |

---

## 六、配置与部署

### 6.1 创建知识库目录

```bash
mkdir -p ~/.agentnow/knowledge/docs
chmod -R 755 ~/.agentnow/knowledge/
```

### 6.2 配置 Hermes MCP 连接

编辑 `~/.hermes/config.yaml`，添加：

```yaml
mcp_servers:
  agentnow_knowledge:
    command: npx
    args:
      - "-y"
      - "@wirux/mcp-markdown-vault"
    env:
      VAULT_PATH: "/Users/yourname/.agentnow/knowledge/docs"
```

**注意：**
- 将 `/Users/yourname/` 替换为实际的用户目录
- `npx -y` 会自动安装包（如果不存在）
- 第一次运行时，嵌入模型会自动下载（约 100MB）

### 6.3 Docker 部署方式（可选）

如果需要多客户端访问或服务器部署：

```bash
docker run -d \
  --name markdown-vault \
  -v ~/.agentnow/knowledge/docs:/vault:rw \
  -p 3000:3000 \
  -e VAULT_PATH=/vault \
  ghcr.io/wirux/mcp-markdown-vault:latest
```

然后 Hermes 配置（通过 HTTP/SSE）：

```yaml
mcp_servers:
  agentnow_knowledge:
    command: npx
    args:
      - "-y"
      - "mcp-remote"
      - "http://localhost:3000/sse"
```

### 6.4 环境变量配置

mcp-markdown-vault 支持的环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VAULT_PATH` | 知识库目录（必填） | 无 |
| `OLLAMA_BASE_URL` | Ollama 地址（可选，更高质量嵌入） | `http://localhost:11434` |
| `EMBEDDING_MODEL` | 嵌入模型（可选） | `all-MiniLM-L6-v2` |

---

## 七、开发任务清单

### 7.1 后端开发（已完成）

| 模块 | 状态 | 说明 |
|------|------|------|
| `config.py` | ✅ 已完成 | 添加 `KNOWLEDGE_BASE_PATH` 等配置 |
| `models/knowledge_doc.py` | ✅ 已完成 | 简化模型，新增辅助方法 |
| `schemas/knowledge.py` | ✅ 已完成 | 更新 schema，支持内容编辑 |
| `utils/file_handler.py` | ✅ 已完成 | 增强文件处理功能 |
| `services/knowledge_service.py` | ✅ 已完成 | 重写服务层，移除 Hermes 同步 |
| `routers/knowledge.py` | ✅ 已完成 | 更新路由，新增 Markdown 创建、内容编辑等 |
| `data/database.sql` | ✅ 已完成 | 简化表结构，更新权限配置 |

### 7.2 前端开发（已完成）

| 模块 | 状态 | 说明 |
|------|------|------|
| `types/index.ts` | ✅ 已完成 | 更新类型定义 |
| `api/knowledge.ts` | ✅ 已完成 | 更新 API 调用 |
| `views/KnowledgeDocument.vue` | ✅ 已完成 | 文档列表管理页面 |

### 7.3 配置与测试（待执行）

| 任务 | 状态 | 说明 |
|------|------|------|
| 创建知识库目录 | ⏳ 待执行 | `mkdir -p ~/.agentnow/knowledge/docs` |
| 数据库初始化/升级 | ⏳ 待执行 | 执行 `database.sql` |
| 配置 Hermes MCP | ⏳ 待执行 | 修改 `~/.hermes/config.yaml` |
| 测试后端 API | ⏳ 待执行 | 启动后端，测试 API |
| 测试 MCP 连接 | ⏳ 待执行 | 启动 Hermes，测试智能体调用 |

---

## 八、测试方法

### 8.1 测试 AgentNow 后端

```bash
# 进入 backend 目录
cd /path/to/AgentNow/backend

# 安装依赖（如果还没有）
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 5116

# 访问 API 文档
# http://localhost:5116/docs
```

### 8.2 测试 mcp-markdown-vault

```bash
# 测试是否可用
VAULT_PATH=~/.agentnow/knowledge/docs npx @wirux/mcp-markdown-vault

# 如果提示安装，输入 y
```

### 8.3 测试 Hermes 连接

```bash
# 启动 Hermes（会自动加载配置中的 MCP 服务器）
hermes

# 在对话中测试：
# "搜索知识库中关于产品介绍的文档"
# "读取产品介绍文档"
# "在知识库中创建一个新文档，标题是：测试文档"
```

---

## 九、注意事项

### 9.1 嵌入模型下载

mcp-markdown-vault 使用本地嵌入模型 `all-MiniLM-L6-v2`，第一次运行时会自动下载（约 100MB）：
- 无需 API key
- 完全本地运行，不依赖外部服务
- 下载完成后，后续启动很快

### 9.2 文件同步

- AgentNow 和 mcp-markdown-vault 共享同一个目录
- 两者都直接读写，**无需任何同步机制**
- 如果在 AgentNow 中上传文件，mcp-markdown-vault 会自动检测到
- mcp-markdown-vault 有自动索引机制，文件变更会被检测

### 9.3 智能体自主调用

Hermes 智能体自己决定何时调用 MCP 工具：
- 可以直接问："搜索知识库中关于 XXX 的文档"
- 或者让智能体自己决定："回答这个问题，如果需要可以使用知识库"

### 9.4 权限边界

| 层级 | 权限控制 | 说明 |
|------|----------|------|
| AgentNow 层 | ✅ 完全控制 | 用户认证、权限校验、操作记录 |
| MCP 层 | ❌ 不控制 | 只处理文件操作，没有用户概念 |
| 文件系统 | ⚠️ 有限制 | 基于目录权限 |

**注意：** 目前的设计中，MCP Server 层没有权限控制。如果需要细粒度权限控制，后续可以考虑：
- 让 AgentNow 作为 MCP 代理
- 或者在 Hermes 层面控制

对于 Demo 版本，当前设计已足够。

---

## 十、总结

### 10.1 最终方案确认

| 组件 | 选择 | 说明 |
|------|------|------|
| MCP Server | **@wirux/mcp-markdown-vault** | 开箱即用，内置语义搜索 |
| 知识库存储 | 纯文件系统 | `~/.agentnow/knowledge/docs/` |
| AgentNow 职责 | 管理界面 + 权限控制 | 不重复造轮子 |
| 搜索方式 | mcp-markdown-vault 内置 | 混合检索：向量 + TF-IDF |
| 嵌入模型 | all-MiniLM-L6-v2 | 本地自动下载，无 API key |

### 10.2 核心优势

1. **无需重复开发**：使用现成的 MCP Server，不重复造轮子
2. **零配置语义搜索**：开箱即用的混合检索
3. **数据开放**：纯 Markdown 文件，可随时导入 Obsidian
4. **架构清晰**：AgentNow 管理界面，MCP Server 处理检索
5. **最小可用**：Demo 版本，快速验证概念

### 10.3 下一步

1. **创建知识库目录**：`mkdir -p ~/.agentnow/knowledge/docs`
2. **初始化/升级数据库**：执行 `backend/data/database.sql`
3. **配置 Hermes MCP**：修改 `~/.hermes/config.yaml`
4. **启动测试**：后端 → 前端 → MCP → Hermes

---

**文档结束。**
