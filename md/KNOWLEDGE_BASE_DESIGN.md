# 知识库管理功能设计文档（v2.0）

> 版本：v2.0  
> 日期：2026-04-28  
> 状态：基于 MCP 的完整解决方案

***

## 一、背景与重新评估

### 1.1 Hermes 知识库现状（重要更新）

经过深入调研，发现 Hermes 的知识库功能**并非已实现功能**，而是 Feature Request：

| 功能 | 状态 | Issue/PR | 说明 |
|------|------|----------|------|
| Knowledgebase RAG | ❌ Feature Request | #844 | 设计文档，尚未实现 |
| User Workspace | ❌ Feature Request | #531 | 概念设计，尚未实现 |
| semantic-memory skill | ❓ PR #4056 | 开发中，可能未发布 |
| MEMORY.md / USER.md | ✅ 已实现 | - | 有限容量（共 ~3500 字符） |
| FTS5 Session Search | ✅ 已实现 | - | 对话历史搜索 |
| MCP Integration | ✅ 已实现 | v0.7.0+ | 标准协议支持 |

**关键发现：**
- `~/.hermes/workspace/` 目录**不存在**，因为该功能尚未实现
- Semantic Memory skill 可能**未发布到官方仓库**
- Hermes 当前可用的持久化能力只有 **MEMORY.md**（2200 chars）和 **USER.md**（1375 chars）

### 1.2 Obsidian 知识库架构研究

#### 1.2.1 Obsidian 核心组件

| 组件 | 说明 | 依赖 |
|------|------|------|
| Obsidian 桌面应用 | Electron 应用，Markdown 编辑器 | GUI 显示器 |
| Local REST API Plugin | 社区插件，提供 REST API | Obsidian 运行中 |
| Obsidian MCP Server | 连接 MCP 客户端和 REST API | Local REST API 插件 |
| Obsidian Sync | 官方付费同步服务 | 付费订阅 |
| Obsidian Headless | CLI 同步工具（Beta） | 付费订阅 |

#### 1.2.2 Obsidian 的问题

| 问题 | 说明 |
|------|------|
| 需要 GUI | Electron 应用，必须有显示器才能运行 |
| Headless 复杂 | 需要 Xvfb + Openbox 模拟显示器，配置复杂 |
| 资源消耗大 | 运行时需要 200-300MB RAM |
| API 依赖应用 | Local REST API 是插件，Obsidian 必须运行 |

#### 1.2.3 Obsidian 的优点

| 优点 | 说明 |
|------|------|
| 成熟的编辑体验 | 强大的 Markdown 编辑器、双向链接、标签系统 |
| 文件系统存储 | 所有数据都是 Markdown 文件，可移植性强 |
| 插件生态 | 丰富的社区插件（Dataview、Templater 等） |
| MCP 支持 | 有成熟的 MCP Server 实现 |

### 1.3 重新评估后的设计目标

**核心问题：**
- Hermes 没有成熟的知识库功能
- Obsidian 需要 GUI，不适合服务器部署
- 需要**全局共享的知识库**（所有智能体可访问）
- 需要**个人记忆隔离**（每个智能体独立）
- 智能体需要**自主决定**何时访问知识库

**解决方案：**
- **AgentNow 自建知识库管理系统**（不依赖 Hermes/Obsidian）
- **提供 MCP Server**（让 Hermes 智能体可以调用）
- **存储基于文件系统**（Markdown 文件，可随时导入 Obsidian）
- **全局共享 + 个人记忆隔离** 的双层设计

***

## 二、整体架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AgentNow 知识库系统                                   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              接入层                                        │ │
│  │                                                                           │ │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │ │
│  │  │    Web UI        │    │    REST API      │    │    MCP Server    │ │ │
│  │  │    (Vue3)        │◄──►│    (FastAPI)     │◄──►│  (供 Hermes 连接)  │ │ │
│  │  │  - 文档管理       │    │  - 文档 CRUD     │    │                  │ │ │
│  │  │  - 标签管理       │    │  - 搜索/检索     │    │  Tools:           │ │ │
│  │  │  - 搜索功能       │    │  - 权限控制       │    │  - search         │ │ │
│  │  │  - 权限管理       │    │                  │    │  - get_note       │ │ │
│  │  └──────────────────┘    └──────────────────┘    │  - list_notes     │ │ │
│  │                                                    │  - create_note    │ │ │
│  │                                                    │  - update_note    │ │ │
│  │                                                    │  - delete_note    │ │ │
│  │                                                    │  - list_tags      │ │ │
│  │                                                    └──────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                         │
│                                      ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              服务层                                        │ │
│  │                                                                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │ │
│  │  │  文档服务      │  │  搜索服务      │  │  标签服务      │  │  权限服务  │ │ │
│  │  │  DocService   │  │ SearchService │  │  TagService   │  │ AuthSvc  │ │ │
│  │  │              │  │              │  │              │  │          │ │ │
│  │  │ - 上传/下载   │  │ - 全文搜索   │  │ - 标签管理   │  │ - 访问控制│ │ │
│  │  │ - 创建/删除   │  │ - 标签搜索   │  │ - 分类管理   │  │ - 权限校验│ │ │
│  │  │ - 版本管理    │  │ - 分类搜索   │  │ - 标签云     │  │          │ │ │
│  │  │ - 附件管理    │  │ - 高级检索   │  │              │  │          │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                         │
│                                      ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                              数据存储层                                    │ │
│  │                                                                           │ │
│  │  ┌──────────────────────────────┐    ┌──────────────────────────────┐ │ │
│  │  │          MySQL               │    │         文件系统                │ │ │
│  │  │                              │    │                              │ │ │
│  │  │  表：                        │    │  路径：~/.agentnow/knowledge/ │ │ │
│  │  │  - knowledge_docs           │    │                              │ │ │
│  │  │  - knowledge_doc_chunks     │    │  结构：                        │ │ │
│  │  │  - knowledge_tags           │    │  ├── docs/          # 文档目录   │ │ │
│  │  │  - knowledge_categories     │    │  │   ├── 2026/     # 按年分目录  │ │ │
│  │  │  - knowledge_attachments    │    │  │   ├── archive/  # 归档目录   │ │ │
│  │  │  - knowledge_configs        │    │  │   └── ...       # 其他分类   │ │ │
│  │  │                              │    │  │                              │ │ │
│  │  │  用途：                      │    │  ├── attachments/   # 附件目录   │ │ │
│  │  │  - 文档元数据                │    │  ├── index/        # 搜索索引   │ │ │
│  │  │  - 标签/分类                 │    │  ├── temp/         # 临时文件   │ │ │
│  │  │  - 权限配置                  │    │  └── versions/     # 版本历史   │ │ │
│  │  │  - 搜索日志                  │    │                              │ │ │
│  │  └──────────────────────────────┘    └──────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          │ MCP (stdio 或 HTTP)
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Hermes 智能体系统                                 │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                           智能体层                                         │ │
│  │                                                                           │ │
│  │  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │ │
│  │  │    智能体 A       │    │    智能体 B       │    │   MCP 客户端      │ │ │
│  │  │   (员工A)        │    │   (员工B)        │    │                  │ │ │
│  │  │                  │    │                  │    │  连接 AgentNow    │ │ │
│  │  │  个人记忆：       │    │  个人记忆：       │    │  MCP Server      │ │ │
│  │  │  - MEMORY.md     │    │  - MEMORY.md     │    │                  │ │ │
│  │  │  - USER.md       │    │  - USER.md       │    │  可调用工具：      │ │ │
│  │  │  (隔离，不共享)   │    │  (隔离，不共享)   │    │  - search         │ │ │
│  │  │                  │    │                  │    │  - get_note       │ │ │
│  │  │  可访问：         │    │  可访问：         │    │  - list_notes     │ │ │
│  │  │  - 全局知识库     │◄──►│  - 全局知识库     │◄──►│  - create_note    │ │ │
│  │  │  (通过 MCP)      │    │  (通过 MCP)      │    │  - update_note    │ │ │
│  │  │                  │    │                  │    │  - delete_note    │ │ │
│  │  │  自主决定何时调用 │    │  自主决定何时调用 │    │  - list_tags      │ │ │
│  │  └──────────────────┘    └──────────────────┘    └──────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  设计原则：                                                                      │
│  - 全局知识库：所有智能体共享，存储企业知识、公共文档                            │
│  - 个人记忆：每个智能体独立，存储个人偏好、工作习惯                                │
│  - 智能体自主：MCP 工具让智能体自己决定何时访问知识库                             │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

| 原则 | 说明 |
|------|------|
| **不依赖第三方** | 不依赖 Hermes 未实现功能，不依赖 Obsidian GUI |
| **文件系统存储** | 文档以 Markdown 格式存储，可随时导入 Obsidian |
| **MCP 标准协议** | 提供标准 MCP Server，Hermes 可直接连接 |
| **全局共享** | 知识库所有智能体可访问 |
| **个人记忆隔离** | Hermes 的 MEMORY.md/USER.md 保持独立 |
| **智能体自主** | 智能体自己决定何时调用知识库工具 |
| **最小可用** | Demo 版本，实现核心闭环即可 |

### 2.3 全局共享 vs 个人记忆

| 层级 | 存储位置 | 访问权限 | 容量限制 | 用途 |
|------|----------|----------|----------|------|
| **全局知识库** | AgentNow 管理 | 所有智能体共享 | 无限制（文件系统） | 企业知识、公共文档、项目资料 |
| **个人记忆** | Hermes MEMORY.md | 仅该智能体 | 2200 字符 | 个人偏好、工作习惯、临时笔记 |
| **用户配置** | Hermes USER.md | 仅该用户 | 1375 字符 | 用户偏好、沟通风格 |

**设计思路：**
- 企业级的公共知识放在 **全局知识库**（AgentNow 管理）
- 个人的工作习惯、偏好放在 **个人记忆**（Hermes 管理）
- 智能体在对话中自主决定：
  - 是从个人记忆查找（快速、小容量）
  - 还是从全局知识库搜索（全面、大容量）

***

## 三、MCP Server 设计

### 3.1 MCP 工具定义

AgentNow 提供以下 MCP 工具，供 Hermes 智能体调用：

| 工具名称 | 参数 | 返回值 | 说明 |
|----------|------|--------|------|
| `knowledge_search` | query: str, limit: int = 10 | 匹配的文档列表 | 搜索知识库（全文、标签、分类） |
| `knowledge_get` | doc_id: int | 文档完整内容 | 获取单个文档的详细内容 |
| `knowledge_list` | category: str = None, tag: str = None, limit: int = 20 | 文档列表 | 列出文档（可按分类/标签筛选） |
| `knowledge_create` | title: str, content: str, tags: list = [], category: str = None | 创建的文档信息 | 创建新文档 |
| `knowledge_update` | doc_id: int, title: str = None, content: str = None, tags: list = None | 更新后的文档信息 | 更新文档 |
| `knowledge_delete` | doc_id: int | 删除结果 | 删除文档（软删除） |
| `knowledge_tags` | - | 标签列表及计数 | 获取所有标签 |
| `knowledge_categories` | - | 分类列表 | 获取所有分类 |

### 3.2 MCP Server 实现方式

有两种方式实现 MCP Server：

#### 方式 A：独立进程（推荐，更灵活）

```
AgentNow 后端 (FastAPI)
    │
    ├── REST API (Web UI 使用)
    │
    └── MCP Server (独立进程)
         │
         └── stdio 或 HTTP 传输
              │
              ▼
         Hermes MCP 客户端
```

**优点：**
- 不依赖 FastAPI 请求周期
- 可以独立部署、独立扩展
- 支持 stdio 和 HTTP 两种传输方式

**实现方式：**
- 使用 `mcp` Python 库
- 独立脚本启动：`python -m app.mcp.server`

#### 方式 B：集成到 FastAPI

```
AgentNow 后端 (FastAPI)
    │
    ├── REST API 端点
    │
    └── MCP over HTTP 端点
         │
         ▼
    Hermes MCP 客户端 (HTTP 传输)
```

**优点：**
- 部署简单，一个进程
- 共享数据库连接、配置

**缺点：**
- 只支持 HTTP 传输，不支持 stdio
- 与 FastAPI 生命周期耦合

### 3.3 推荐方案：方式 A（独立进程）

对于 Demo 版本，使用 **独立进程 + stdio 传输**：

**优点：**
- Hermes 对 stdio MCP 支持最好
- 配置简单，不需要网络端口
- 适合本地开发和测试

**配置示例（Hermes config.yaml）：**

```yaml
mcp_servers:
  agentnow_knowledge:
    command: python
    args:
      - "-m"
      - "app.mcp.server"
    env:
      DATABASE_URL: "mysql+pymysql://user:pass@localhost/agentnow"
      KNOWLEDGE_BASE_PATH: "~/.agentnow/knowledge"
```

***

## 四、数据库设计（更新版）

### 4.1 数据表结构

#### 4.1.1 知识库文档表 (knowledge_docs)

```sql
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    title VARCHAR(500) NOT NULL COMMENT '文档标题',
    file_name VARCHAR(500) COMMENT '原始文件名（上传时的文件名）',
    file_path VARCHAR(1000) NOT NULL COMMENT '存储路径（相对路径）',
    
    doc_type VARCHAR(20) DEFAULT 'markdown' COMMENT '文档类型：markdown, pdf, docx, etc.',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
    
    content_hash VARCHAR(64) COMMENT '内容哈希（SHA256），用于去重和检测变更',
    word_count INT DEFAULT 0 COMMENT '字数统计',
    char_count INT DEFAULT 0 COMMENT '字符数统计',
    
    status TINYINT DEFAULT 1 COMMENT '状态：1-正常，2-归档，3-已删除（软删除）',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开（所有用户可见）',
    
    category_id BIGINT COMMENT '分类ID',
    tags JSON COMMENT '标签列表，JSON数组格式',
    
    summary TEXT COMMENT '文档摘要/简介',
    frontmatter JSON COMMENT 'Markdown frontmatter（YAML解析后的JSON）',
    
    version INT DEFAULT 1 COMMENT '当前版本号',
    last_edited_at DATETIME COMMENT '最后编辑时间',
    last_edited_by BIGINT COMMENT '最后编辑者用户ID',
    
    created_by BIGINT NOT NULL COMMENT '创建者用户ID',
    deleted_at DATETIME COMMENT '删除时间（软删除）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_title (title),
    INDEX idx_doc_type (doc_type),
    INDEX idx_status (status),
    INDEX idx_category_id (category_id),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    INDEX idx_deleted_at (deleted_at),
    FULLTEXT INDEX idx_fulltext (title, summary, tags),
    
    FOREIGN KEY (category_id) REFERENCES knowledge_categories(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档表';
```

#### 4.1.2 知识库分类表 (knowledge_categories)

```sql
CREATE TABLE IF NOT EXISTS knowledge_categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分类ID',
    name VARCHAR(100) NOT NULL COMMENT '分类名称',
    code VARCHAR(50) NOT NULL COMMENT '分类代码（英文标识）',
    description VARCHAR(500) COMMENT '分类描述',
    parent_id BIGINT DEFAULT 0 COMMENT '父分类ID（0表示顶级分类）',
    sort_order INT DEFAULT 0 COMMENT '排序序号',
    icon VARCHAR(100) COMMENT '图标',
    color VARCHAR(20) COMMENT '颜色',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_code (code),
    INDEX idx_parent_id (parent_id),
    INDEX idx_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库分类表';
```

#### 4.1.3 知识库标签表 (knowledge_tags)

```sql
CREATE TABLE IF NOT EXISTS knowledge_tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '标签ID',
    name VARCHAR(100) NOT NULL COMMENT '标签名称',
    color VARCHAR(20) COMMENT '标签颜色',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_name (name),
    INDEX idx_usage_count (usage_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库标签表';
```

#### 4.1.4 文档-标签关联表 (knowledge_doc_tags)

```sql
CREATE TABLE IF NOT EXISTS knowledge_doc_tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
    doc_id BIGINT NOT NULL COMMENT '文档ID',
    tag_id BIGINT NOT NULL COMMENT '标签ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    UNIQUE KEY uk_doc_tag (doc_id, tag_id),
    INDEX idx_doc_id (doc_id),
    INDEX idx_tag_id (tag_id),
    
    FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES knowledge_tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档-标签关联表';
```

#### 4.1.5 文档附件表 (knowledge_attachments)

```sql
CREATE TABLE IF NOT EXISTS knowledge_attachments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '附件ID',
    doc_id BIGINT NOT NULL COMMENT '所属文档ID',
    file_name VARCHAR(500) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(1000) NOT NULL COMMENT '存储路径',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    description VARCHAR(500) COMMENT '附件描述',
    created_by BIGINT COMMENT '上传者用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_doc_id (doc_id),
    FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档附件表';
```

#### 4.1.6 文档版本历史表 (knowledge_doc_versions)

```sql
CREATE TABLE IF NOT EXISTS knowledge_doc_versions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '版本ID',
    doc_id BIGINT NOT NULL COMMENT '文档ID',
    version INT NOT NULL COMMENT '版本号',
    title VARCHAR(500) COMMENT '该版本的标题',
    content_hash VARCHAR(64) COMMENT '该版本的内容哈希',
    file_path VARCHAR(1000) COMMENT '该版本的文件路径',
    change_summary VARCHAR(500) COMMENT '变更摘要',
    created_by BIGINT COMMENT '编辑者用户ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_doc_id (doc_id),
    INDEX idx_version (version),
    FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档版本历史表';
```

#### 4.1.7 知识库配置表 (knowledge_configs)

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
('storage.base_path', '~/.agentnow/knowledge', '知识库存储根目录'),
('storage.docs_path', '~/.agentnow/knowledge/docs', '文档存储目录'),
('storage.attachments_path', '~/.agentnow/knowledge/attachments', '附件存储目录'),
('storage.versions_path', '~/.agentnow/knowledge/versions', '版本历史目录'),
('file.max_size', '104857600', '单文件最大大小（字节，默认100MB）'),
('file.allowed_types', '.md,.txt,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.csv,.json,.xml,.html,.htm', '允许上传的文件类型'),
('search.limit_default', '20', '搜索默认返回数量'),
('search.limit_max', '100', '搜索最大返回数量'),
('version.keep_count', '10', '保留的版本数量');
```

#### 4.1.8 知识库分类初始化数据

```sql
INSERT INTO knowledge_categories (name, code, description, parent_id, sort_order, icon, color) VALUES
('产品文档', 'product', '产品相关文档', 0, 1, '📋', '#3B82F6'),
('技术文档', 'tech', '技术架构、API文档', 0, 2, '⚙️', '#8B5CF6'),
('运营文档', 'operation', '运营流程、规范', 0, 3, '📊', '#10B981'),
('培训资料', 'training', '培训课程、教程', 0, 4, '🎓', '#F59E0B'),
('会议记录', 'meeting', '会议纪要、讨论', 0, 5, '📝', '#EC4899'),
('项目资料', 'project', '项目相关资料', 0, 6, '📁', '#06B6D4'),
('归档', 'archive', '归档文档', 0, 100, '🗄️', '#6B7280');
```

### 4.2 ER 图

```
┌─────────────────────────┐       ┌─────────────────────────┐
│   knowledge_categories  │       │    knowledge_docs       │
├─────────────────────────┤       ├─────────────────────────┤
│ id (PK)                 │◄──────│ category_id (FK)        │
│ name                    │       │ id (PK)                 │
│ code                    │       │ title                   │
│ parent_id               │       │ file_path               │
└─────────────────────────┘       │ doc_type                │
                                   │ status                  │
                                   │ tags (JSON)             │
                                   │ created_by (FK)         │
                                   └───────────┬─────────────┘
                                               │
                                               ├──────────────────┐
                                               │                  │
                                               ▼                  ▼
                              ┌──────────────────────┐  ┌──────────────────────┐
                              │ knowledge_doc_tags   │  │ knowledge_attachments│
                              ├──────────────────────┤  ├──────────────────────┤
                              │ id (PK)              │  │ id (PK)              │
                              │ doc_id (FK)          │◄─│ doc_id (FK)          │
                              │ tag_id (FK)          │  │ file_path            │
                              └──────────┬───────────┘  └──────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │  knowledge_tags      │
                              ├──────────────────────┤
                              │ id (PK)              │
                              │ name                 │
                              │ usage_count          │
                              └──────────────────────┘
```

***

## 五、文件存储设计

### 5.1 目录结构

```
~/.agentnow/knowledge/
├── config.yaml                    # 知识库配置文件（可选）
├── docs/                          # 文档目录
│   ├── 2024/                      # 按年分目录
│   │   ├── 2024-01-15-product-overview.md
│   │   └── ...
│   ├── 2025/
│   │   ├── 2025-01-10-tech-spec.md
│   │   └── ...
│   ├── 2026/
│   │   └── ...
│   └── archive/                   # 归档目录
│       └── ...
├── attachments/                   # 附件目录
│   ├── {doc_id}/                  # 按文档ID分目录
│   │   ├── screenshot.png
│   │   └── data.xlsx
│   └── ...
├── versions/                      # 版本历史目录
│   ├── {doc_id}/
│   │   ├── v1_20260101_120000.md
│   │   ├── v2_20260102_143000.md
│   │   └── ...
│   └── ...
├── index/                         # 搜索索引目录（可选，如使用 Whoosh）
│   ├── _MAIN_1.toc
│   └── ...
└── temp/                          # 临时文件目录
    └── ...
```

### 5.2 文档命名规范

**格式：** `{YYYY-MM-DD}-{slugified-title}.{ext}`

**示例：**
- `2026-04-28-知识库系统设计文档.md`
- `2026-04-28-product-roadmap-2026.pdf`

**优点：**
- 按日期排序，方便查找
- 标题 slug 化，避免特殊字符问题
- 可随时导入 Obsidian

### 5.3 Markdown 文档格式

推荐使用标准 Markdown + YAML Frontmatter：

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
- 标准格式，Obsidian 完全兼容
- Frontmatter 包含元数据，便于解析
- 可直接在 Obsidian 中编辑

***

## 六、后端模块设计

### 6.1 目录结构

```
backend/app/
├── models/
│   ├── __init__.py
│   ├── knowledge_doc.py           # 文档模型
│   ├── knowledge_category.py      # 分类模型
│   ├── knowledge_tag.py           # 标签模型
│   ├── knowledge_doc_tag.py       # 文档-标签关联模型
│   ├── knowledge_attachment.py    # 附件模型
│   ├── knowledge_doc_version.py   # 版本模型
│   └── knowledge_config.py        # 配置模型
├── schemas/
│   ├── __init__.py
│   └── knowledge.py               # Pydantic Schema
├── routers/
│   ├── __init__.py
│   ├── knowledge_doc.py           # 文档 API
│   ├── knowledge_category.py      # 分类 API
│   ├── knowledge_tag.py           # 标签 API
│   └── knowledge_search.py        # 搜索 API
├── services/
│   ├── __init__.py
│   ├── doc_service.py             # 文档服务
│   ├── search_service.py          # 搜索服务
│   ├── tag_service.py             # 标签服务
│   ├── category_service.py        # 分类服务
│   └── version_service.py         # 版本服务
├── mcp/
│   ├── __init__.py
│   ├── server.py                  # MCP Server 入口
│   ├── tools.py                   # MCP 工具定义
│   └── context.py                 # MCP 上下文管理
├── utils/
│   ├── __init__.py
│   ├── file_handler.py            # 文件处理工具
│   ├── markdown_parser.py         # Markdown 解析工具
│   ├── slugify.py                 # 文件名 slug 化
│   └── frontmatter.py             # Frontmatter 解析
└── main.py                        # 入口文件
```

### 6.2 REST API 设计

#### 6.2.1 文档相关 API

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/api/v1/knowledge/docs` | 获取文档列表（分页、筛选） | 登录用户 |
| GET | `/api/v1/knowledge/docs/{id}` | 获取文档详情 | 登录用户 |
| POST | `/api/v1/knowledge/docs` | 创建新文档 | 登录用户 |
| PUT | `/api/v1/knowledge/docs/{id}` | 更新文档 | 上传者/管理员 |
| DELETE | `/api/v1/knowledge/docs/{id}` | 删除文档（软删除） | 上传者/管理员 |
| POST | `/api/v1/knowledge/docs/upload` | 上传文件并创建文档 | 登录用户 |
| GET | `/api/v1/knowledge/docs/{id}/download` | 下载文档 | 登录用户 |
| GET | `/api/v1/knowledge/docs/{id}/versions` | 获取版本历史 | 登录用户 |
| POST | `/api/v1/knowledge/docs/{id}/restore/{version_id}` | 恢复到指定版本 | 上传者/管理员 |

#### 6.2.2 搜索相关 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/knowledge/search` | 搜索文档（关键词、标签、分类） |
| POST | `/api/v1/knowledge/search/advanced` | 高级搜索 |

#### 6.2.3 标签相关 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/knowledge/tags` | 获取所有标签（含使用计数） |
| POST | `/api/v1/knowledge/tags` | 创建新标签 |
| DELETE | `/api/v1/knowledge/tags/{id}` | 删除标签 |

#### 6.2.4 分类相关 API

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/v1/knowledge/categories` | 获取所有分类（树形结构） |
| POST | `/api/v1/knowledge/categories` | 创建分类 |
| PUT | `/api/v1/knowledge/categories/{id}` | 更新分类 |
| DELETE | `/api/v1/knowledge/categories/{id}` | 删除分类 |

### 6.3 MCP Server 实现

#### 6.3.1 核心代码结构

```python
# app/mcp/server.py

from mcp.server import Server
from mcp.server.stdio import stdio_server
from app.mcp.tools import KnowledgeTools
from app.core.config import get_settings
import asyncio

server = Server("agentnow-knowledge")

@server.list_tools()
async def list_tools():
    return KnowledgeTools.get_tool_definitions()

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    tools = KnowledgeTools()
    return await tools.execute(name, arguments)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
```

#### 6.3.2 工具实现

```python
# app/mcp/tools.py

from typing import Any, Dict, List, Optional
from app.services.doc_service import DocService
from app.services.search_service import SearchService
from app.schemas.knowledge import (
    KnowledgeDocCreate, KnowledgeDocUpdate,
    KnowledgeDocResponse, SearchResult
)

class KnowledgeTools:
    def __init__(self):
        self.doc_service = DocService()
        self.search_service = SearchService()
    
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        return [
            {
                "name": "knowledge_search",
                "description": "搜索知识库中的文档。支持关键词、标签、分类筛选。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词（标题、内容、标签）"
                        },
                        "category": {
                            "type": "string",
                            "description": "分类代码，如：tech, product, operation"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标签列表，多个标签为 AND 关系"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量限制，默认 10",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "knowledge_get",
                "description": "获取单个文档的完整内容。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "integer",
                            "description": "文档 ID"
                        }
                    },
                    "required": ["doc_id"]
                }
            },
            {
                "name": "knowledge_list",
                "description": "列出文档。可按分类、标签筛选，按时间排序。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "分类代码"
                        },
                        "tag": {
                            "type": "string",
                            "description": "标签名称"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回数量限制，默认 20",
                            "default": 20
                        },
                        "sort_by": {
                            "type": "string",
                            "description": "排序方式：created_at, updated_at, title",
                            "default": "updated_at"
                        }
                    }
                }
            },
            {
                "name": "knowledge_create",
                "description": "创建新文档。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "文档标题"
                        },
                        "content": {
                            "type": "string",
                            "description": "文档内容（Markdown 格式）"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标签列表"
                        },
                        "category": {
                            "type": "string",
                            "description": "分类代码"
                        },
                        "summary": {
                            "type": "string",
                            "description": "文档摘要"
                        }
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "knowledge_update",
                "description": "更新现有文档。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "integer",
                            "description": "文档 ID"
                        },
                        "title": {
                            "type": "string",
                            "description": "新标题（可选）"
                        },
                        "content": {
                            "type": "string",
                            "description": "新内容（可选）"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "新标签列表（可选）"
                        },
                        "change_summary": {
                            "type": "string",
                            "description": "变更摘要"
                        }
                    },
                    "required": ["doc_id"]
                }
            },
            {
                "name": "knowledge_delete",
                "description": "删除文档（软删除，可恢复）。",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "doc_id": {
                            "type": "integer",
                            "description": "文档 ID"
                        }
                    },
                    "required": ["doc_id"]
                }
            },
            {
                "name": "knowledge_tags",
                "description": "获取所有标签及其使用计数。",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "knowledge_categories",
                "description": "获取所有分类。",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "knowledge_search": self._handle_search,
            "knowledge_get": self._handle_get,
            "knowledge_list": self._handle_list,
            "knowledge_create": self._handle_create,
            "knowledge_update": self._handle_update,
            "knowledge_delete": self._handle_delete,
            "knowledge_tags": self._handle_tags,
            "knowledge_categories": self._handle_categories,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return await handler(arguments)
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")
        category = args.get("category")
        tags = args.get("tags", [])
        limit = args.get("limit", 10)
        
        results = await self.search_service.search(
            query=query,
            category=category,
            tags=tags,
            limit=limit
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": self._format_search_results(results)
                }
            ]
        }
    
    async def _handle_get(self, args: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = args["doc_id"]
        doc = await self.doc_service.get_by_id(doc_id)
        
        if not doc:
            return {"content": [{"type": "text", "text": f"文档不存在: ID={doc_id}"}]}
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": self._format_doc_detail(doc)
                }
            ]
        }
    
    # ... 其他处理方法
    
    def _format_search_results(self, results: List[SearchResult]) -> str:
        lines = ["搜索结果：", ""]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. 【{r.title}】(ID: {r.doc_id})")
            lines.append(f"   分类: {r.category} | 标签: {', '.join(r.tags)}")
            lines.append(f"   摘要: {r.summary[:150]}...")
            lines.append(f"   更新时间: {r.updated_at}")
            lines.append("")
        return "\n".join(lines)
    
    def _format_doc_detail(self, doc: KnowledgeDocResponse) -> str:
        lines = [
            f"# {doc.title}",
            "",
            f"ID: {doc.id}",
            f"分类: {doc.category}",
            f"标签: {', '.join(doc.tags)}",
            f"字数: {doc.word_count} 字",
            f"最后更新: {doc.updated_at}",
            "",
            "---",
            "",
            doc.content  # 完整内容
        ]
        return "\n".join(lines)
```

***

## 七、前端模块设计

### 7.1 页面结构

```
知识库模块
├── 文档列表页 (/knowledge/docs)
│   ├── 顶部搜索栏
│   │   ├── 搜索框
│   │   ├── 分类筛选
│   │   ├── 标签筛选
│   │   └── 新建/上传按钮
│   ├── 文档列表
│   │   ├── 列表视图
│   │   └── 网格视图
│   └── 分页组件
├── 文档详情页 (/knowledge/docs/:id)
│   ├── 文档内容展示
│   ├── 元数据信息
│   ├── 操作按钮（编辑、删除、下载、版本历史）
│   └── 相关文档推荐
├── 文档编辑页 (/knowledge/docs/:id/edit)
│   ├── Markdown 编辑器
│   ├── 元数据编辑（标签、分类、摘要）
│   └── 保存/取消按钮
├── 分类管理页 (/knowledge/categories)
│   └── 分类树形管理
└── 标签管理页 (/knowledge/tags)
    └── 标签云管理
```

### 7.2 核心组件

| 组件 | 路径 | 功能 |
|------|------|------|
| DocList | `views/knowledge/DocList.vue` | 文档列表页面 |
| DocDetail | `views/knowledge/DocDetail.vue` | 文档详情页面 |
| DocEditor | `views/knowledge/DocEditor.vue` | 文档编辑器 |
| SearchBar | `components/knowledge/SearchBar.vue` | 搜索栏组件 |
| DocCard | `components/knowledge/DocCard.vue` | 文档卡片组件 |
| DocListItem | `components/knowledge/DocListItem.vue` | 文档列表项组件 |
| TagSelector | `components/knowledge/TagSelector.vue` | 标签选择器 |
| CategorySelector | `components/knowledge/CategorySelector.vue` | 分类选择器 |
| MarkdownEditor | `components/common/MarkdownEditor.vue` | Markdown 编辑器 |
| MarkdownViewer | `components/common/MarkdownViewer.vue` | Markdown 渲染器 |

### 7.3 API 模块

```typescript
// frontend/src/api/knowledge.ts

import request from './http'

export interface KnowledgeDoc {
  id: number
  title: string
  content?: string
  summary: string
  doc_type: string
  category: string
  category_id: number
  tags: string[]
  word_count: number
  char_count: number
  status: number
  is_public: boolean
  version: number
  created_by: number
  last_edited_by: number
  last_edited_at: string
  created_at: string
  updated_at: string
}

export interface DocListParams {
  page?: number
  page_size?: number
  keyword?: string
  category?: string
  tag?: string
  status?: number
  sort_by?: 'created_at' | 'updated_at' | 'title'
  sort_order?: 'asc' | 'desc'
}

export interface DocListResponse {
  items: KnowledgeDoc[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SearchResult {
  doc_id: number
  title: string
  summary: string
  category: string
  tags: string[]
  score: number
  updated_at: string
}

export const knowledgeApi = {
  getDocs: (params: DocListParams) => 
    request.get<DocListResponse>('/knowledge/docs', { params }),
  
  getDoc: (id: number) =>
    request.get<KnowledgeDoc>(`/knowledge/docs/${id}`),
  
  createDoc: (data: Partial<KnowledgeDoc> & { content: string }) =>
    request.post<KnowledgeDoc>('/knowledge/docs', data),
  
  updateDoc: (id: number, data: Partial<KnowledgeDoc>) =>
    request.put<KnowledgeDoc>(`/knowledge/docs/${id}`, data),
  
  deleteDoc: (id: number) =>
    request.delete(`/knowledge/docs/${id}`),
  
  uploadFile: (formData: FormData, onProgress?: (percent: number) => void) =>
    request.post<KnowledgeDoc>('/knowledge/docs/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      }
    }),
  
  downloadDoc: (id: number) =>
    request.get(`/knowledge/docs/${id}/download`, { responseType: 'blob' }),
  
  search: (query: string, options?: { category?: string; tags?: string[]; limit?: number }) =>
    request.get<SearchResult[]>('/knowledge/search', {
      params: {
        q: query,
        ...options
      }
    }),
  
  getCategories: () =>
    request.get('/knowledge/categories'),
  
  getTags: () =>
    request.get('/knowledge/tags'),
}
```

***

## 八、权限设计

### 8.1 权限码设计

| 权限名称 | 权限码 | 类型 | 路径 | 说明 |
|----------|--------|------|------|------|
| 文档查询 | `knowledge:doc:query` | 3 | GET /api/v1/knowledge/docs | 查看文档列表 |
| 文档详情 | `knowledge:doc:detail` | 3 | GET /api/v1/knowledge/docs/:id | 查看文档详情 |
| 文档创建 | `knowledge:doc:create` | 3 | POST /api/v1/knowledge/docs | 创建文档 |
| 文档编辑 | `knowledge:doc:update` | 3 | PUT /api/v1/knowledge/docs/:id | 编辑文档 |
| 文档删除 | `knowledge:doc:delete` | 3 | DELETE /api/v1/knowledge/docs/:id | 删除文档 |
| 文档上传 | `knowledge:doc:upload` | 3 | POST /api/v1/knowledge/docs/upload | 上传文件 |
| 文档下载 | `knowledge:doc:download` | 3 | GET /api/v1/knowledge/docs/:id/download | 下载文档 |
| 分类管理 | `knowledge:category:manage` | 3 | /api/v1/knowledge/categories/* | 分类增删改 |
| 标签管理 | `knowledge:tag:manage` | 3 | /api/v1/knowledge/tags/* | 标签增删改 |
| 配置管理 | `knowledge:config:manage` | 3 | /api/v1/knowledge/configs | 知识库配置 |

### 8.2 角色权限分配

| 角色 | 权限 |
|------|------|
| 超级管理员 | 所有权限 |
| 系统管理员 | `knowledge:doc:*`, `knowledge:category:*`, `knowledge:tag:*`, `knowledge:config:*` |
| 知识库管理员 | `knowledge:doc:*`, `knowledge:category:*`, `knowledge:tag:*` |
| 普通用户 | `knowledge:doc:query`, `knowledge:doc:detail`, `knowledge:doc:create`, `knowledge:doc:download` |

### 8.3 数据权限规则

| 操作 | 权限规则 |
|------|----------|
| 查看公开文档 | 所有登录用户可查看 |
| 查看非公开文档 | 文档创建者 + 管理员 |
| 编辑文档 | 文档创建者 + 管理员 |
| 删除文档 | 文档创建者 + 管理员 |
| 创建文档 | 所有登录用户 |

### 8.4 MCP 访问权限

**重要：** MCP Server 的访问权限设计

| 场景 | 权限策略 |
|------|----------|
| 读取操作（search, get, list, tags, categories） | 所有智能体可访问（全局知识库共享） |
| 写入操作（create, update, delete） | 需要验证（可配置是否允许） |

**推荐策略（Demo 版本）：**
- 允许所有读取操作（search, get, list）
- 允许创建操作（智能体可以新增知识）
- 限制更新/删除操作（需要确认机制）

**配置项：**
```yaml
# ~/.hermes/config.yaml 中的 MCP 配置
mcp_servers:
  agentnow_knowledge:
    command: python
    args: ["-m", "app.mcp.server"]
    env:
      # 控制 MCP 权限
      MCP_ALLOW_READ: "true"
      MCP_ALLOW_CREATE: "true"
      MCP_ALLOW_UPDATE: "false"  # Demo 版本禁用
      MCP_ALLOW_DELETE: "false"  # Demo 版本禁用
```

***

## 九、安装与配置指南

### 9.1 系统要求

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.11+ | 后端运行环境 |
| Node.js | 18+ | 前端构建 |
| MySQL | 8.0+ | 数据库 |
| Hermes | v0.7.0+ | MCP 支持 |

### 9.2 后端安装步骤

#### 步骤 1：安装 Python 依赖

```bash
cd backend

# 安装基础依赖
pip install -r requirements.txt

# 安装 MCP 相关依赖
pip install mcp fastembed
```

#### 步骤 2：创建数据库表

```bash
# 执行数据库初始化脚本
mysql -u root -p agentnow < data/database.sql

# 或单独执行知识库表创建
mysql -u root -p agentnow < data/knowledge_schema.sql
```

#### 步骤 3：创建存储目录

```bash
# 创建知识库存储目录
mkdir -p ~/.agentnow/knowledge/docs
mkdir -p ~/.agentnow/knowledge/attachments
mkdir -p ~/.agentnow/knowledge/versions
mkdir -p ~/.agentnow/knowledge/temp

# 确认目录权限
chmod -R 755 ~/.agentnow/knowledge/
```

#### 步骤 4：配置环境变量

```bash
# 在 .env 文件中添加
KNOWLEDGE_BASE_PATH=~/.agentnow/knowledge
KNOWLEDGE_MAX_FILE_SIZE=104857600

# MCP 配置
MCP_ALLOW_READ=true
MCP_ALLOW_CREATE=true
MCP_ALLOW_UPDATE=false
MCP_ALLOW_DELETE=false
```

#### 步骤 5：启动后端服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用启动脚本
python main.py
```

### 9.3 前端安装步骤

```bash
cd frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

### 9.4 Hermes 集成配置

#### 步骤 1：配置 MCP Server

编辑 `~/.hermes/config.yaml`：

```yaml
mcp_servers:
  agentnow_knowledge:
    command: python
    args:
      - "-m"
      - "app.mcp.server"
    env:
      # 数据库连接（如果需要）
      DATABASE_URL: "mysql+pymysql://root:password@localhost/agentnow"
      # 知识库路径
      KNOWLEDGE_BASE_PATH: "/Users/yourname/.agentnow/knowledge"
      # 权限控制
      MCP_ALLOW_READ: "true"
      MCP_ALLOW_CREATE: "true"
      MCP_ALLOW_UPDATE: "false"
      MCP_ALLOW_DELETE: "false"
    
    # 工作目录（指向 AgentNow backend）
    cwd: "/Users/yourname/code/AgentNow/backend"
```

#### 步骤 2：验证 MCP 连接

```bash
# 启动 Hermes
hermes

# 在对话中测试
> 查看可用的 MCP 工具
> 搜索知识库中的"产品文档"
```

#### 步骤 3：测试 MCP 工具

在 Hermes 对话中尝试：

```
用户：搜索知识库中关于"产品"的文档

Hermes 应该：
1. 调用 knowledge_search 工具
2. 返回匹配的文档列表
3. 根据需要调用 knowledge_get 获取详细内容
```

### 9.5 可选：Obsidian 集成

如果您想使用 Obsidian 编辑文档：

#### 步骤 1：创建符号链接

```bash
# 将 AgentNow 的文档目录链接到 Obsidian Vault
ln -s ~/.agentnow/knowledge/docs ~/Obsidian/Vaults/AgentNow-Knowledge
```

#### 步骤 2：Obsidian 配置

1. 打开 Obsidian
2. 打开 Vault：`~/Obsidian/Vaults/AgentNow-Knowledge`
3. 安装推荐插件：
   - **Dataview**：高级查询
   - **Templater**：模板管理
   - **Tag Wrangler**：标签管理

#### 步骤 3：同步注意事项

- **AgentNow → Obsidian**：实时（文件系统共享）
- **Obsidian → AgentNow**：实时（文件系统共享）
- **数据库同步**：需要配置文件监听（后续版本）

### 9.6 验证清单

| 检查项 | 命令/操作 | 预期结果 |
|--------|-----------|----------|
| 后端服务 | `curl http://localhost:8000/health` | 返回 `{"status": "ok"}` |
| 前端服务 | 浏览器访问 `http://localhost:5173` | 正常显示 |
| 数据库连接 | 后端启动日志 | 无连接错误 |
| 存储目录 | `ls -la ~/.agentnow/knowledge/` | 目录存在 |
| MCP 配置 | `hermes tools` | 显示 AgentNow 工具 |
| MCP 搜索 | Hermes 中说"搜索知识库" | 调用工具并返回结果 |

***

## 十、开发计划

### 10.1 版本规划

| 版本 | 功能 | 优先级 | 状态 |
|------|------|--------|------|
| **v2.0 (当前)** | 基础 CRUD + MCP Server | P0 | 设计中 |
| v2.1 | 全文搜索 | P1 | 待开发 |
| v2.2 | 版本管理 | P2 | 待开发 |
| v2.3 | 标签云 + 分类管理 | P2 | 待开发 |
| v2.4 | Obsidian 同步优化 | P3 | 待开发 |
| v2.5 | 权限细化 + 分享功能 | P3 | 待开发 |

### 10.2 v2.0 详细开发任务

#### 后端任务

| 任务 | 描述 | 预估工作量 |
|------|------|------------|
| 数据库模型 | 创建所有知识相关模型 | 0.5 天 |
| Schema 定义 | Pydantic Schema | 0.5 天 |
| 文档服务 | DocService CRUD | 1 天 |
| 标签服务 | TagService | 0.5 天 |
| 分类服务 | CategoryService | 0.5 天 |
| REST API | 所有路由 | 1 天 |
| MCP Server | MCP 工具实现 | 1 天 |
| 文件处理工具 | 上传、下载、Markdown 解析 | 0.5 天 |
| 权限集成 | 与现有权限系统集成 | 0.5 天 |

#### 前端任务

| 任务 | 描述 | 预估工作量 |
|------|------|------------|
| 类型定义 | TypeScript 接口 | 0.5 天 |
| API 模块 | knowledge.ts | 0.5 天 |
| 文档列表页 | DocList.vue | 1 天 |
| 文档详情页 | DocDetail.vue | 0.5 天 |
| 文档编辑器 | DocEditor.vue | 1 天 |
| Markdown 组件 | Editor/Viewer | 0.5 天 |
| 路由配置 | 新增路由 | 0.5 天 |

#### 集成任务

| 任务 | 描述 | 预估工作量 |
|------|------|------------|
| MCP 测试 | Hermes MCP 连接测试 | 0.5 天 |
| 文档整理 | 安装配置文档 | 0.5 天 |

### 10.3 总预估

| 阶段 | 工作量 |
|------|--------|
| 后端开发 | 约 6 天 |
| 前端开发 | 约 4.5 天 |
| 集成测试 | 约 1 天 |
| **总计** | **约 11.5 天** |

***

## 十一、风险与注意事项

### 11.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| MCP 版本兼容性 | Hermes 和 mcp 库版本不匹配 | 使用 Hermes 文档中推荐的版本 |
| 文件系统权限 | 读写权限问题 | 启动前检查目录权限 |
| 数据库连接池 | 并发连接问题 | 配置连接池大小 |
| 大文件上传 | 内存溢出 | 使用流式上传、分块上传 |

### 11.2 安全注意事项

| 关注点 | 措施 |
|--------|------|
| 文件类型验证 | 严格验证 MIME 类型和扩展名 |
| 文件大小限制 | 配置最大文件大小 |
| 路径遍历攻击 | 规范化文件路径，禁止 `..` |
| 恶意文件 | 生产环境集成病毒扫描 |
| MCP 写入权限 | Demo 版本限制 update/delete |

### 11.3 与现有系统集成

| 系统 | 集成点 | 说明 |
|------|---------|------|
| 用户系统 | `created_by`, `last_edited_by` | 使用现有用户表 |
| 权限系统 | 权限码 + 角色 | 使用现有权限框架 |
| 配置系统 | 环境变量 | 使用现有配置管理 |
| 日志系统 | 操作日志 | 使用现有日志框架 |

***

## 十二、总结

### 12.1 核心设计要点

1. **不依赖第三方**：不依赖 Hermes 未实现功能，不依赖 Obsidian GUI
2. **MCP 标准协议**：Hermes 可直接连接，智能体自主调用
3. **文件系统存储**：Markdown 文件，可随时导入 Obsidian
4. **全局共享**：所有智能体可访问知识库
5. **个人记忆隔离**：Hermes MEMORY.md 保持独立

### 12.2 架构优势

| 优势 | 说明 |
|------|------|
| **解耦** | AgentNow 管理知识库，Hermes 只调用 |
| **标准** | MCP 协议，未来可扩展其他智能体 |
| **开放** | Markdown 文件，不锁定数据格式 |
| **灵活** | 可独立部署、独立扩展 |
| **简单** | Demo 版本，核心闭环即可 |

### 12.3 下一步

1. **确认方案**：您确认此设计方案
2. **开始开发**：按开发计划实现
3. **测试验证**：Hermes MCP 连接测试
4. **文档完善**：安装配置指南

***

> 本文档为基于 MCP 的知识库系统设计方案 v2.0。核心思想是：AgentNow 管理知识库，通过 MCP 协议让 Hermes 智能体自主访问。实现全局知识共享、个人记忆隔离的双层架构。
