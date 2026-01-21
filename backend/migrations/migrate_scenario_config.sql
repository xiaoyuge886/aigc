-- ============================================================================
-- 数据迁移脚本：统一场景配置到 user_scenario_configs 表
-- ============================================================================
-- 目标：
--   1. 将所有 user_configs.associated_scenario_id 迁移到 user_scenario_configs.scenario_ids
--   2. 保持 user_scenario_configs 表已有的数据
--   3. 为每个用户创建 JSON 数组格式的 scenario_ids
--
-- 执行时间：2026-01-08
-- ============================================================================

-- Step 1: 备份数据（已经在 shell 中执行）
-- cp data/sessions.db data/sessions.db.backup_YYYYMMDD_HHMMSS

-- Step 2: 查看需要迁移的数据
SELECT '===== 迁移前数据状态 =====' AS '';
SELECT 'user_configs 表中有 associated_scenario_id 的用户:' AS '';
SELECT user_id, associated_scenario_id FROM user_configs WHERE associated_scenario_id IS NOT NULL;

SELECT 'user_scenario_configs 表中已有的用户:' AS '';
SELECT user_id, scenario_ids FROM user_scenario_configs;

-- Step 3: 迁移数据（INSERT OR REPLACE 确保不重复）
-- 对于每个在 user_configs 中有 associated_scenario_id 但在 user_scenario_configs 中没有记录的用户
-- 插入一条新记录到 user_scenario_configs 表
INSERT INTO user_scenario_configs (user_id, scenario_ids, user_custom_prompt, created_at, updated_at)
SELECT
    user_id,
    JSON_ARRAY(associated_scenario_id) as scenario_ids,  -- 转换为 JSON 数组
    NULL as user_custom_prompt,
    datetime('now') as created_at,
    datetime('now') as updated_at
FROM user_configs
WHERE associated_scenario_id IS NOT NULL
AND user_id NOT IN (
    SELECT user_id FROM user_scenario_configs
);

-- Step 4: 验证迁移结果
SELECT '===== 迁移后数据状态 =====' AS '';
SELECT 'user_scenario_configs 表中的所有用户:' AS '';
SELECT
    user_id,
    scenario_ids,
    json_extract(scenario_ids, '$[0]') as first_scenario_id,  -- 提取第一个场景ID
    user_custom_prompt,
    created_at,
    updated_at
FROM user_scenario_configs
ORDER BY user_id;

-- Step 5: 对比验证（确保数据一致）
SELECT '===== 数据一致性验证 =====' AS '';
SELECT
    uc.user_id,
    uc.associated_scenario_id as old_scenario_id,
    usc.scenario_ids as new_scenario_ids,
    CASE
        WHEN usc.scenario_ids IS NULL THEN '❌ 未迁移'
        WHEN json_extract(usc.scenario_ids, '$[0]') = uc.associated_scenario_id THEN '✅ 迁移成功'
        ELSE '⚠️ 数据不一致'
    END as migration_status
FROM user_configs uc
LEFT JOIN user_scenario_configs usc ON uc.user_id = usc.user_id
WHERE uc.associated_scenario_id IS NOT NULL;

-- Step 6: 查看各用户的场景配置详情
SELECT '===== 用户场景配置详情 =====' AS '';
SELECT
    u.id as user_id,
    u.username,
    usc.scenario_ids,
    json_extract(usc.scenario_ids, '$[0]') as first_scenario_id,
    bs.name as first_scenario_name,
    bs.category as scenario_category
FROM users u
LEFT JOIN user_scenario_configs usc ON u.id = usc.user_id
LEFT JOIN user_configs uc ON u.id = uc.user_id
LEFT JOIN business_scenarios bs ON COALESCE(
    json_extract(usc.scenario_ids, '$[0]'),
    uc.associated_scenario_id
) = bs.id
WHERE u.is_active = 1
ORDER BY u.id;

-- ============================================================================
-- 注意：迁移完成后，不要立即删除 user_configs.associated_scenario_id 字段
-- 先运行一段时间，确保系统稳定后再废弃该字段
-- ============================================================================
