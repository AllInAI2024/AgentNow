-- 智现 AgentNow 智能体平台数据库初始化脚本
-- 数据库: agentnow
-- 版本: v8.0 (知识库管理 v2.0 - 集成 mcp-markdown-vault)
-- 日期: 2026-04-28

-- 创建数据库
CREATE DATABASE IF NOT EXISTS agentnow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE agentnow;

-- ============================================
-- 一、部门表
-- ============================================
CREATE TABLE IF NOT EXISTS departments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '部门ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父部门ID（0表示顶级部门）',
    name VARCHAR(100) NOT NULL COMMENT '部门名称',
    code VARCHAR(50) COMMENT '部门编码',
    description VARCHAR(500) COMMENT '部门描述',
    sort INT DEFAULT 0 COMMENT '排序号',
    status TINYINT DEFAULT 1 COMMENT '状态：1-启用，0-禁用',
    leader_id BIGINT COMMENT '部门负责人ID（关联用户表）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_parent_id (parent_id),
    INDEX idx_code (code),
    INDEX idx_sort (sort)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- ============================================
-- 二、用户表（员工表）
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    department_id BIGINT COMMENT '所属部门ID',
    login_name VARCHAR(50) NOT NULL COMMENT '登录账号（唯一，用于登录）',
    phone VARCHAR(20) COMMENT '手机号（可选，可用于登录）',
    email VARCHAR(100) COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    username VARCHAR(50) NOT NULL COMMENT '用户姓名/昵称',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    hermes_profile VARCHAR(100) COMMENT '对应的 Hermes Profile 名称',
    hermes_profile_config TEXT COMMENT 'Hermes Profile 配置(JSON)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_default_password BOOLEAN DEFAULT TRUE COMMENT '是否为默认密码（首次登录需修改）',
    is_super_admin BOOLEAN DEFAULT FALSE COMMENT '是否为超级管理员（全局权限）',
    last_login_at DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(50) COMMENT '最后登录IP',
    password_changed_at DATETIME COMMENT '密码修改时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_login_name (login_name),
    UNIQUE KEY uk_phone (phone),
    UNIQUE KEY uk_email (email),
    INDEX idx_department_id (department_id),
    INDEX idx_hermes_profile (hermes_profile),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 三、角色表
-- ============================================
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    name VARCHAR(50) NOT NULL COMMENT '角色名称',
    code VARCHAR(50) NOT NULL COMMENT '角色编码（英文标识）',
    description TEXT COMMENT '角色描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- ============================================
-- 四、权限表
-- ============================================
CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父权限ID（0表示顶级）',
    name VARCHAR(50) NOT NULL COMMENT '权限名称',
    code VARCHAR(100) NOT NULL COMMENT '权限编码（英文标识，如user:list, user:create）',
    type TINYINT DEFAULT 1 COMMENT '类型：1-菜单，2-按钮，3-API接口',
    path VARCHAR(255) COMMENT '路由路径/接口路径',
    icon VARCHAR(100) COMMENT '菜单图标',
    sort INT DEFAULT 0 COMMENT '排序号',
    divider TINYINT DEFAULT 0 COMMENT '是否是菜单分割线：0-否，1-是',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_parent_id (parent_id),
    INDEX idx_code (code),
    INDEX idx_type (type),
    INDEX idx_sort (sort)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- ============================================
-- 五、角色-权限关联表
-- ============================================
CREATE TABLE IF NOT EXISTS role_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色-权限关联表';

-- ============================================
-- 六、用户-角色关联表
-- ============================================
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户-角色关联表';

-- ============================================
-- 七、知识库配置表
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_configs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '配置描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库配置表';

-- ============================================
-- 八、知识库文档表
-- ============================================
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

-- ============================================
-- 九、初始化数据
-- ============================================

-- 插入系统内置角色
INSERT INTO roles (name, code, description)
VALUES 
('超级管理员', 'super_admin', '系统超级管理员，拥有所有权限'),
('系统管理员', 'system_admin', '系统管理员，拥有系统管理权限'),
('普通用户', 'user', '普通用户，拥有基本操作权限');

-- 插入系统权限/功能点（菜单结构）
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(0, '工作台', 'dashboard', 1, '/dashboard', 'dashboard', 1),
(0, '智能体管理', 'agent', 1, '/agent', 'robot', 2),
(0, '知识库管理', 'knowledge', 1, '/knowledge', 'folder-open', 3),
(0, '系统管理', 'system', 1, '/system', 'team', 4);

-- 获取父权限ID
SET @dashboard_id = (SELECT id FROM permissions WHERE code = 'dashboard');
SET @agent_id = (SELECT id FROM permissions WHERE code = 'agent');
SET @knowledge_id = (SELECT id FROM permissions WHERE code = 'knowledge');
SET @system_id = (SELECT id FROM permissions WHERE code = 'system');

-- 二级菜单 - 智能体管理
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@agent_id, '智能体列表', 'agent:list', 1, '/agent/list', 'list', 1),
(@agent_id, '智能体配置', 'agent:config', 1, '/agent/config', 'appstore', 2),
(@agent_id, '对话管理', 'agent:conversation', 1, '/agent/conversation', 'message', 3);

-- 二级菜单 - 知识库管理
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@knowledge_id, '文档列表', 'knowledge:document', 1, '/knowledge/document', 'file', 1),
(@knowledge_id, '知识库设置', 'knowledge:setting', 1, '/knowledge/setting', 'setting', 2);

-- 二级菜单 - 系统管理
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@system_id, '部门管理', 'department', 1, '/organization/department', 'apartment', 1),
(@system_id, '员工管理', 'employee', 1, '/organization/employee', 'user', 2);

-- 分割线（组织管理和角色权限之间）
INSERT INTO permissions (parent_id, name, code, type, sort, divider)
VALUES 
(@system_id, '---', 'divider:1', 1, 3, 1);

-- 角色权限部分
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@system_id, '角色管理', 'role:manage', 1, '/role/manage', 'safety-certificate', 4),
(@system_id, '功能点管理', 'permission:manage', 1, '/permission/manage', 'key', 5);

-- 分割线（角色权限和系统设置之间）
INSERT INTO permissions (parent_id, name, code, type, sort, divider)
VALUES 
(@system_id, '---', 'divider:2', 1, 6, 1);

-- 系统设置部分
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@system_id, '系统设置', 'system:setting', 1, '/system/setting', 'tool', 7),
(@system_id, '系统监控', 'system:monitor', 1, '/system/monitor', 'monitor', 8);

-- 插入按钮/接口级权限
-- 获取一些二级菜单的ID
SET @department_id = (SELECT id FROM permissions WHERE code = 'department');
SET @employee_id = (SELECT id FROM permissions WHERE code = 'employee');
SET @role_manage_id = (SELECT id FROM permissions WHERE code = 'role:manage');

-- 部门管理相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@department_id, '部门查询', 'department:query', 3, '/api/v1/departments'),
(@department_id, '部门创建', 'department:create', 3, '/api/v1/departments'),
(@department_id, '部门编辑', 'department:update', 3, '/api/v1/departments/:id'),
(@department_id, '部门删除', 'department:delete', 3, '/api/v1/departments/:id');

-- 员工管理相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@employee_id, '员工查询', 'employee:query', 3, '/api/v1/employees'),
(@employee_id, '员工创建', 'employee:create', 3, '/api/v1/employees'),
(@employee_id, '员工编辑', 'employee:update', 3, '/api/v1/employees/:id'),
(@employee_id, '员工删除', 'employee:delete', 3, '/api/v1/employees/:id'),
(@employee_id, '员工重置密码', 'employee:reset_password', 3, '/api/v1/employees/:id/reset-password'),
(@employee_id, '员工启用/禁用', 'employee:toggle_status', 3, '/api/v1/employees/:id/status');

-- 角色管理相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@role_manage_id, '角色查询', 'role:query', 3, '/api/v1/roles'),
(@role_manage_id, '角色创建', 'role:create', 3, '/api/v1/roles'),
(@role_manage_id, '角色编辑', 'role:update', 3, '/api/v1/roles/:id'),
(@role_manage_id, '角色删除', 'role:delete', 3, '/api/v1/roles/:id'),
(@role_manage_id, '角色权限配置', 'role:assign_permission', 3, '/api/v1/roles/:id/permissions');

-- 获取知识库文档列表菜单ID
SET @knowledge_doc_id = (SELECT id FROM permissions WHERE code = 'knowledge:document');
SET @knowledge_setting_id = (SELECT id FROM permissions WHERE code = 'knowledge:setting');

-- 知识库文档管理相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@knowledge_doc_id, '文档查询', 'knowledge:doc:query', 3, '/api/v1/knowledge/docs'),
(@knowledge_doc_id, '文档详情', 'knowledge:doc:detail', 3, '/api/v1/knowledge/docs/:id'),
(@knowledge_doc_id, '文档上传', 'knowledge:doc:create', 3, '/api/v1/knowledge/docs'),
(@knowledge_doc_id, '文档编辑', 'knowledge:doc:update', 3, '/api/v1/knowledge/docs/:id'),
(@knowledge_doc_id, '文档删除', 'knowledge:doc:delete', 3, '/api/v1/knowledge/docs/:id'),
(@knowledge_doc_id, '文档下载', 'knowledge:doc:download', 3, '/api/v1/knowledge/docs/:id/download');

-- 知识库设置相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@knowledge_setting_id, '配置查看', 'knowledge:config:view', 3, '/api/v1/knowledge/configs'),
(@knowledge_setting_id, '配置编辑', 'knowledge:config:edit', 3, '/api/v1/knowledge/configs');

-- 初始化知识库配置
INSERT INTO knowledge_configs (config_key, config_value, description) VALUES
('storage.base_path', '~/.agentnow/knowledge/docs', '知识库文档存储根目录'),
('file.max_size', '104857600', '单文件最大大小（字节，默认100MB）'),
('file.allowed_types', '.pdf,.doc,.docx,.txt,.md,.json,.csv,.xlsx,.xls,.pptx,.ppt,.html,.htm,.xml', '允许上传的文件类型'),
('mcp.enabled', 'true', '是否启用MCP服务（供Hermes调用）');

-- 为超级管理员角色分配所有权限
SET @super_admin_role_id = (SELECT id FROM roles WHERE code = 'super_admin');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @super_admin_role_id, id FROM permissions;

-- 为系统管理员角色分配权限
SET @system_admin_role_id = (SELECT id FROM roles WHERE code = 'system_admin');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @system_admin_role_id, id FROM permissions 
WHERE code IN (
    'dashboard', 
    'system', 'department', 'employee',
    'department:query', 'department:create', 'department:update', 'department:delete',
    'employee:query', 'employee:create', 'employee:update', 'employee:delete', 
    'employee:reset_password', 'employee:toggle_status',
    'system:setting', 'system:monitor',
    'role:manage', 'permission:manage',
    'role:query', 'role:create', 'role:update', 'role:delete', 'role:assign_permission',
    'agent', 'agent:list', 'agent:config', 'agent:conversation',
    'knowledge', 'knowledge:document', 'knowledge:setting',
    'knowledge:doc:query', 'knowledge:doc:detail', 'knowledge:doc:create',
    'knowledge:doc:update', 'knowledge:doc:delete', 'knowledge:doc:download',
    'knowledge:config:view', 'knowledge:config:edit'
);

-- 为普通用户角色分配权限
SET @user_role_id = (SELECT id FROM roles WHERE code = 'user');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @user_role_id, id FROM permissions 
WHERE code IN (
    'dashboard',
    'agent:list', 'agent:conversation',
    'knowledge:document',
    'knowledge:doc:query', 'knowledge:doc:detail', 
    'knowledge:doc:create', 'knowledge:doc:download'
);

-- ============================================
-- 十、初始化默认管理员用户
-- ============================================
-- 默认管理员账号：
-- 登录名: admin
-- 手机号: 13651165117
-- 密码: 123456 (bcrypt哈希值)
-- 注意: 首次登录后必须修改密码

INSERT INTO users (
    login_name,
    phone, 
    email, 
    password_hash, 
    username, 
    avatar_url, 
    hermes_profile, 
    hermes_profile_config, 
    is_active, 
    is_default_password, 
    is_super_admin, 
    last_login_at, 
    last_login_ip, 
    password_changed_at
)
VALUES (
    'admin',
    '13651165117',
    NULL,
    '$2b$12$kRHVDsTios01SXRdfW.HSOAHSKH84lJXUkTQf/PeGZKMlPpkucdi2',
    '系统管理员',
    NULL,
    NULL,
    NULL,
    TRUE,
    TRUE,
    TRUE,
    NULL,
    NULL,
    NULL
);

-- 为管理员用户分配超级管理员角色
SET @admin_user_id = (SELECT id FROM users WHERE login_name = 'admin');
SET @super_admin_role_id = (SELECT id FROM roles WHERE code = 'super_admin');

INSERT INTO user_roles (user_id, role_id)
VALUES (@admin_user_id, @super_admin_role_id);

-- ============================================
-- 完成提示
-- ============================================
-- 数据库初始化完成
-- 默认管理员账号:
-- 登录名: admin
-- 手机号: 13651165117
-- 密码: 123456
-- 注意: 首次登录后必须修改密码

-- ============================================
-- 知识库目录创建提示
-- ============================================
-- 创建知识库存储目录：
-- mkdir -p ~/.agentnow/knowledge/docs
-- chmod -R 755 ~/.agentnow/knowledge/

-- ============================================
-- MCP Server 配置提示
-- ============================================
-- 在 ~/.hermes/config.yaml 中添加：
--
-- mcp_servers:
--   agentnow_knowledge:
--     command: npx
--     args:
--       - "-y"
--       - "@wirux/mcp-markdown-vault"
--     env:
--       VAULT_PATH: "/Users/yourname/.agentnow/knowledge/docs"

-- ============================================
-- 十一、Hermes 系统管理菜单权限
-- ============================================

-- 插入 Hermes 一级菜单
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(0, 'Hermes 系统管理', 'hermes', 1, '/hermes', 'robot', 5);

-- 获取 Hermes 一级菜单 ID
SET @hermes_id = (SELECT id FROM permissions WHERE code = 'hermes');

-- 二级菜单 - 监控组
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@hermes_id, '系统概览', 'hermes:overview', 1, '/hermes/overview', 'dashboard', 1),
(@hermes_id, 'Profiles 管理', 'hermes:profiles', 1, '/hermes/profiles', 'apartment', 2),
(@hermes_id, '对话日志管理', 'hermes:conversations', 1, '/hermes/conversations', 'message', 3);

-- 分割线（监控组和能力组之间）
INSERT INTO permissions (parent_id, name, code, type, sort, divider)
VALUES 
(@hermes_id, '---', 'hermes:divider:1', 1, 4, 1);

-- 二级菜单 - 能力组
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@hermes_id, '技能管理', 'hermes:skills', 1, '/hermes/skills', 'tool', 5),
(@hermes_id, 'MCP 服务', 'hermes:mcp', 1, '/hermes/mcp', 'appstore', 6),
(@hermes_id, '工具集', 'hermes:tools', 1, '/hermes/tools', 'list', 7);

-- 分割线（能力组和深度信息之间）
INSERT INTO permissions (parent_id, name, code, type, sort, divider)
VALUES 
(@hermes_id, '---', 'hermes:divider:2', 1, 8, 1);

-- 二级菜单 - 深度信息
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@hermes_id, '记忆系统', 'hermes:memory', 1, '/hermes/memory', 'folder-open', 9),
(@hermes_id, '配置管理', 'hermes:config', 1, '/hermes/config', 'setting', 10),
(@hermes_id, '知识库管理', 'hermes:knowledge', 1, '/hermes/knowledge', 'file', 11);

-- 分割线（深度信息和审计之间）
INSERT INTO permissions (parent_id, name, code, type, sort, divider)
VALUES 
(@hermes_id, '---', 'hermes:divider:3', 1, 12, 1);

-- 二级菜单 - 审计
INSERT INTO permissions (parent_id, name, code, type, path, icon, sort)
VALUES 
(@hermes_id, '操作审计', 'hermes:audit', 1, '/hermes/audit', 'safety-certificate', 13);

-- 为超级管理员角色分配 Hermes 权限
SET @super_admin_role_id = (SELECT id FROM roles WHERE code = 'super_admin');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @super_admin_role_id, id FROM permissions 
WHERE code LIKE 'hermes%';

-- ============================================
-- 菜单分组说明（前端双列展示）
-- ============================================
-- Hermes 系统管理菜单共 10 个二级菜单，建议前端采用双列布局：
--
-- 第一列（监控组 + 能力组 - 6 个）
-- ├── 系统概览
-- ├── Profiles 管理
-- ├── 对话日志管理
-- ├── ────────── (分割线)
-- ├── 技能管理
-- ├── MCP 服务
-- └── 工具集
--
-- 第二列（深度信息 + 审计 - 4 个）
-- ├── 记忆系统
-- ├── 配置管理
-- ├── 知识库管理
-- ├── ────────── (分割线)
-- └── 操作审计
--
-- 或者采用单列展示（带分组标题），效果如下：
-- ┌─────────────────────────┐
-- │ 📊 监控组               │
-- │ ├── 系统概览            │
-- │ ├── Profiles 管理       │
-- │ └── 对话日志管理        │
-- ├─────────────────────────┤
-- │ ⚡ 能力组               │
-- │ ├── 技能管理            │
-- │ ├── MCP 服务            │
-- │ └── 工具集              │
-- ├─────────────────────────┤
-- │ 📁 深度信息             │
-- │ ├── 记忆系统            │
│ ├── 配置管理            │
│ └── 知识库管理          │
├─────────────────────────┤
│ 📋 审计                 │
│ └── 操作审计            │
└─────────────────────────┘
