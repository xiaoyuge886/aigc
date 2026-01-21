---
name: minio-uploader
description: 简化版MinIO文件上传工具，支持一键上传文件到MinIO对象存储并获取访问链接
allowed-tools: Read, Write, Bash, Glob
---

# MinIO 文件上传器 (MinIO Uploader)

专业的MinIO对象存储上传工具，帮助您快速将文件上传到MinIO并生成可访问的链接。

## 🎯 工作流程

当用户要求上传文件到 MinIO 时，请按照以下步骤执行：

### 步骤 1: 确认文件路径
- 使用 `ls` 或 `Read` 工具确认文件存在
- 获取文件的完整路径
- 检查文件大小和类型

### 步骤 2: 执行上传命令
使用以下 Python 命令上传文件：

```bash
python /Users/hehe/pycharm_projects/aigc/.claude/skills/minio_uploader/simple_minio_uploader.py <文件路径> [对象名称] [force_download] [存储桶]
```

**参数说明**：
- `<文件路径>`: 必需，要上传的文件完整路径
- `[对象名称]`: 可选，MinIO 中的存储路径（默认使用原文件名）
- `[force_download]`: 可选，是否强制下载（true/false，默认 false）
- `[存储桶]`: 可选，存储桶名称（默认：agentic）

### 步骤 3: 验证上传结果
- 检查命令输出中的"上传成功"消息
- 获取返回的公开访问链接
- 如需要，使用 list_files() 验证文件已上传

### 步骤 4: 返回结果给用户
- 提供公开访问链接
- 显示文件信息（大小、类型等）
- 说明如何使用链接

## 📋 使用场景

### 场景 1: 上传单个文件（最常见）
**用户请求**: "上传这个文件到 MinIO"
**AI 应该执行**:
```bash
# 1. 先确认文件存在
ls -lh <文件路径>

# 2. 执行上传
python /Users/hehe/pycharm_projects/aigc/.claude/skills/minio_uploader/simple_minio_uploader.py <文件路径>
```

### 场景 2: 上传到指定路径
**用户请求**: "上传报告到 reports/ 目录"
**AI 应该执行**:
```bash
python /Users/hehe/pycharm_projects/aigc/.claude/skills/minio_uploader/simple_minio_uploader.py <文件路径> reports/<文件名>
```

### 场景 3: 上传并生成下载链接
**用户请求**: "上传文件并提供下载链接"
**AI 应该执行**:
```bash
python /Users/hehe/pycharm_projects/aigc/.claude/skills/minio_uploader/simple_minio_uploader.py <文件路径> <对象名称> true
```

### 场景 4: 批量上传多个文件
**用户请求**: "上传所有 PDF 文件"
**AI 应该执行**:
```bash
# 1. 先找到所有 PDF 文件
ls <目录>/*.pdf

# 2. 逐个上传
for file in <目录>/*.pdf; do
    python /Users/hehe/pycharm_projects/aigc/.claude/skills/minio_uploader/simple_minio_uploader.py "$file"
done
```

## 🔧 配置说明

**环境变量配置**（推荐）：
- `MINIO_ENDPOINT`: MinIO 服务地址（默认：`http://localhost:9000`）
- `MINIO_ACCESS_KEY`: 访问密钥（默认：`minioadmin`）
- `MINIO_SECRET_KEY`: 密钥（默认：`minioadmin`）
- `MINIO_BUCKET_NAME`: 默认存储桶（默认：`agentic`）
- `MINIO_SECURE`: 是否使用 HTTPS（默认：`false`）
- `MINIO_REGION`: AWS 区域（默认：`us-east-1`）

**支持的文件类型**：
- 文档：PDF, DOC, DOCX, TXT, MD, HTML
- 表格：XLS, XLSX, CSV
- 图片：JPG, PNG, GIF, SVG
- 其他：ZIP, JSON, XML 等

## 💡 最佳实践

1. **总是先检查文件是否存在**再执行上传
2. **使用有意义的对象名称**，例如：`reports/2025-01-analysis.pdf`
3. **对于大文件**，提示用户上传可能需要一些时间
4. **返回链接时**，同时说明链接的用途（预览或下载）
5. **中文文件名会自动处理** URL 编码，无需担心

## ⚠️ 注意事项

- 确保 boto3 包已安装（`pip install boto3`）
- 文件路径必须是绝对路径或相对于当前目录的路径
- 默认生成的链接是**公开访问**的，任何人都可以访问
- 如果需要私有访问，请使用预签名 URL 功能

## 📤 返回给用户的格式

上传成功后，请按以下格式返回结果：

```
✅ 文件上传成功！

📄 文件信息：
- 文件名：[文件名]
- 文件大小：[大小]
- 文件类型：[类型]

🔗 公开访问链接：
[链接地址]

💡 提示：
- 点击链接可直接预览/下载
- 链接永久有效（除非删除文件）
```

---

**现在开始使用吧！请告诉我您要上传哪个文件。**
