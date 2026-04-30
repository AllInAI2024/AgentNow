-- ============================================
-- 智能体菜单更新脚本
-- 用途：将"智能体列表"改为"我的智能体"，调整为员工侧入口
-- 执行方式：mysql -u root -p agentnow < backend/data/migrate_agent_menu_20260430.sql
-- ============================================

USE agentnow;

-- ============================================
-- 一、更新菜单项
-- ============================================

-- 将 "智能体列表" 改为 "我的智能体"，路径改为 /agents
UPDATE permissions 
SET 
    name = '我的智能体',
    path = '/agents',
    description = '员工管理和使用自己的智能体'
WHERE code = 'agent:list';

-- 将 "对话管理" 改为 "对话记录"，作为员工侧历史记录入口
-- 注意：员工侧的对话列表在聊天页面左侧，这里保留作为查看所有历史的入口
UPDATE permissions 
SET 
    name = '对话记录',
    description = '查看智能体对话历史记录'
WHERE code = 'agent:conversation';

-- 智能体配置保留为管理员功能，修改描述
UPDATE permissions 
SET 
    description = '管理智能体模板和配置（管理员功能）'
WHERE code = 'agent:config';

-- ============================================
-- 二、（可选）如果需要为普通用户添加新的权限，可在此添加
-- ============================================

-- 注意：普通用户角色(user)已经有 agent:list 和 agent:conversation 权限
-- 这是在 database.sql 中初始化的：
-- 'agent:list', 'agent:conversation'

-- ============================================
-- 三、验证更新结果
-- ============================================

SELECT 
    id,
    parent_id,
    name,
    code,
    path,
    icon,
    sort,
    description
FROM permissions 
WHERE parent_id = (SELECT id FROM permissions WHERE code = 'agent')
ORDER BY sort;

-- 显示智能体管理一级菜单信息
SELECT 
    id,
    name,
    code,
    path,
    icon
FROM permissions 
WHERE code = 'agent';
