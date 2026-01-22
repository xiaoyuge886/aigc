-- ============================================================================
-- 技能标识统一迁移脚本：从ID数组改为名称数组
-- ============================================================================
-- 目标：
--   1. 将 business_scenarios.skills 字段从 ID 数组改为技能名称数组
--   2. 统一使用技能名称作为标识，与 SDK 系统保持一致
--   3. 简化代码逻辑，避免 ID 到名称的转换
--
-- 执行时间：2026-01-08
-- ============================================================================

-- Step 1: 查看迁移前数据状态
SELECT '===== 迁移前数据状态 =====' AS '';
SELECT
    id,
    name,
    skills,
    typeof(skills) as skills_type
FROM business_scenarios;

-- Step 2: 创建临时映射表（技能ID → 名称）
CREATE TEMP TABLE IF NOT EXISTS skill_id_mapping AS
SELECT
    id as skill_id,
    name as skill_name
FROM skills;

SELECT '===== 技能ID映射表 =====' AS '';
SELECT * FROM skill_id_mapping ORDER BY skill_id;

-- Step 3: 迁移场景1（数据分析）
-- 将 "[\"10\", \"8\", \"1\"]" 转换为 '["smart_query_analyzer", "planning_first", "echarts_chart"]'
UPDATE business_scenarios
SET skills = '["smart_query_analyzer", "planning_first", "echarts_chart"]'
WHERE id = 1 AND skills = '["\"10\", \"8\", \"1\"]';

-- Step 4: 验证场景1的迁移
SELECT '===== 场景1迁移验证 =====' AS '';
SELECT id, name, skills FROM business_scenarios WHERE id = 1;

-- Step 5: 验证所有场景的skills格式
SELECT '===== 迁移后数据状态 =====' AS '';
SELECT
    id,
    name,
    skills,
    CASE
        WHEN skills IS NULL THEN 'NULL'
        WHEN json_extract(skills, '$.skills') IS NOT NULL THEN 'JSON对象格式'
        WHEN json_valid(skills) THEN 'JSON数组格式'
        ELSE '字符串格式'
    END as format_type
FROM business_scenarios;

-- Step 6: 提取技能名称（用于验证）
SELECT '===== 技能名称提取验证 =====' AS '';
SELECT
    id,
    name,
    json_extract(skills, '$') as skill_names,
    json_array_length(json_extract(skills, '$')) as skill_count
FROM business_scenarios
WHERE skills IS NOT NULL AND json_valid(skills);

-- Step 7: 对比验证（确保映射正确）
SELECT '===== 技能映射对比验证 =====' AS '';
SELECT
    bs.id as scenario_id,
    bs.name as scenario_name,
    bs.skills as skills_json,
    json_extract(bs.skills, '$') as skill_names,
    -- 检查每个技能名称是否存在于skills表中
    (
        SELECT GROUP_CONCAT(s.name, ', ')
        FROM skill_id_mapping s
        WHERE s.name IN (
            SELECT value FROM json_each(bs.skills)
        )
    ) as verified_skills
FROM business_scenarios bs
WHERE bs.skills IS NOT NULL
AND json_valid(bs.skills);

-- ============================================================================
-- 注意事项：
-- 1. 场景3（默认场景）已经使用名称数组格式，无需修改
-- 2. 场景2（程序员）和场景4（通用场景）的skills为NULL，无需修改
-- 3. 迁移后，skills字段将统一使用JSON数组格式的技能名称
-- 4. 后端代码需要相应修改，直接使用技能名称而不是ID
-- ============================================================================
