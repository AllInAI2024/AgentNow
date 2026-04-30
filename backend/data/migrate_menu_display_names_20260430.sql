-- ============================================
-- 一级菜单名称更新脚本
-- 用途：统一一级菜单展示名称
-- 执行方式：mysql -u root -p agentnow < backend/data/migrate_menu_display_names_20260430.sql
-- ============================================

USE agentnow;

-- 更新一级菜单名称
UPDATE permissions
SET name = '智能体'
WHERE code = 'agent' AND parent_id = 0;

UPDATE permissions
SET name = '知识库'
WHERE code = 'knowledge' AND parent_id = 0;

UPDATE permissions
SET name = 'Hermes管理'
WHERE code = 'hermes' AND parent_id = 0;

-- 验证更新结果
SELECT
    id,
    parent_id,
    name,
    code,
    path,
    icon,
    sort
FROM permissions
WHERE code IN ('agent', 'knowledge', 'hermes')
ORDER BY sort;
