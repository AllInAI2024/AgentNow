-- 智现 AgentNow 企业智能体平台数据库初始化脚本
-- 数据库: agentnow
-- 版本: v2.0 (RBAC权限管理系统)
-- 日期: 2026-04-27

-- 创建数据库
CREATE DATABASE IF NOT EXISTS agentnow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE agentnow;

-- ============================================
-- 一、企业表
-- ============================================
CREATE TABLE IF NOT EXISTS enterprises (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '企业ID',
    name VARCHAR(100) NOT NULL COMMENT '企业名称',
    short_name VARCHAR(50) COMMENT '企业简称',
    code VARCHAR(50) COMMENT '企业代码/统一社会信用代码',
    contact_person VARCHAR(50) COMMENT '联系人',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    contact_email VARCHAR(100) COMMENT '联系邮箱',
    address VARCHAR(255) COMMENT '企业地址',
    logo_url VARCHAR(500) COMMENT '企业Logo URL',
    description TEXT COMMENT '企业描述',
    industry VARCHAR(100) COMMENT '所属行业',
    scale VARCHAR(50) COMMENT '企业规模',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '是否认证',
    verified_at DATETIME COMMENT '认证时间',
    verified_by BIGINT COMMENT '认证人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_code (code),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业表';

-- ============================================
-- 二、用户表 (重新设计，支持RBAC)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    enterprise_id BIGINT COMMENT '所属企业ID',
    phone VARCHAR(20) NOT NULL COMMENT '手机号/登录账号',
    email VARCHAR(100) COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    username VARCHAR(50) NOT NULL COMMENT '用户姓名/昵称',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    department VARCHAR(100) COMMENT '部门',
    position VARCHAR(100) COMMENT '职位',
    employee_no VARCHAR(50) COMMENT '员工工号',
    gender TINYINT DEFAULT 0 COMMENT '性别：0-未知，1-男，2-女',
    birthday DATE COMMENT '生日',
    hermes_profile VARCHAR(100) COMMENT '对应的 Hermes Profile 名称',
    hermes_profile_config TEXT COMMENT 'Hermes Profile 配置(JSON)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_default_password BOOLEAN DEFAULT TRUE COMMENT '是否为默认密码（首次登录需修改）',
    is_super_admin BOOLEAN DEFAULT FALSE COMMENT '是否为超级管理员（跨企业全局权限）',
    last_login_at DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(50) COMMENT '最后登录IP',
    password_changed_at DATETIME COMMENT '密码修改时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_phone (phone),
    UNIQUE KEY uk_email (email),
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_hermes_profile (hermes_profile),
    INDEX idx_is_active (is_active),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 三、角色表
-- ============================================
CREATE TABLE IF NOT EXISTS roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    enterprise_id BIGINT COMMENT '所属企业ID（NULL表示系统内置角色）',
    name VARCHAR(50) NOT NULL COMMENT '角色名称',
    code VARCHAR(50) NOT NULL COMMENT '角色编码（英文标识）',
    description TEXT COMMENT '角色描述',
    sort INT DEFAULT 0 COMMENT '排序号',
    status TINYINT DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否为系统内置角色（不可删除）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_code (code),
    INDEX idx_status (status),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- ============================================
-- 四、功能点/权限表
-- ============================================
CREATE TABLE IF NOT EXISTS permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '权限ID',
    parent_id BIGINT DEFAULT 0 COMMENT '父权限ID（0表示顶级）',
    enterprise_id BIGINT COMMENT '所属企业ID（NULL表示系统权限）',
    name VARCHAR(50) NOT NULL COMMENT '权限名称',
    code VARCHAR(100) NOT NULL COMMENT '权限编码（英文标识，如user:list, user:create）',
    type TINYINT DEFAULT 1 COMMENT '类型：1-菜单，2-按钮，3-API接口',
    path VARCHAR(255) COMMENT '路由路径/接口路径',
    component VARCHAR(255) COMMENT '前端组件路径',
    icon VARCHAR(100) COMMENT '菜单图标',
    sort INT DEFAULT 0 COMMENT '排序号',
    status TINYINT DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    visible BOOLEAN DEFAULT TRUE COMMENT '菜单是否显示',
    keep_alive BOOLEAN DEFAULT FALSE COMMENT '是否缓存路由',
    redirect VARCHAR(255) COMMENT '重定向路径',
    permission_level TINYINT DEFAULT 1 COMMENT '权限级别：1-普通，2-敏感，3-高危',
    description TEXT COMMENT '权限描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_parent_id (parent_id),
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_code (code),
    INDEX idx_type (type),
    INDEX idx_status (status),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='功能点/权限表';

-- ============================================
-- 五、用户-角色关联表
-- ============================================
CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by BIGINT COMMENT '创建人ID',
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户-角色关联表';

-- ============================================
-- 六、角色-权限关联表
-- ============================================
CREATE TABLE IF NOT EXISTS role_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '关联ID',
    role_id BIGINT NOT NULL COMMENT '角色ID',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    created_by BIGINT COMMENT '创建人ID',
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色-权限关联表';

-- ============================================
-- 七、操作日志表
-- ============================================
CREATE TABLE IF NOT EXISTS operation_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    enterprise_id BIGINT COMMENT '企业ID',
    user_id BIGINT COMMENT '操作用户ID',
    username VARCHAR(50) COMMENT '操作用户名',
    module VARCHAR(100) COMMENT '操作模块',
    business_type VARCHAR(50) COMMENT '业务类型',
    method VARCHAR(20) COMMENT '请求方法：GET, POST, PUT, DELETE',
    request_url VARCHAR(500) COMMENT '请求URL',
    request_params TEXT COMMENT '请求参数(JSON)',
    response_code INT COMMENT '响应状态码',
    response_msg VARCHAR(500) COMMENT '响应消息',
    response_data TEXT COMMENT '响应数据(JSON)',
    ip VARCHAR(50) COMMENT '操作IP',
    location VARCHAR(255) COMMENT '操作地点',
    browser VARCHAR(100) COMMENT '浏览器',
    os VARCHAR(100) COMMENT '操作系统',
    status TINYINT DEFAULT 1 COMMENT '操作状态：0-失败，1-成功',
    error_msg TEXT COMMENT '错误信息',
    cost_time INT COMMENT '耗时(毫秒)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_user_id (user_id),
    INDEX idx_module (module),
    INDEX idx_business_type (business_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- ============================================
-- 八、登录日志表
-- ============================================
CREATE TABLE IF NOT EXISTS login_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    enterprise_id BIGINT COMMENT '企业ID',
    user_id BIGINT COMMENT '用户ID',
    username VARCHAR(50) COMMENT '用户名',
    phone VARCHAR(20) COMMENT '登录账号',
    ip VARCHAR(50) COMMENT '登录IP',
    location VARCHAR(255) COMMENT '登录地点',
    browser VARCHAR(100) COMMENT '浏览器',
    os VARCHAR(100) COMMENT '操作系统',
    device VARCHAR(100) COMMENT '设备信息',
    status TINYINT DEFAULT 0 COMMENT '登录状态：0-失败，1-成功',
    failure_reason VARCHAR(255) COMMENT '失败原因',
    token VARCHAR(500) COMMENT '登录Token',
    logout_at DATETIME COMMENT '登出时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_user_id (user_id),
    INDEX idx_phone (phone),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='登录日志表';

-- ============================================
-- 九、初始化数据
-- ============================================

-- 插入默认企业
INSERT INTO enterprises (name, short_name, contact_person, contact_phone, is_active, is_verified)
VALUES ('智现科技有限公司', '智现科技', '系统管理员', '13651165117', TRUE, TRUE);

-- 插入系统内置角色
INSERT INTO roles (enterprise_id, name, code, description, sort, status, is_system)
VALUES 
(NULL, '超级管理员', 'super_admin', '系统超级管理员，拥有所有权限', 1, 1, TRUE),
(NULL, '企业管理员', 'enterprise_admin', '企业管理员，拥有企业内所有权限', 2, 1, TRUE),
(NULL, '部门管理员', 'dept_admin', '部门管理员，拥有部门内管理权限', 3, 1, TRUE),
(NULL, '普通用户', 'user', '普通用户，拥有基本操作权限', 4, 1, TRUE);

-- 插入系统权限/功能点（菜单结构）
-- 一级菜单
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, icon, sort, status, visible, description)
VALUES 
(0, NULL, '工作台', 'dashboard', 1, '/dashboard', 'dashboard', 1, 1, 1, '系统工作台'),
(0, NULL, '系统管理', 'system', 1, '/system', 'setting', 2, 1, 1, '系统管理模块'),
(0, NULL, '企业管理', 'enterprise', 1, '/enterprise', 'office', 3, 1, 1, '企业管理模块'),
(0, NULL, '用户管理', 'user', 1, '/user', 'user', 4, 1, 1, '用户管理模块'),
(0, NULL, '角色权限', 'role', 1, '/role', 'safety-certificate', 5, 1, 1, '角色权限管理'),
(0, NULL, '日志管理', 'log', 1, '/log', 'file-text', 6, 1, 1, '日志管理模块'),
(0, NULL, '智能体管理', 'agent', 1, '/agent', 'robot', 7, 1, 1, '智能体管理模块'),
(0, NULL, '知识库管理', 'knowledge', 1, '/knowledge', 'folder-open', 8, 1, 1, '知识库管理模块');

-- 获取父权限ID（假设按顺序插入）
-- 这里使用变量来获取实际的ID
SET @dashboard_id = (SELECT id FROM permissions WHERE code = 'dashboard');
SET @system_id = (SELECT id FROM permissions WHERE code = 'system');
SET @enterprise_id = (SELECT id FROM permissions WHERE code = 'enterprise');
SET @user_id = (SELECT id FROM permissions WHERE code = 'user');
SET @role_id = (SELECT id FROM permissions WHERE code = 'role');
SET @log_id = (SELECT id FROM permissions WHERE code = 'log');
SET @agent_id = (SELECT id FROM permissions WHERE code = 'agent');
SET @knowledge_id = (SELECT id FROM permissions WHERE code = 'knowledge');

-- 二级菜单 - 系统管理
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@system_id, NULL, '系统设置', 'system:setting', 1, '/system/setting', 'system/setting/index', 'tool', 1, 1, 1, '系统设置'),
(@system_id, NULL, '系统监控', 'system:monitor', 1, '/system/monitor', 'system/monitor/index', 'monitor', 2, 1, 1, '系统监控');

-- 二级菜单 - 企业管理
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@enterprise_id, NULL, '企业列表', 'enterprise:list', 1, '/enterprise/list', 'enterprise/list/index', 'list', 1, 1, 1, '企业列表'),
(@enterprise_id, NULL, '企业信息', 'enterprise:info', 1, '/enterprise/info', 'enterprise/info/index', 'info-circle', 2, 1, 1, '企业信息维护');

-- 二级菜单 - 用户管理
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@user_id, NULL, '用户列表', 'user:list', 1, '/user/list', 'user/list/index', 'list', 1, 1, 1, '用户列表'),
(@user_id, NULL, '用户导入', 'user:import', 1, '/user/import', 'user/import/index', 'upload', 2, 1, 1, '批量导入用户');

-- 二级菜单 - 角色权限
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@role_id, NULL, '角色列表', 'role:list', 1, '/role/list', 'role/list/index', 'list', 1, 1, 1, '角色列表'),
(@role_id, NULL, '权限配置', 'role:permission', 1, '/role/permission', 'role/permission/index', 'key', 2, 1, 1, '权限配置');

-- 二级菜单 - 日志管理
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@log_id, NULL, '操作日志', 'log:operation', 1, '/log/operation', 'log/operation/index', 'file-text', 1, 1, 1, '操作日志'),
(@log_id, NULL, '登录日志', 'log:login', 1, '/log/login', 'log/login/index', 'login', 2, 1, 1, '登录日志');

-- 二级菜单 - 智能体管理
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@agent_id, NULL, '智能体列表', 'agent:list', 1, '/agent/list', 'agent/list/index', 'list', 1, 1, 1, '智能体列表'),
(@agent_id, NULL, '智能体配置', 'agent:config', 1, '/agent/config', 'agent/config/index', 'setting', 2, 1, 1, '智能体配置'),
(@agent_id, NULL, '对话管理', 'agent:conversation', 1, '/agent/conversation', 'agent/conversation/index', 'message', 3, 1, 1, '对话管理');

-- 二级菜单 - 知识库管理
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, component, icon, sort, status, visible, description)
VALUES 
(@knowledge_id, NULL, '文档列表', 'knowledge:document', 1, '/knowledge/document', 'knowledge/document/index', 'file', 1, 1, 1, '文档列表'),
(@knowledge_id, NULL, '知识库设置', 'knowledge:setting', 1, '/knowledge/setting', 'knowledge/setting/index', 'setting', 2, 1, 1, '知识库设置');

-- 插入按钮/接口级权限（示例）
-- 获取一些二级菜单的ID
SET @user_list_id = (SELECT id FROM permissions WHERE code = 'user:list');
SET @role_list_id = (SELECT id FROM permissions WHERE code = 'role:list');
SET @enterprise_list_id = (SELECT id FROM permissions WHERE code = 'enterprise:list');

-- 用户管理相关按钮权限
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, sort, status, visible, description)
VALUES 
(@user_list_id, NULL, '用户查询', 'user:query', 3, '/api/v1/users', 1, 1, 0, '查询用户列表'),
(@user_list_id, NULL, '用户创建', 'user:create', 3, '/api/v1/users', 2, 1, 0, '创建用户'),
(@user_list_id, NULL, '用户编辑', 'user:update', 3, '/api/v1/users/:id', 3, 1, 0, '编辑用户'),
(@user_list_id, NULL, '用户删除', 'user:delete', 3, '/api/v1/users/:id', 4, 1, 0, '删除用户'),
(@user_list_id, NULL, '用户重置密码', 'user:reset_password', 3, '/api/v1/users/:id/reset-password', 5, 1, 0, '重置用户密码'),
(@user_list_id, NULL, '用户启用/禁用', 'user:toggle_status', 3, '/api/v1/users/:id/status', 6, 1, 0, '启用/禁用用户');

-- 角色管理相关按钮权限
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, sort, status, visible, description)
VALUES 
(@role_list_id, NULL, '角色查询', 'role:query', 3, '/api/v1/roles', 1, 1, 0, '查询角色列表'),
(@role_list_id, NULL, '角色创建', 'role:create', 3, '/api/v1/roles', 2, 1, 0, '创建角色'),
(@role_list_id, NULL, '角色编辑', 'role:update', 3, '/api/v1/roles/:id', 3, 1, 0, '编辑角色'),
(@role_list_id, NULL, '角色删除', 'role:delete', 3, '/api/v1/roles/:id', 4, 1, 0, '删除角色'),
(@role_list_id, NULL, '角色权限配置', 'role:assign_permission', 3, '/api/v1/roles/:id/permissions', 5, 1, 0, '为角色分配权限');

-- 企业管理相关按钮权限
INSERT INTO permissions (parent_id, enterprise_id, name, code, type, path, sort, status, visible, description)
VALUES 
(@enterprise_list_id, NULL, '企业查询', 'enterprise:query', 3, '/api/v1/enterprises', 1, 1, 0, '查询企业列表'),
(@enterprise_list_id, NULL, '企业创建', 'enterprise:create', 3, '/api/v1/enterprises', 2, 1, 0, '创建企业'),
(@enterprise_list_id, NULL, '企业编辑', 'enterprise:update', 3, '/api/v1/enterprises/:id', 3, 1, 0, '编辑企业'),
(@enterprise_list_id, NULL, '企业删除', 'enterprise:delete', 3, '/api/v1/enterprises/:id', 4, 1, 0, '删除企业'),
(@enterprise_list_id, NULL, '企业认证', 'enterprise:verify', 3, '/api/v1/enterprises/:id/verify', 5, 1, 0, '认证企业');

-- 为超级管理员角色分配所有权限
-- 首先获取角色和权限的ID
SET @super_admin_role_id = (SELECT id FROM roles WHERE code = 'super_admin');

-- 插入角色权限关联（超级管理员拥有所有权限）
INSERT INTO role_permissions (role_id, permission_id)
SELECT @super_admin_role_id, id FROM permissions;

-- 为企业管理员角色分配权限（示例：分配用户管理和角色管理权限）
SET @enterprise_admin_role_id = (SELECT id FROM roles WHERE code = 'enterprise_admin');

-- 插入角色权限关联（企业管理员）
INSERT INTO role_permissions (role_id, permission_id)
SELECT @enterprise_admin_role_id, id FROM permissions 
WHERE code IN (
    'dashboard', 
    'user', 'user:list', 'user:info',
    'user:query', 'user:create', 'user:update', 'user:delete', 'user:reset_password', 'user:toggle_status',
    'role', 'role:list', 'role:permission',
    'role:query', 'role:create', 'role:update', 'role:assign_permission',
    'log', 'log:operation', 'log:login',
    'agent', 'agent:list', 'agent:config', 'agent:conversation',
    'knowledge', 'knowledge:document', 'knowledge:setting'
);

-- 为普通用户角色分配权限
SET @user_role_id = (SELECT id FROM roles WHERE code = 'user');

-- 插入角色权限关联（普通用户）
INSERT INTO role_permissions (role_id, permission_id)
SELECT @user_role_id, id FROM permissions 
WHERE code IN (
    'dashboard',
    'agent:list', 'agent:conversation',
    'knowledge:document'
);

-- ============================================
-- 十、创建视图（方便查询）
-- ============================================

-- 用户角色权限视图
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT 
    u.id AS user_id,
    u.phone,
    u.username,
    u.enterprise_id,
    r.id AS role_id,
    r.name AS role_name,
    r.code AS role_code,
    p.id AS permission_id,
    p.name AS permission_name,
    p.code AS permission_code,
    p.type AS permission_type,
    p.path,
    p.parent_id
FROM users u
INNER JOIN user_roles ur ON u.id = ur.user_id
INNER JOIN roles r ON ur.role_id = r.id
INNER JOIN role_permissions rp ON r.id = rp.role_id
INNER JOIN permissions p ON rp.permission_id = p.id
WHERE u.is_active = TRUE AND r.status = 1 AND p.status = 1;

-- 角色权限视图
CREATE OR REPLACE VIEW v_role_permissions AS
SELECT 
    r.id AS role_id,
    r.name AS role_name,
    r.code AS role_code,
    r.enterprise_id AS role_enterprise_id,
    p.id AS permission_id,
    p.name AS permission_name,
    p.code AS permission_code,
    p.type AS permission_type,
    p.path,
    p.parent_id,
    p.icon,
    p.sort,
    p.visible
FROM roles r
INNER JOIN role_permissions rp ON r.id = rp.role_id
INNER JOIN permissions p ON rp.permission_id = p.id
WHERE r.status = 1 AND p.status = 1;

-- ============================================
-- 十一、创建存储过程（示例）
-- ============================================

-- 获取用户权限列表
DELIMITER //
CREATE PROCEDURE GetUserPermissions(IN p_user_id BIGINT)
BEGIN
    SELECT DISTINCT 
        p.id,
        p.parent_id,
        p.name,
        p.code,
        p.type,
        p.path,
        p.component,
        p.icon,
        p.sort,
        p.visible,
        p.keep_alive,
        p.redirect
    FROM v_user_permissions p
    WHERE p.user_id = p_user_id
    ORDER BY p.parent_id, p.sort;
END //
DELIMITER ;

-- 检查用户是否拥有权限
DELIMITER //
CREATE PROCEDURE CheckUserPermission(
    IN p_user_id BIGINT,
    IN p_permission_code VARCHAR(100),
    OUT p_has_permission BOOLEAN
)
BEGIN
    SELECT COUNT(*) > 0 INTO p_has_permission
    FROM v_user_permissions p
    WHERE p.user_id = p_user_id AND p.permission_code = p_permission_code;
END //
DELIMITER ;

-- ============================================
-- 完成提示
-- ============================================
-- 数据库初始化完成
-- 注意：超级管理员账号需要在应用启动时初始化
-- 默认超级管理员配置在 .env 文件中：
-- DEFAULT_ADMIN_PHONE=13651165117
-- DEFAULT_ADMIN_PASSWORD=123456
