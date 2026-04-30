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
    path = '/agents'
WHERE code = 'agent:list';

-- 将 "对话管理" 改为 "对话记录"
UPDATE permissions 
SET 
    name = '对话记录'
WHERE code = 'agent:conversation';

-- ============================================
-- 二、验证更新结果
-- ============================================

SELECT 
    id,
    parent_id,
    name,
    code,
    path,
    icon,
    sort
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
