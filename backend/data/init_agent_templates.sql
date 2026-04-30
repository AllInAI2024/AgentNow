-- ============================================
-- 智能体模板初始化脚本
-- 用途：创建默认的智能体模板，供员工开通使用
-- 执行方式：mysql -u root -p agentnow < backend/data/init_agent_templates.sql
-- ============================================

USE agentnow;

-- ============================================
-- 一、创建默认的 PPT 生成智能体模板
-- ============================================

-- 检查是否已存在默认模板（避免重复插入）
SET @existing_id = (SELECT id FROM agent_templates WHERE is_default = TRUE AND deleted_at IS NULL LIMIT 1);

-- 如果不存在默认模板，则创建
INSERT INTO agent_templates (
    code,
    name,
    description,
    template_type,
    role_prompt,
    system_prompt,
    welcome_message,
    knowledge_scope,
    tool_policy,
    model_config,
    status,
    is_default,
    version,
    created_by
)
SELECT 
    'ppt_assistant',
    'PPT 智能助手',
    '帮助用户快速生成专业的 PPT 演示文稿。支持需求理解、大纲设计、风格选择、内容生成等完整流程。',
    'business',
    '你是一位专业的 PPT 制作顾问和演示文稿设计师。你的目标是帮助用户快速创建高质量、专业的演示文稿。

你应该：
1. 主动询问用户的演示目标、受众、时间限制等关键信息
2. 提供清晰的大纲建议和结构规划
3. 帮助用户选择合适的视觉风格
4. 提供专业的内容建议和优化
5. 确保演示文稿逻辑清晰、重点突出',
    '## 角色定位
你是专业的 PPT 制作顾问，擅长将复杂信息转化为清晰、有说服力的演示文稿。

## 工作流程
1. **需求确认**：了解演示目的、受众、时长、风格偏好
2. **大纲设计**：基于需求设计演示文稿结构和逻辑
3. **内容填充**：为每个页面提供内容建议和文案
4. **风格选择**：推荐合适的配色方案和视觉风格
5. **生成交付**：确认后生成最终的 PPT 文件

## 输出规范
- 使用清晰的层级结构（标题、要点、子要点）
- 每个页面建议 3-5 个要点
- 提供具体的文案示例，而非抽象建议
- 关键数据用可视化方式呈现',
    '你好！我是 PPT 智能助手 🎯

我可以帮你：
- 📋 梳理演示需求，设计大纲结构
- ✍️ 提供专业的内容建议和文案
- 🎨 推荐合适的视觉风格
- 📊 生成最终的 PPT 文件

请告诉我：
1. 你想做什么主题的演示？
2. 目标受众是谁？
3. 预计演示时长？

或者直接描述你的需求，我来帮你规划！',
    'global',
    '{"allowed_tools": ["file_read", "file_write", "web_search"], "tool_policy": "auto"}',
    '{"model": "gpt-4o", "temperature": 0.7, "max_tokens": 4096}',
    1,
    TRUE,
    1,
    1
WHERE @existing_id IS NULL;

-- ============================================
-- 二、创建模板版本（快照）
-- ============================================

-- 获取默认模板 ID
SET @default_template_id = (SELECT id FROM agent_templates WHERE is_default = TRUE AND deleted_at IS NULL LIMIT 1);

-- 检查是否已存在版本记录
SET @existing_version = (SELECT id FROM agent_template_versions WHERE template_id = @default_template_id AND version_no = 1 LIMIT 1);

-- 插入版本快照
INSERT INTO agent_template_versions (
    template_id,
    version_no,
    version_label,
    change_summary,
    template_snapshot,
    published_by
)
SELECT 
    @default_template_id,
    1,
    'v1.0 初始版本',
    '默认 PPT 智能助手模板初始版本',
    JSON_OBJECT(
        'id', @default_template_id,
        'code', 'ppt_assistant',
        'name', 'PPT 智能助手',
        'description', '帮助用户快速生成专业的 PPT 演示文稿',
        'template_type', 'business',
        'role_prompt', '你是一位专业的 PPT 制作顾问...',
        'system_prompt', '## 角色定位...',
        'welcome_message', '你好！我是 PPT 智能助手...',
        'knowledge_scope', 'global',
        'tool_policy', JSON_OBJECT('allowed_tools', JSON_ARRAY('file_read', 'file_write', 'web_search'), 'tool_policy', 'auto'),
        'model_config', JSON_OBJECT('model', 'gpt-4o', 'temperature', 0.7, 'max_tokens', 4096),
        'status', 1,
        'is_default', TRUE,
        'version', 1
    ),
    1
WHERE @existing_version IS NULL AND @default_template_id IS NOT NULL;

-- ============================================
-- 三、输出结果
-- ============================================

SELECT 
    '默认模板创建完成' AS message,
    @default_template_id AS template_id,
    (SELECT COUNT(*) FROM agent_templates WHERE is_default = TRUE) AS default_template_count;

-- 显示所有模板
SELECT 
    id,
    code,
    name,
    template_type,
    status,
    is_default,
    version
FROM agent_templates
WHERE deleted_at IS NULL
ORDER BY is_default DESC, id;
