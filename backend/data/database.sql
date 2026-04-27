-- 智现 AgentNow 智能体平台数据库初始化脚本
-- 数据库: agentnow
-- 版本: v4.0 (简化版 RBAC 权限管理系统)
-- 日期: 2026-04-27

-- 创建数据库
CREATE DATABASE IF NOT EXISTS agentnow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE agentnow;

-- ============================================
-- 一、用户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    phone VARCHAR(20) NOT NULL COMMENT '手机号/登录账号',
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
    UNIQUE KEY uk_phone (phone),
    UNIQUE KEY uk_email (email),
    INDEX idx_hermes_profile (hermes_profile),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 二、角色表
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
-- 三、权限表
-- ============================================
CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父权限ID（0表示顶级）',
    name VARCHAR(50) NOT NULL COMMENT '权限名称',
    code VARCHAR(100) NOT NULL COMMENT '权限编码（英文标识，如user:list, user:create）',
    type TINYINT DEFAULT 1 COMMENT '类型：1-菜单，2-按钮，3-API接口',
    path VARCHAR(255) COMMENT '路由路径/接口路径',
    icon VARCHAR(100) COMMENT '菜单图标',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_parent_id (parent_id),
    INDEX idx_code (code),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';

-- ============================================
-- 四、角色-权限关联表
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
-- 五、用户-角色关联表
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
-- 六、初始化数据
-- ============================================

-- 插入系统内置角色
INSERT INTO roles (name, code, description)
VALUES 
('超级管理员', 'super_admin', '系统超级管理员，拥有所有权限'),
('系统管理员', 'system_admin', '系统管理员，拥有系统管理权限'),
('普通用户', 'user', '普通用户，拥有基本操作权限');

-- 插入系统权限/功能点（菜单结构）
-- 一级菜单
INSERT INTO permissions (parent_id, name, code, type, path, icon)
VALUES 
(0, '工作台', 'dashboard', 1, '/dashboard', 'dashboard'),
(0, '系统管理', 'system', 1, '/system', 'setting'),
(0, '用户管理', 'user', 1, '/user', 'user'),
(0, '角色权限', 'role', 1, '/role', 'safety-certificate'),
(0, '智能体管理', 'agent', 1, '/agent', 'robot'),
(0, '知识库管理', 'knowledge', 1, '/knowledge', 'folder-open');

-- 获取父权限ID
SET @dashboard_id = (SELECT id FROM permissions WHERE code = 'dashboard');
SET @system_id = (SELECT id FROM permissions WHERE code = 'system');
SET @user_id = (SELECT id FROM permissions WHERE code = 'user');
SET @role_id = (SELECT id FROM permissions WHERE code = 'role');
SET @agent_id = (SELECT id FROM permissions WHERE code = 'agent');
SET @knowledge_id = (SELECT id FROM permissions WHERE code = 'knowledge');

-- 二级菜单 - 系统管理
INSERT INTO permissions (parent_id, name, code, type, path, icon)
VALUES 
(@system_id, '系统设置', 'system:setting', 1, '/system/setting', 'tool'),
(@system_id, '系统监控', 'system:monitor', 1, '/system/monitor', 'monitor');

-- 二级菜单 - 用户管理
INSERT INTO permissions (parent_id, name, code, type, path, icon)
VALUES 
(@user_id, '用户列表', 'user:list', 1, '/user/list', 'list');

-- 二级菜单 - 角色权限
INSERT INTO permissions (parent_id, name, code, type, path, icon)
VALUES 
(@role_id, '角色列表', 'role:list', 1, '/role/list', 'list'),
(@role_id, '权限配置', 'role:permission', 1, '/role/permission', 'key');

-- 二级菜单 - 智能体管理
INSERT INTO permissions (parent_id, name, code, type, path, icon)
VALUES 
(@agent_id, '智能体列表', 'agent:list', 1, '/agent/list', 'list'),
(@agent_id, '智能体配置', 'agent:config', 1, '/agent/config', 'setting'),
(@agent_id, '对话管理', 'agent:conversation', 1, '/agent/conversation', 'message');

-- 二级菜单 - 知识库管理
INSERT INTO permissions (parent_id, name, code, type, path, icon)
VALUES 
(@knowledge_id, '文档列表', 'knowledge:document', 1, '/knowledge/document', 'file'),
(@knowledge_id, '知识库设置', 'knowledge:setting', 1, '/knowledge/setting', 'setting');

-- 插入按钮/接口级权限
-- 获取一些二级菜单的ID
SET @user_list_id = (SELECT id FROM permissions WHERE code = 'user:list');
SET @role_list_id = (SELECT id FROM permissions WHERE code = 'role:list');

-- 用户管理相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@user_list_id, '用户查询', 'user:query', 3, '/api/v1/users'),
(@user_list_id, '用户创建', 'user:create', 3, '/api/v1/users'),
(@user_list_id, '用户编辑', 'user:update', 3, '/api/v1/users/:id'),
(@user_list_id, '用户删除', 'user:delete', 3, '/api/v1/users/:id'),
(@user_list_id, '用户重置密码', 'user:reset_password', 3, '/api/v1/users/:id/reset-password'),
(@user_list_id, '用户启用/禁用', 'user:toggle_status', 3, '/api/v1/users/:id/status');

-- 角色管理相关按钮权限
INSERT INTO permissions (parent_id, name, code, type, path)
VALUES 
(@role_list_id, '角色查询', 'role:query', 3, '/api/v1/roles'),
(@role_list_id, '角色创建', 'role:create', 3, '/api/v1/roles'),
(@role_list_id, '角色编辑', 'role:update', 3, '/api/v1/roles/:id'),
(@role_list_id, '角色删除', 'role:delete', 3, '/api/v1/roles/:id'),
(@role_list_id, '角色权限配置', 'role:assign_permission', 3, '/api/v1/roles/:id/permissions');

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
    'system', 'system:setting', 'system:monitor',
    'user', 'user:list',
    'user:query', 'user:create', 'user:update', 'user:delete', 'user:reset_password', 'user:toggle_status',
    'role', 'role:list', 'role:permission',
    'role:query', 'role:create', 'role:update', 'role:delete', 'role:assign_permission',
    'agent', 'agent:list', 'agent:config', 'agent:conversation',
    'knowledge', 'knowledge:document', 'knowledge:setting'
);

-- 为普通用户角色分配权限
SET @user_role_id = (SELECT id FROM roles WHERE code = 'user');

INSERT INTO role_permissions (role_id, permission_id)
SELECT @user_role_id, id FROM permissions 
WHERE code IN (
    'dashboard',
    'agent:list', 'agent:conversation',
    'knowledge:document'
);

-- ============================================
-- 七、初始化默认管理员用户
-- ============================================
-- 默认管理员账号：
-- 手机号: 13651165117
-- 密码: 123456 (bcrypt哈希值)
-- 注意: 首次登录后必须修改密码

INSERT INTO users (
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
    '13651165117',
    NULL,
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/XewdhYfU/xBBbq/2K',
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
SET @admin_user_id = (SELECT id FROM users WHERE phone = '13651165117');
SET @super_admin_role_id = (SELECT id FROM roles WHERE code = 'super_admin');

INSERT INTO user_roles (user_id, role_id)
VALUES (@admin_user_id, @super_admin_role_id);

-- ============================================
-- 完成提示
-- ============================================
-- 数据库初始化完成
-- 默认管理员账号:
-- 手机号: 13651165117
-- 密码: 123456
-- 注意: 首次登录后必须修改密码