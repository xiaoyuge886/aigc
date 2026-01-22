# 部署与运维文档

## 1. 环境要求

### 1.1 基础环境
- **Python**: 3.11+
- **Node.js**: 18+
- **数据库**: SQLite（内置）
- **存储**: MinIO（文件存储，可选）

### 1.2 依赖服务
- **Claude Agent SDK**: 已集成
- **Anthropic API Key**: 必需

## 2. 本地开发部署

### 2.1 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2.2 前端启动
```bash
cd frontend/aigc-frontend
npm install
npm run dev
```

### 2.3 一键启动（推荐）
```bash
# macOS / Linux
./scripts/start.sh

# Windows
scripts/start.bat
```

## 3. 生产环境部署

### 3.1 Docker 部署
```bash
# 构建镜像
docker build -f deploy/Dockerfile -t aigc-backend:latest .

# 使用 Docker Compose
cd deploy
docker-compose up -d
```

### 3.2 环境变量配置
```bash
# .env 文件
ANTHROPIC_API_KEY=your-api-key
HOST=0.0.0.0
PORT=8000
DEBUG=false
DEFAULT_MODEL=sonnet
```

### 3.3 数据持久化
挂载以下目录：
- `/app/data`: SQLite 数据库
- `/app/work_dir`: 生成的文件
- `/app/logs`: 日志文件

## 4. 数据库迁移

### 4.1 初始化数据库
```bash
cd backend
python -m migrations.init_database
```

### 4.2 执行迁移脚本
```bash
# 按顺序执行迁移
python -m migrations.add_scenario_meta_fields
python -m migrations.add_scenario_is_default_field
python -m migrations.add_user_scenario_config_table
python -m migrations.migrate_string_ids_to_integer
python -m migrations.add_phase3_evolution_tables
```

## 5. 定时任务

### 5.1 自动启动
定时任务在 `main.py` 启动时自动初始化：
- 用户偏好学习：每小时执行一次
- 动态获取 `agent_service`，避免启动依赖问题

### 5.2 手动触发
```bash
curl -X POST 'http://localhost:8000/api/v1/platform/cron/batch-learn-preferences?min_feedback_count=5' \
  -H 'Authorization: Bearer <token>'
```

## 6. 监控与日志

### 6.1 日志位置
- **后端日志**: `logs/backend.log`
- **前端日志**: `logs/frontend.log`

### 6.2 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

### 6.3 关键指标
- 会话数、消息数、费用统计：`GET /api/v1/sessions/stats`
- 用户行为统计：`user_behavior_stats` 表
- 偏好学习状态：`user_preferences_cache` 表

## 7. 备份与恢复

### 7.1 数据备份
```bash
# 备份数据库
cp data/sessions.db data/sessions.db.backup

# 备份工作目录
tar -czf work_dir_backup.tar.gz work_dir/
```

### 7.2 数据恢复
```bash
# 恢复数据库
cp data/sessions.db.backup data/sessions.db

# 恢复工作目录
tar -xzf work_dir_backup.tar.gz
```

## 8. 故障排查

### 8.1 常见问题

**问题1：API 调用失败**
- 检查 `ANTHROPIC_API_KEY` 是否正确
- 检查网络连接（能否访问 Anthropic API）

**问题2：数据库锁定**
- SQLite 并发写入限制，建议生产环境使用 PostgreSQL

**问题3：定时任务未执行**
- 检查 `main.py` 中 `cron_jobs.start()` 是否调用
- 查看日志确认任务启动

**问题4：偏好学习失败**
- 检查 `agent_service` 是否可用
- 确认用户有足够反馈数据（≥5 条）

### 8.2 日志分析
```bash
# 查看后端日志
tail -f logs/backend.log

# 搜索错误
grep ERROR logs/backend.log

# 查看场景匹配日志
grep "ScenarioMatcher" logs/backend.log
```

## 9. 性能优化

### 9.1 数据库优化
- 添加必要索引（场景、用户、会话相关字段）
- 定期清理过期会话数据
- 考虑迁移到 PostgreSQL（高并发场景）

### 9.2 缓存策略
- 场景匹配结果缓存（ScenarioMatcher 内部）
- 用户偏好缓存（`user_preferences_cache` 表）
- 数据摘要 hash 判断是否需要重新分析

### 9.3 异步处理
- 偏好学习在 CronJob 中异步执行
- 文件上传使用 MinIO 异步上传
- 工具调用结果异步保存

## 10. 安全建议

### 10.1 API 密钥
- 使用环境变量，不要硬编码
- 定期轮换 API 密钥
- 使用 Docker secrets 或密钥管理服务

### 10.2 权限控制
- 所有管理接口需要管理员身份
- 技能通过 `is_public`、`created_by` 控制可见性
- JWT Token 过期时间合理设置

### 10.3 数据安全
- 定期备份数据库
- 敏感数据加密存储
- 日志中不输出敏感信息

## 11. 版本升级

### 11.1 升级步骤
```bash
# 1. 备份数据
cp data/sessions.db data/sessions.db.backup

# 2. 拉取新代码
git pull origin dev

# 3. 执行迁移脚本
cd backend
python -m migrations.<new_migration>

# 4. 重启服务
docker-compose restart
```

### 11.2 回滚步骤
```bash
# 1. 恢复代码
git checkout <previous_tag>

# 2. 恢复数据库
cp data/sessions.db.backup data/sessions.db

# 3. 重启服务
docker-compose restart
```
