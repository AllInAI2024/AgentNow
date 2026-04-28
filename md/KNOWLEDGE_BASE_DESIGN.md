# 知识库管理功能设计文档

> 版本：v1.0\
> 日期：2026-04-28\
> 状态：基础CRUD版本（不含混合检索）

***

## 一、背景与目标

### 1.1 Hermes 知识库现状分析

根据对 Hermes 官方文档和代码的调研，Hermes 的知识库功能现状如下：

| 功能                    | 状态              | 说明                           |
| --------------------- | --------------- | ---------------------------- |
| Knowledgebase 配置      | Feature Request | Issue #844，开发中               |
| semantic-memory skill | PR #4056        | 可选安装，实现混合检索                  |
| workspace 目录          | 已有              | `~/.hermes/workspace/` 持久化存储 |
| document\_cache       | 已有              | 临时缓存，24小时自动清理                |
| 知识库管理 API             | 暂不支持            | 目前只有 CLI 或文件系统操作             |

### 1.2 混合检索实现方式（当前暂不实现）

Hermes 的 `semantic-memory` skill 采用以下技术栈：

- **嵌入模型**：fastembed（BAAI/bge-small-en-v1.5，384维，本地免费）
- **存储**：SQLite + 向量扩展
- **检索算法**：BM25关键词搜索 + 向量相似度搜索 + 时间衰减排名

### 1.3 本阶段目标

**基础CRUD版本**：

- 实现文档的增删改查功能
- 与 Hermes workspace 目录同步
- 存储文档原文与 Hermes embedding 的对应关系
- 不实现混合检索（后续版本扩展）

***

## 二、设计原则

### 2.1 核心原则

1. **Hermes 不改造原则**：完全通过文件系统操作与 Hermes 集成，不修改 Hermes 代码
2. **共享知识库**：所有企业用户共享同一知识库，不区分部门/人员
3. **双向映射**：AgentNow 存储文档元数据，Hermes workspace 存储实际文档
4. **可扩展性**：预留混合检索接口，后续可平滑扩展

### 2.2 架构设计

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AgentNow Web 层                                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐  │
│  │  前端管理界面  │  │  知识库API    │  │  知识库服务            │  │
│  │  (Vue3)       │  │  (FastAPI)    │  │  (文件同步/元数据管理) │  │
│  └───────┬───────┘  └───────┬───────┘  └───────────┬───────────┘  │
└──────────┼──────────────────┼────────────────────────┼────────────────┘
           │                  │                        │
           ▼                  ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         数据存储层                                     │
│  ┌───────────────────┐  ┌─────────────────────────────────────────┐ │
│  │  MySQL (元数据)   │  │  文件系统 (实际文档)                     │ │
│  │  - knowledge_docs │  │  - AgentNow 存储目录 (备份/原文)        │ │
│  │  - knowledge_chunks│ │  - Hermes workspace 目录 (同步)         │ │
│  └───────────────────┘  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Hermes 层（原生）                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  ~/.hermes/workspace/  (所有 Profile 共享)                       ││
│  │  ├── docs/          # 文档目录                                    ││
│  │  └── workspace.db   # semantic-memory 数据库（可选）             ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

***

## 三、数据库设计

### 3.1 数据表结构

#### 3.1.1 知识库文档表 (knowledge\_docs)

存储文档的基本元数据信息。

```sql
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    title VARCHAR(500) NOT NULL COMMENT '文档标题',
    file_name VARCHAR(500) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(1000) COMMENT 'AgentNow 存储路径（相对路径）',
    hermes_path VARCHAR(1000) COMMENT 'Hermes workspace 中的路径（相对路径）',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
    file_type VARCHAR(50) COMMENT '文件类型/扩展名',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    content_hash VARCHAR(64) COMMENT '文件内容哈希值（SHA256），用于去重和变更检测',
    
    status TINYINT DEFAULT 1 COMMENT '状态：1-已上传，2-已同步到Hermes，3-处理中，4-失败',
    sync_status TINYINT DEFAULT 0 COMMENT '同步状态：0-未同步，1-已同步，2-同步失败',
    sync_error TEXT COMMENT '同步失败错误信息',
    synced_at DATETIME COMMENT '同步到Hermes的时间',
    
    description TEXT COMMENT '文档描述/摘要',
    tags JSON COMMENT '标签列表，JSON数组格式',
    category VARCHAR(100) COMMENT '文档分类',
    
    created_by BIGINT COMMENT '上传者用户ID',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开（默认所有用户可见）',
    
    embedding_id VARCHAR(255) COMMENT 'Hermes embedding 对应的ID（如有）',
    embedding_info JSON COMMENT 'Hermes embedding 相关信息（JSON格式）',
    
    deleted_at DATETIME COMMENT '删除时间（软删除）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_title (title),
    INDEX idx_file_name (file_name),
    INDEX idx_status (status),
    INDEX idx_sync_status (sync_status),
    INDEX idx_category (category),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档表';
```

#### 3.1.2 文档分块表 (knowledge\_doc\_chunks)

存储文档的分块信息，用于记录与 Hermes embedding 的对应关系。
（基础版本可简化，后续实现检索时完善）

```sql
CREATE TABLE IF NOT EXISTS knowledge_doc_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分块ID',
    doc_id BIGINT NOT NULL COMMENT '所属文档ID',
    
    chunk_index INT COMMENT '分块序号',
    chunk_content TEXT COMMENT '分块原文内容',
    chunk_hash VARCHAR(64) COMMENT '分块内容哈希',
    
    start_position BIGINT COMMENT '在原文件中的起始位置',
    end_position BIGINT COMMENT '在原文件中的结束位置',
    char_count INT COMMENT '字符数',
    token_count INT COMMENT '预估token数',
    
    hermes_embedding_id VARCHAR(255) COMMENT 'Hermes embedding ID',
    embedding_info JSON COMMENT 'Embedding 相关元信息',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_chunk_index (chunk_index),
    INDEX idx_hermes_embedding_id (hermes_embedding_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档分块表';
```

#### 3.1.3 知识库配置表 (knowledge\_configs)

存储知识库的全局配置信息。

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

-- 初始化默认配置
INSERT INTO knowledge_configs (config_key, config_value, description) VALUES
('storage.base_path', './data/knowledge_docs', 'AgentNow 知识库文档存储根目录'),
('hermes.workspace_path', '~/.hermes/workspace/docs', 'Hermes workspace 文档目录'),
('sync.auto_sync', 'true', '是否自动同步到Hermes'),
('file.max_size', '104857600', '单文件最大大小（字节，默认100MB）'),
('file.allowed_types', '.pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml', '允许上传的文件类型'),
('embedding.enabled', 'false', '是否启用embedding（基础版本为false）');
```

### 3.2 ER 图

```
┌─────────────────────┐       ┌─────────────────────────┐
│   knowledge_docs    │       │  knowledge_doc_chunks   │
├─────────────────────┤       ├─────────────────────────┤
│ id (PK)             │◄──────│ doc_id (FK)             │
│ title               │       │ chunk_index             │
│ file_name           │       │ chunk_content           │
│ file_path           │       │ start_position          │
│ hermes_path         │       │ hermes_embedding_id     │
│ status              │       └─────────────────────────┘
│ sync_status         │
│ created_by          │
│ embedding_id        │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  knowledge_configs  │
├─────────────────────┤
│ config_key (UK)     │
│ config_value        │
└─────────────────────┘
```

***

## 四、后端设计

### 4.1 目录结构

```
backend/app/
├── models/
│   ├── __init__.py
│   ├── knowledge_doc.py        # 文档模型
│   ├── knowledge_doc_chunk.py  # 分块模型
│   ├── knowledge_config.py     # 配置模型
│   └── ... (其他已有模型)
├── schemas/
│   ├── __init__.py
│   ├── knowledge.py            # 知识库相关 Pydantic 模型
│   └── ... (其他已有 schema)
├── routers/
│   ├── __init__.py
│   ├── knowledge.py            # 知识库 API 路由
│   └── ... (其他已有路由)
├── services/
│   ├── __init__.py
│   ├── knowledge_service.py    # 知识库业务逻辑
│   ├── hermes_sync_service.py  # Hermes 同步服务
│   └── ... (其他已有服务)
├── utils/
│   ├── __init__.py
│   └── file_handler.py         # 文件处理工具
└── main.py                     # 入口文件（需更新）
```

### 4.2 核心模块设计

#### 4.2.1 模型层 (Models)

**KnowledgeDoc 模型**：

- 映射 `knowledge_docs` 表
- 包含软删除字段 `deleted_at`
- 与 `KnowledgeDocChunk` 一对多关系

**KnowledgeDocChunk 模型**：

- 映射 `knowledge_doc_chunks` 表
- 存储分块原文，便于后续查看
- 记录 Hermes embedding 对应关系

#### 4.2.2 服务层 (Services)

**KnowledgeService**：

- 文档上传、下载、删除、列表查询
- 文档元数据管理（标签、分类、描述）
- 文件存储管理

**HermesSyncService**：

- 与 Hermes workspace 目录同步
- 文件复制/移动操作
- 同步状态追踪
- 冲突处理

#### 4.2.3 路由层 (Routers)

| 接口                                     | 方法     | 描述          | 权限      |
| -------------------------------------- | ------ | ----------- | ------- |
| `/api/v1/knowledge/docs`               | GET    | 获取文档列表（分页）  | 登录用户    |
| `/api/v1/knowledge/docs/{id}`          | GET    | 获取文档详情      | 登录用户    |
| `/api/v1/knowledge/docs`               | POST   | 上传文档        | 登录用户    |
| `/api/v1/knowledge/docs/{id}`          | PUT    | 更新文档信息      | 上传者/管理员 |
| `/api/v1/knowledge/docs/{id}`          | DELETE | 删除文档（软删除）   | 上传者/管理员 |
| `/api/v1/knowledge/docs/{id}/download` | GET    | 下载文档        | 登录用户    |
| `/api/v1/knowledge/docs/{id}/sync`     | POST   | 手动同步到Hermes | 管理员     |
| `/api/v1/knowledge/configs`            | GET    | 获取知识库配置     | 管理员     |
| `/api/v1/knowledge/configs`            | PUT    | 更新知识库配置     | 管理员     |

#### 4.2.4 Schema 定义

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class KnowledgeDocBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="文档标题")
    description: Optional[str] = Field(None, description="文档描述")
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    category: Optional[str] = Field(None, description="分类")
    is_public: bool = Field(True, description="是否公开")

class KnowledgeDocCreate(KnowledgeDocBase):
    pass

class KnowledgeDocUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    is_public: Optional[bool] = None

class KnowledgeDocResponse(KnowledgeDocBase):
    id: int
    file_name: str
    file_size: int
    file_type: Optional[str]
    mime_type: Optional[str]
    status: int
    sync_status: int
    synced_at: Optional[datetime]
    created_by: int
    embedding_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class KnowledgeDocListResponse(BaseModel):
    items: List[KnowledgeDocResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class SyncStatusResponse(BaseModel):
    doc_id: int
    sync_status: int
    synced_at: Optional[datetime]
    message: str
```

### 4.3 文件同步流程

#### 4.3.1 上传流程

```
1. 用户上传文件
        │
        ▼
2. 后端接收文件，验证类型/大小
        │
        ▼
3. 生成唯一文件名，保存到 AgentNow 存储目录
        │
        ▼
4. 计算文件哈希，检查是否重复
        │
        ├── 重复？ ──→ 返回错误或提示
        │
        ▼ 否
5. 插入数据库记录 (knowledge_docs)
        │
        ▼
6. 检查自动同步配置
        │
        ├── 启用自动同步？
        │       │
        │       ▼ 是
        │  ┌────────────────────┐
        │  │ 7. 同步到 Hermes   │
        │  │    workspace 目录  │
        │  └─────────┬──────────┘
        │            │
        └────────────┼─────────┐
                     ▼         ▼
              同步成功      同步失败
                     │         │
                     ▼         ▼
          更新 sync_status  记录错误信息
          = 1, synced_at
```

#### 4.3.2 删除流程

```
1. 用户请求删除文档
        │
        ▼
2. 检查权限（上传者或管理员）
        │
        ▼
3. 软删除数据库记录 (deleted_at = NOW())
        │
        ▼
4. 异步任务：
   ├── 从 Hermes workspace 删除文件
   ├── 从 AgentNow 存储目录删除文件（可选，保留备份）
   └── 更新 sync_status
```

***

## 五、前端设计

### 5.1 页面结构

```
知识库管理页面
├── 顶部工具栏
│   ├── 搜索框（按标题/标签搜索）
│   ├── 分类筛选下拉框
│   ├── 状态筛选下拉框
│   └── 上传文档按钮
├── 文档列表
│   ├── 列表视图（默认）
│   │   ├── 复选框（批量操作）
│   │   ├── 文档图标（根据类型）
│   │   ├── 标题/文件名
│   │   ├── 大小/类型
│   │   ├── 同步状态（图标+文字）
│   │   ├── 上传时间
│   │   └── 操作按钮（查看详情/下载/编辑/删除/同步）
│   └── 网格视图（可选）
└── 分页组件
```

### 5.2 组件设计

#### 5.2.1 主要组件

| 组件名                   | 路径                                     | 描述      |
| --------------------- | -------------------------------------- | ------- |
| KnowledgeDocumentList | `views/knowledge/DocumentList.vue`     | 文档列表主页面 |
| KnowledgeUploadModal  | `components/knowledge/UploadModal.vue` | 上传弹窗    |
| KnowledgeEditModal    | `components/knowledge/EditModal.vue`   | 编辑弹窗    |
| KnowledgeDetailModal  | `components/knowledge/DetailModal.vue` | 详情弹窗    |
| FileIcon              | `components/common/FileIcon.vue`       | 文件类型图标  |

#### 5.2.2 API 模块

```typescript
// frontend/src/api/knowledge.ts

import request from './http'

export interface KnowledgeDoc {
  id: number
  title: string
  file_name: string
  file_size: number
  file_type: string
  status: number
  sync_status: number
  synced_at: string | null
  created_by: number
  tags: string[]
  category: string | null
  is_public: boolean
  created_at: string
  updated_at: string
}

export interface KnowledgeDocList {
  items: KnowledgeDoc[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const knowledgeApi = {
  getList: (params: {
    page?: number
    page_size?: number
    keyword?: string
    category?: string
    status?: number
  }) => request.get<KnowledgeDocList>('/knowledge/docs', { params }),

  getDetail: (id: number) => request.get<KnowledgeDoc>(`/knowledge/docs/${id}`),

  upload: (formData: FormData, onUploadProgress?: (progress: number) => void) => 
    request.post<KnowledgeDoc>('/knowledge/docs', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          onUploadProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total))
        }
      }
    }),

  update: (id: number, data: Partial<KnowledgeDoc>) => 
    request.put<KnowledgeDoc>(`/knowledge/docs/${id}`, data),

  delete: (id: number) => request.delete(`/knowledge/docs/${id}`),

  download: (id: number) => 
    request.get(`/knowledge/docs/${id}/download`, { responseType: 'blob' }),

  sync: (id: number) => request.post(`/knowledge/docs/${id}/sync`),
}
```

### 5.3 路由配置

```typescript
// 在 router/index.ts 中添加

{
  path: '/knowledge/document',
  name: 'KnowledgeDocument',
  component: () => import('@/views/knowledge/DocumentList.vue'),
  meta: { title: '文档列表', requiresAuth: true },
},
{
  path: '/knowledge/setting',
  name: 'KnowledgeSetting',
  component: () => import('@/views/knowledge/Setting.vue'),
  meta: { title: '知识库设置', requiresAuth: true },
},
```

***

## 六、与 Hermes 的集成方式

### 6.1 当前实现方式（文件系统同步）

由于 Hermes 暂未提供知识库管理的 HTTP API，采用以下方式：

1. **共享目录**：AgentNow 和 Hermes 共享 `~/.hermes/workspace/docs/` 目录
2. **文件同步**：AgentNow 上传文件后，同步复制到 Hermes workspace 目录
3. **Hermes 自动处理**：Hermes 的 semantic-memory skill（如果启用）会自动监控目录并生成 embedding

### 6.2 同步策略

| 场景        | 策略                      |
| --------- | ----------------------- |
| 新增文档      | 立即同步到 Hermes workspace  |
| 更新文档      | 删除旧文件，同步新文件             |
| 删除文档      | 从 Hermes workspace 删除   |
| Hermes 重启 | Hermes 自动重新扫描 workspace |

### 6.3 配置要求

在 Hermes 的 `config.yaml` 中需要配置：

```yaml
knowledgebase:
  enabled: true
  directories:
    - ~/.hermes/workspace/docs
  auto_retrieve: true
```

如果使用 semantic-memory skill，还需要：

```bash
# 安装 skill
hermes skill install semantic-memory

# 或手动安装依赖
pip install fastembed
```

***

## 七、权限设计

### 7.1 权限码设计

在 `permissions` 表中添加以下权限：

| 权限名称 | 权限码                    | 类型 | 路径                                       | 说明          |
| ---- | ---------------------- | -- | ---------------------------------------- | ----------- |
| 文档查询 | knowledge:doc:query    | 3  | GET /api/v1/knowledge/docs               | 查看文档列表      |
| 文档详情 | knowledge:doc:detail   | 3  | GET /api/v1/knowledge/docs/{id}          | 查看文档详情      |
| 文档上传 | knowledge:doc:create   | 3  | POST /api/v1/knowledge/docs              | 上传文档        |
| 文档编辑 | knowledge:doc:update   | 3  | PUT /api/v1/knowledge/docs/{id}          | 编辑文档信息      |
| 文档删除 | knowledge:doc:delete   | 3  | DELETE /api/v1/knowledge/docs/{id}       | 删除文档        |
| 文档下载 | knowledge:doc:download | 3  | GET /api/v1/knowledge/docs/{id}/download | 下载文档        |
| 文档同步 | knowledge:doc:sync     | 3  | POST /api/v1/knowledge/docs/{id}/sync    | 手动同步到Hermes |
| 配置查看 | knowledge:config:view  | 3  | GET /api/v1/knowledge/configs            | 查看知识库配置     |
| 配置编辑 | knowledge:config:edit  | 3  | PUT /api/v1/knowledge/configs            | 编辑知识库配置     |

### 7.2 角色权限分配

| 角色    | 权限                                                                                      |
| ----- | --------------------------------------------------------------------------------------- |
| 超级管理员 | 所有权限                                                                                    |
| 系统管理员 | knowledge:doc:*, knowledge:config:*                                                     |
| 普通用户  | knowledge:doc:query, knowledge:doc:detail, knowledge:doc:create, knowledge:doc:download |

### 7.3 数据权限

- **文档创建者**：可以编辑、删除自己上传的文档
- **管理员**：可以编辑、删除所有文档
- **公共文档**：所有用户都可以查看、下载（`is_public = true`）

***

## 八、数据库升级脚本

### 8.1 升级 SQL

```sql
-- ============================================
-- 知识库功能升级脚本
-- 版本: v7.0
-- 日期: 2026-04-28
-- ============================================

USE agentnow;

-- 1. 创建知识库配置表
CREATE TABLE IF NOT EXISTS knowledge_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '配置描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库配置表';

-- 2. 初始化默认配置
INSERT INTO knowledge_configs (config_key, config_value, description) VALUES
('storage.base_path', './data/knowledge_docs', 'AgentNow 知识库文档存储根目录'),
('hermes.workspace_path', '~/.hermes/workspace/docs', 'Hermes workspace 文档目录'),
('sync.auto_sync', 'true', '是否自动同步到Hermes'),
('file.max_size', '104857600', '单文件最大大小（字节，默认100MB）'),
('file.allowed_types', '.pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml', '允许上传的文件类型'),
('embedding.enabled', 'false', '是否启用embedding（基础版本为false）');

-- 3. 创建知识库文档表
CREATE TABLE IF NOT EXISTS knowledge_docs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    title VARCHAR(500) NOT NULL COMMENT '文档标题',
    file_name VARCHAR(500) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(1000) COMMENT 'AgentNow 存储路径（相对路径）',
    hermes_path VARCHAR(1000) COMMENT 'Hermes workspace 中的路径（相对路径）',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
    file_type VARCHAR(50) COMMENT '文件类型/扩展名',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    content_hash VARCHAR(64) COMMENT '文件内容哈希值（SHA256）',
    status TINYINT DEFAULT 1 COMMENT '状态：1-已上传，2-已同步到Hermes，3-处理中，4-失败',
    sync_status TINYINT DEFAULT 0 COMMENT '同步状态：0-未同步，1-已同步，2-同步失败',
    sync_error TEXT COMMENT '同步失败错误信息',
    synced_at DATETIME COMMENT '同步到Hermes的时间',
    description TEXT COMMENT '文档描述/摘要',
    tags JSON COMMENT '标签列表',
    category VARCHAR(100) COMMENT '文档分类',
    created_by BIGINT COMMENT '上传者用户ID',
    is_public BOOLEAN DEFAULT TRUE COMMENT '是否公开',
    embedding_id VARCHAR(255) COMMENT 'Hermes embedding ID',
    embedding_info JSON COMMENT 'Hermes embedding 相关信息',
    deleted_at DATETIME COMMENT '删除时间（软删除）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_title (title),
    INDEX idx_file_name (file_name),
    INDEX idx_status (status),
    INDEX idx_sync_status (sync_status),
    INDEX idx_category (category),
    INDEX idx_created_by (created_by),
    INDEX idx_created_at (created_at),
    INDEX idx_deleted_at (deleted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库文档表';

-- 4. 创建文档分块表
CREATE TABLE IF NOT EXISTS knowledge_doc_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '分块ID',
    doc_id BIGINT NOT NULL COMMENT '所属文档ID',
    chunk_index INT COMMENT '分块序号',
    chunk_content TEXT COMMENT '分块原文内容',
    chunk_hash VARCHAR(64) COMMENT '分块内容哈希',
    start_position BIGINT COMMENT '起始位置',
    end_position BIGINT COMMENT '结束位置',
    char_count INT COMMENT '字符数',
    token_count INT COMMENT '预估token数',
    hermes_embedding_id VARCHAR(255) COMMENT 'Hermes embedding ID',
    embedding_info JSON COMMENT 'Embedding 元信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id) ON DELETE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_chunk_index (chunk_index),
    INDEX idx_hermes_embedding_id (hermes_embedding_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档分块表';

-- 5. 添加知识库相关权限
-- 获取知识库管理菜单ID
SET @knowledge_parent_id = (SELECT id FROM permissions WHERE code = 'knowledge');

-- 添加文档管理相关权限（按钮级）
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@knowledge_parent_id, '文档查询', 'knowledge:doc:query', 3, '/api/v1/knowledge/docs'),
(@knowledge_parent_id, '文档详情', 'knowledge:doc:detail', 3, '/api/v1/knowledge/docs/:id'),
(@knowledge_parent_id, '文档上传', 'knowledge:doc:create', 3, '/api/v1/knowledge/docs'),
(@knowledge_parent_id, '文档编辑', 'knowledge:doc:update', 3, '/api/v1/knowledge/docs/:id'),
(@knowledge_parent_id, '文档删除', 'knowledge:doc:delete', 3, '/api/v1/knowledge/docs/:id'),
(@knowledge_parent_id, '文档下载', 'knowledge:doc:download', 3, '/api/v1/knowledge/docs/:id/download'),
(@knowledge_parent_id, '文档同步', 'knowledge:doc:sync', 3, '/api/v1/knowledge/docs/:id/sync'),
(@knowledge_parent_id, '配置查看', 'knowledge:config:view', 3, '/api/v1/knowledge/configs'),
(@knowledge_parent_id, '配置编辑', 'knowledge:config:edit', 3, '/api/v1/knowledge/configs');

-- 6. 为超级管理员分配新权限
SET @super_admin_role_id = (SELECT id FROM roles WHERE code = 'super_admin');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @super_admin_role_id, id FROM permissions WHERE code LIKE 'knowledge:%';

-- 7. 为系统管理员分配权限
SET @system_admin_role_id = (SELECT id FROM roles WHERE code = 'system_admin');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @system_admin_role_id, id FROM permissions 
WHERE code IN (
    'knowledge:doc:query', 'knowledge:doc:detail', 'knowledge:doc:create',
    'knowledge:doc:update', 'knowledge:doc:delete', 'knowledge:doc:download',
    'knowledge:doc:sync', 'knowledge:config:view', 'knowledge:config:edit'
);

-- 8. 为普通用户分配权限
SET @user_role_id = (SELECT id FROM roles WHERE code = 'user');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @user_role_id, id FROM permissions 
WHERE code IN (
    'knowledge:doc:query', 'knowledge:doc:detail', 
    'knowledge:doc:create', 'knowledge:doc:download'
);
```

### 8.2 升级步骤

1. 备份现有数据库
2. 执行上述升级脚本
3. 重启后端服务
4. 验证新功能

***

## 九、后续扩展规划

### 9.1 版本规划

| 版本        | 功能     | 说明                                  |
| --------- | ------ | ----------------------------------- |
| v1.0 (当前) | 基础CRUD | 文档上传/下载/删除/列表，与Hermes同步             |
| v1.1      | 混合检索   | 集成Hermes semantic-memory，实现向量+关键词搜索 |
| v1.2      | 文档预览   | PDF、文本文件在线预览                        |
| v1.3      | 批量操作   | 批量上传、批量删除、批量同步                      |
| v1.4      | 权限细化   | 部门级权限、文档分享功能                        |

### 9.2 混合检索集成方案

后续实现混合检索时，需要：

1. **安装依赖**：
   ```bash
   pip install fastembed
   # 或安装 Hermes semantic-memory skill
   hermes skill install semantic-memory
   ```
2. **配置 Hermes**：
   ```yaml
   knowledgebase:
     enabled: true
     directories:
       - ~/.hermes/workspace/docs
     auto_retrieve: true
   ```
3. **扩展 AgentNow**：
   - 添加搜索 API 接口
   - 前端添加搜索结果展示
   - 可能需要独立的向量数据库（如 ChromaDB）

***

## 十、注意事项

### 10.1 已知限制

1. **Hermes API 限制**：目前没有公开的知识库管理 HTTP API，只能通过文件系统操作
2. **同步延迟**：文件同步到 Hermes workspace 后，Hermes 的 embedding 生成可能需要时间
3. **文件类型限制**：Hermes 对某些文件类型（如复杂的 Excel、PPT）的处理能力有限

### 10.2 生产环境建议

1. **文件存储**：考虑使用对象存储（如 OSS、S3）替代本地文件系统
2. **异步同步**：使用 Celery 或其他任务队列处理文件同步
3. **文件去重**：基于 content\_hash 实现文件级去重
4. **监控告警**：监控同步状态，失败时及时告警

### 10.3 安全考虑

1. **文件类型验证**：严格验证上传文件类型，防止恶意文件
2. **文件大小限制**：设置合理的文件大小上限
3. **访问控制**：确保非公开文档只有授权用户可访问
4. **病毒扫描**：生产环境建议集成病毒扫描服务

***

> 本文档为知识库管理功能的基础版本设计方案，聚焦于实现文档的增删改查和与 Hermes 的文件同步。混合检索功能将在后续版本中实现。

