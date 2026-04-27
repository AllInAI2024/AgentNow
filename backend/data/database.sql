-- 智现 AgentNow 企业智能体平台数据库初始化脚本
-- 数据库: agentnow
-- 版本: v1.0
-- 日期: 2026-04-27

-- 创建数据库
CREATE DATABASE IF NOT EXISTS agentnow DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE agentnow;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    phone VARCHAR(20) NOT NULL UNIQUE COMMENT '账号',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    role VARCHAR(20) DEFAULT 'user' COMMENT '角色：admin-管理员，user-普通用户',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    is_default_password BOOLEAN DEFAULT TRUE COMMENT '是否为默认密码（首次登录需修改）',
    hermes_profile VARCHAR(100) COMMENT '对应的 Hermes Profile 名称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_phone (phone),
    INDEX idx_role (role),
    INDEX idx_hermes_profile (hermes_profile)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 初始化默认管理员账号
-- 默认账号: 13651165117
-- 默认密码: 123456 (bcrypt加密后的值)
-- 注意: 实际插入时需要使用Python的bcrypt库生成真实的哈希值
-- 这里使用占位符，实际在应用启动时初始化

-- 插入管理员记录的示例SQL (实际密码哈希需要在应用中生成)
-- INSERT INTO users (phone, password_hash, username, role, is_active, is_default_password)
-- VALUES ('13651165117', '实际的bcrypt哈希值', '系统管理员', 'admin', TRUE, TRUE);
