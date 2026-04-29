# 知识库功能配置与使用手册

> 版本：v1.0
> 日期：2026-04-28
> 状态：已完成

---

## 一、概述

本文档详细说明 AgentNow 知识库功能的配置方法、使用方法和测试步骤。知识库功能采用以下架构：

- **文件存储**：`~/.agentnow/knowledge/docs/`（与 mcp-markdown-vault 共享）
- **MCP Server**：`@wirux/mcp-markdown-vault`（提供语义搜索和文件操作）
- **后端服务**：AgentNow FastAPI 服务（提供用户认证、权限控制、元数据管理）
- **智能体调用**：Hermes 通过 MCP 协议调用知识库功能

---

## 二、环境准备

### 2.1 目录结构确认

知识库目录已创建，结构如下：

```
~/.agentnow/
└── knowledge/
    └── docs/          # 文档存储目录（与 mcp-markdown-vault 共享）
```

### 2.2 数据库确认

数据库已更新，包含以下表：
- `knowledge_docs` - 知识库文档表
- `knowledge_configs` - 知识库配置表

数据库初始化脚本位置：`AgentNow/backend/data/database.sql`

---

## 三、Hermes MCP 连接配置

### 3.1 配置方法

编辑 Hermes 配置文件 `~/.hermes/config.yaml`，添加 MCP 服务器配置：

```yaml
mcp_servers:
  agentnow_knowledge:
    command: npx
    args:
      - "-y"
      - "@wirux/mcp-markdown-vault"
    env:
      VAULT_PATH: "/Users/victor/.agentnow/knowledge/docs"
```

**配置说明：**
- `command`：启动命令，使用 `npx`
- `args`：命令参数，`-y` 表示自动确认安装，`@wirux/mcp-markdown-vault` 是包名
- `env.VAULT_PATH`：知识库目录的绝对路径

### 3.2 配置位置

配置文件路径：`~/.hermes/config.yaml`

**注意：** 由于权限限制，需要手动编辑此文件。请使用文本编辑器打开并添加上述配置。

### 3.3 配置验证

配置完成后，启动 Hermes 时会自动加载 MCP 服务器。验证方法见"测试方法"章节。

---

## 四、后端服务配置与启动

### 4.1 后端服务结构

后端服务位于 `AgentNow/backend/` 目录，主要文件：

```
backend/
├── app/
│   ├── main.py                    # 主入口文件
│   ├── config.py                  # 配置文件
│   ├── models/
│   │   ├── __init__.py
│   │   └── knowledge_doc.py       # 知识库文档模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── knowledge.py           # 数据验证模型
│   ├── services/
│   │   ├── __init__.py
│   │   └── knowledge_service.py   # 知识库服务
│   ├── routers/
│   │   ├── __init__.py
│   │   └── knowledge.py           # API 路由
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py        # 文件处理工具
├── data/
│   └── database.sql               # 数据库初始化脚本
├── pyproject.toml                 # 依赖配置
└── .env.example                   # 环境变量示例
```

### 4.2 环境变量配置

复制 `.env.example` 为 `.env` 并根据实际情况修改：

```bash
cd AgentNow/backend
cp .env.example .env
```

**主要配置项：**

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `mysql+pymysql://root:password@localhost:3306/agentnow` |
| `JWT_SECRET_KEY` | JWT 密钥 | `your-secret-key-change-in-production` |
| `SERVER_PORT` | 服务端口 | `5116` |
| `KNOWLEDGE_BASE_PATH` | 知识库路径 | `~/.agentnow/knowledge/docs` |

### 4.3 依赖安装

使用 `uv` 或 `pip` 安装依赖：

```bash
cd AgentNow/backend

# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -r requirements.txt
```

**依赖列表：**
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `sqlalchemy` - ORM 框架
- `pymysql` - MySQL 驱动
- `pydantic` - 数据验证
- `python-jose` - JWT 处理
- `bcrypt` - 密码加密
- `python-multipart` - 文件上传

### 4.4 启动后端服务

#### 开发模式（带热重载）

```bash
cd AgentNow/backend

# 使用 uv
uv run uvicorn app.main:app --reload --port 5116

# 或直接运行
python -m app.main
```

#### 生产模式

```bash
cd AgentNow/backend
uvicorn app.main:app --host 0.0.0.0 --port 5116
```

### 4.5 服务验证

启动后访问以下地址验证服务：

| 地址 | 说明 |
|------|------|
| `http://localhost:5116/` | 根路径，返回服务信息 |
| `http://localhost:5116/health` | 健康检查 |
| `http://localhost:5116/docs` | Swagger API 文档 |
| `http://localhost:5116/redoc` | ReDoc API 文档 |

---

## 五、API 使用方法

### 5.1 认证

所有 API 都需要 Bearer Token 认证。首先获取访问令牌：

**登录接口：**
```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=123456
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**使用 Token：**
在请求头中添加：
```
Authorization: Bearer <access_token>
```

### 5.2 知识库 API 列表

#### 5.2.1 文档管理

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/api/v1/knowledge/docs` | 获取文档列表 | `knowledge:doc:query` |
| GET | `/api/v1/knowledge/docs/{id}` | 获取文档详情 | `knowledge:doc:detail` |
| POST | `/api/v1/knowledge/docs` | 上传文件 | `knowledge:doc:create` |
| POST | `/api/v1/knowledge/docs/markdown` | 创建 Markdown | `knowledge:doc:create` |
| PUT | `/api/v1/knowledge/docs/{id}` | 更新元数据 | `knowledge:doc:update` |
| PUT | `/api/v1/knowledge/docs/{id}/content` | 更新内容 | `knowledge:doc:update` |
| DELETE | `/api/v1/knowledge/docs/{id}` | 删除文档 | `knowledge:doc:delete` |
| GET | `/api/v1/knowledge/docs/{id}/download` | 下载文档 | `knowledge:doc:download` |

#### 5.2.2 分类与标签

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/api/v1/knowledge/categories` | 获取所有分类 | `knowledge:doc:query` |
| GET | `/api/v1/knowledge/tags` | 获取所有标签 | `knowledge:doc:query` |

#### 5.2.3 统计与配置

| 方法 | 路径 | 描述 | 权限 |
|------|------|------|------|
| GET | `/api/v1/knowledge/statistics` | 获取统计信息 | `knowledge:config:view` |
| GET | `/api/v1/knowledge/storage` | 获取存储信息 | `knowledge:config:view` |
| GET | `/api/v1/knowledge/configs` | 获取配置列表 | `knowledge:config:view` |
| PUT | `/api/v1/knowledge/configs/{id}` | 更新配置 | `knowledge:config:edit` |

### 5.3 API 使用示例

#### 示例 1：获取文档列表

```bash
curl -X GET "http://localhost:5116/api/v1/knowledge/docs?page=1&page_size=20" \
  -H "Authorization: Bearer <token>"
```

#### 示例 2：上传文件

```bash
curl -X POST "http://localhost:5116/api/v1/knowledge/docs" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "title=测试文档" \
  -F "description=这是一个测试文档" \
  -F "tags=[\"测试\",\"示例\"]" \
  -F "category=tech" \
  -F "is_public=true" \
  -F "file=@/path/to/document.pdf"
```

#### 示例 3：创建 Markdown 文档

```bash
curl -X POST "http://localhost:5116/api/v1/knowledge/docs/markdown" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: multipart/form-data" \
  -F "title=设计文档" \
  -F "description=系统设计说明" \
  -F "tags=[\"设计\",\"架构\"]" \
  -F "category=tech" \
  -F "content=# 系统设计\n\n## 概述\n\n这是系统设计文档..." \
  -F "filename=system-design"
```

#### 示例 4：更新文档内容

```bash
curl -X PUT "http://localhost:5116/api/v1/knowledge/docs/1/content" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# 更新后的标题\n\n这是更新后的内容..."
  }'
```

#### 示例 5：获取统计信息

```bash
curl -X GET "http://localhost:5116/api/v1/knowledge/statistics" \
  -H "Authorization: Bearer <token>"
```

---

## 六、测试方法

### 6.1 测试前准备

1. **确保 MySQL 数据库运行**
   - 数据库名：`agentnow`
   - 已执行 `database.sql` 初始化脚本

2. **确保知识库目录存在**
   ```bash
   ls -la ~/.agentnow/knowledge/docs/
   ```

3. **安装依赖**
   ```bash
   cd AgentNow/backend
   uv sync
   ```

### 6.2 后端服务测试

#### 步骤 1：启动后端服务

```bash
cd AgentNow/backend
uv run uvicorn app.main:app --reload --port 5116
```

#### 步骤 2：验证服务启动

打开浏览器访问：
- `http://localhost:5116/` - 应返回服务信息
- `http://localhost:5116/health` - 应返回健康状态
- `http://localhost:5116/docs` - 应显示 Swagger 文档

#### 步骤 3：测试 API（使用 Swagger UI）

1. 打开 `http://localhost:5116/docs`
2. 点击 **Authorize** 按钮
3. 使用测试账号登录：
   - 用户名：`admin`
   - 密码：`123456`
4. 测试各个 API 端点

#### 步骤 4：测试文件上传

1. 在 Swagger UI 中找到 `POST /api/v1/knowledge/docs`
2. 填写参数：
   - `title`: 测试文档
   - `description`: 这是一个测试
   - `tags`: `["测试"]`
   - `category`: `test`
   - `file`: 选择一个本地文件
3. 点击 **Execute** 执行
4. 验证返回结果

### 6.3 MCP 服务测试

#### 步骤 1：验证 MCP 配置

检查 Hermes 配置文件：
```bash
cat ~/.hermes/config.yaml | grep -A 10 "mcp_servers"
```

应看到类似输出：
```yaml
mcp_servers:
  agentnow_knowledge:
    command: npx
    args:
      - "-y"
      - "@wirux/mcp-markdown-vault"
    env:
      VAULT_PATH: "/Users/victor/.agentnow/knowledge/docs"
```

#### 步骤 2：测试 mcp-markdown-vault

直接测试 MCP Server 是否可用：

```bash
# 测试 npx 是否能找到包
VAULT_PATH=~/.agentnow/knowledge/docs npx @wirux/mcp-markdown-vault --help
```

**注意：** 第一次运行时，`npx` 会自动下载 `@wirux/mcp-markdown-vault` 包。

#### 步骤 3：测试 Hermes 集成

1. 启动 Hermes：
   ```bash
   hermes
   ```

2. 在对话中测试知识库功能：

   **测试搜索：**
   ```
   搜索知识库中关于产品介绍的文档
   ```

   **测试读取：**
   ```
   读取知识库中的测试文档
   ```

   **测试创建：**
   ```
   在知识库中创建一个新文档，标题是：测试文档，内容是：这是一个测试文档
   ```

### 6.4 完整测试流程

#### 测试场景 1：文档上传与检索

1. **通过 AgentNow 上传文档**
   - 使用 API 或前端界面上传一个 Markdown 文档
   - 文档保存在 `~/.agentnow/knowledge/docs/`

2. **通过 Hermes 搜索文档**
   - 在 Hermes 中询问："搜索知识库中的文档"
   - 验证是否能找到刚上传的文档

3. **通过 Hermes 读取文档**
   - 在 Hermes 中询问："读取知识库中的 XXXX 文档"
   - 验证是否能正确读取文档内容

#### 测试场景 2：权限控制

1. **使用普通用户登录**
   - 尝试编辑其他用户创建的文档
   - 验证是否被拒绝

2. **使用管理员登录**
   - 尝试编辑任何文档
   - 验证是否有权限

### 6.5 故障排查

#### 问题 1：后端服务无法启动

**可能原因：**
- 数据库连接失败
- 依赖未安装
- 端口被占用

**排查方法：**
```bash
# 检查数据库连接
mysql -u root -p -e "SHOW DATABASES LIKE 'agentnow';"

# 检查端口占用
lsof -i :5116

# 查看详细错误日志
uv run uvicorn app.main:app --reload --port 5116 --log-level debug
```

#### 问题 2：MCP 服务无法加载

**可能原因：**
- 配置格式错误
- `npx` 不可用
- 包下载失败

**排查方法：**
```bash
# 检查 npx 是否可用
npx --version

# 手动安装包
npm install -g @wirux/mcp-markdown-vault

# 检查配置文件语法
yamllint ~/.hermes/config.yaml
```

#### 问题 3：文件上传失败

**可能原因：**
- 目录权限不足
- 文件类型不允许
- 文件大小超过限制

**排查方法：**
```bash
# 检查目录权限
ls -la ~/.agentnow/knowledge/

# 检查配置的允许类型
# 查看 KNOWLEDGE_ALLOWED_TYPES 配置

# 检查文件大小限制
# 查看 KNOWLEDGE_MAX_FILE_SIZE 配置
```

---

## 七、默认账号与权限

### 7.1 默认管理员账号

| 项目 | 值 |
|------|-----|
| 登录名 | `admin` |
| 手机号 | `13651165117` |
| 密码 | `123456` |
| 角色 | 超级管理员 |

**注意：** 首次登录后必须修改密码。

### 7.2 权限矩阵

| 权限码 | 权限名称 | 超级管理员 | 系统管理员 | 普通用户 |
|--------|----------|-------------|-----------|---------|
| `knowledge:doc:query` | 文档查询 | ✅ | ✅ | ✅ |
| `knowledge:doc:detail` | 文档详情 | ✅ | ✅ | ✅ |
| `knowledge:doc:create` | 文档上传/创建 | ✅ | ✅ | ✅ |
| `knowledge:doc:update` | 文档编辑 | ✅ | ✅ | ⚠️ 仅自己 |
| `knowledge:doc:delete` | 文档删除 | ✅ | ✅ | ⚠️ 仅自己 |
| `knowledge:doc:download` | 文档下载 | ✅ | ✅ | ✅ |
| `knowledge:config:view` | 配置查看 | ✅ | ✅ | ❌ |
| `knowledge:config:edit` | 配置编辑 | ✅ | ✅ | ❌ |

---

## 八、配置项说明

### 8.1 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接字符串 | `mysql+pymysql://root:password@localhost:3306/agentnow` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `your-secret-key-change-in-production` |
| `SERVER_PORT` | 服务端口 | `5116` |
| `KNOWLEDGE_BASE_PATH` | 知识库根目录 | `~/.agentnow/knowledge/docs` |
| `KNOWLEDGE_MAX_FILE_SIZE` | 单文件最大大小（字节） | `104857600` (100MB) |
| `KNOWLEDGE_ALLOWED_TYPES` | 允许的文件类型 | `.pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml` |

### 8.2 数据库配置

知识库配置存储在 `knowledge_configs` 表中：

| config_key | 默认值 | 说明 |
|------------|--------|------|
| `storage.base_path` | `~/.agentnow/knowledge/docs` | 知识库存储根目录 |
| `file.max_size` | `104857600` | 单文件最大大小（字节） |
| `file.allowed_types` | 多种类型 | 允许上传的文件类型 |
| `mcp.enabled` | `true` | 是否启用 MCP 服务 |

---

## 九、架构说明

### 9.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentNow 前端                              │
│                   (知识库管理界面 - Vue3)                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼ REST API
┌─────────────────────────────────────────────────────────────────┐
│                        AgentNow 后端                              │
│                                                                   │
│  职责：                                                           │
│  - 用户认证、权限控制                                              │
│  - 文档元数据管理（MySQL）                                         │
│  - 文件系统操作（直接读写 ~/.agentnow/knowledge/docs/）           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ├───► 文件系统：~/.agentnow/knowledge/docs/
                                │              (AgentNow 与 mcp-markdown-vault 共享)
                                │
                                │ MCP (stdio)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   @wirux/mcp-markdown-vault                       │
│                         (MCP Server)                              │
│                                                                   │
│  核心特性：                                                        │
│  - 混合检索：向量相似度 + TF-IDF + 词邻近度                        │
│  - 本地嵌入模型：all-MiniLM-L6-v2 (自动下载)                       │
│  - 支持 Markdown Frontmatter 解析                                  │
│  - 精细编辑操作                                                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼ MCP
┌─────────────────────────────────────────────────────────────────┐
│                           Hermes 智能体                            │
│                                                                   │
│  配置 ~/.hermes/config.yaml：                                     │
│  - 添加 mcp_servers 配置                                          │
│  - 指定 VAULT_PATH                                                │
│                                                                   │
│  智能体自主调用 MCP 工具：                                          │
│  - 搜索、读取、创建、更新、删除文档                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 数据流向

1. **文档上传**：
   - 用户 → AgentNow 前端 → AgentNow 后端 → 文件系统 (`~/.agentnow/knowledge/docs/`)
   - 同时写入数据库元数据

2. **文档检索**：
   - Hermes 智能体 → MCP 协议 → mcp-markdown-vault → 文件系统
   - 或：AgentNow 前端 → AgentNow 后端 → 数据库

3. **语义搜索**：
   - Hermes 智能体 → MCP 协议 → mcp-markdown-vault → 本地嵌入模型 → 混合检索

### 9.3 设计原则

| 原则 | 说明 |
|------|------|
| **复用成熟组件** | 使用现成的 `@wirux/mcp-markdown-vault`，不重复造轮子 |
| **文件系统共享** | AgentNow 和 mcp-markdown-vault 共享同一个目录，无需同步 |
| **权限分层** | AgentNow 负责用户认证和权限控制，MCP Server 只处理文件操作 |
| **数据开放** | 所有文档都是纯 Markdown 文件，可随时导入 Obsidian |
| **零配置语义搜索** | mcp-markdown-vault 内置语义搜索，自动下载本地嵌入模型 |

---

## 十、附录

### 10.1 常用命令速查

```bash
# 创建知识库目录
mkdir -p ~/.agentnow/knowledge/docs
chmod -R 755 ~/.agentnow/knowledge/

# 启动后端服务（开发模式）
cd AgentNow/backend
uv run uvicorn app.main:app --reload --port 5116

# 测试 mcp-markdown-vault
VAULT_PATH=~/.agentnow/knowledge/docs npx @wirux/mcp-markdown-vault

# 启动 Hermes
hermes

# 检查 Hermes 配置
cat ~/.hermes/config.yaml | grep -A 10 "mcp_servers"
```

### 10.2 API 文档访问

| 文档类型 | 地址 |
|----------|------|
| Swagger UI | `http://localhost:5116/docs` |
| ReDoc | `http://localhost:5116/redoc` |
| OpenAPI JSON | `http://localhost:5116/openapi.json` |

### 10.3 相关文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 设计文档 | `AgentNow/md/KNOWLEDGE_BASE_DESIGN.md` | 详细设计说明 |
| 配置手册 | `AgentNow/md/KNOWLEDGE_CONFIG_GUIDE.md` | 本文档 |
| 数据库脚本 | `AgentNow/backend/data/database.sql` | 数据库初始化 |
| Hermes 配置 | `~/.hermes/config.yaml` | MCP 服务器配置 |
| 知识库目录 | `~/.agentnow/knowledge/docs/` | 文档存储目录 |

---

**文档结束。**
