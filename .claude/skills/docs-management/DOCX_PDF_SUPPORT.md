# DOCX 和 PDF 文件解析支持

## 概述

docs-management skill 现在支持解析 `.docx` 和 `.pdf` 文件，提取文本内容用于索引和搜索。

## 实现

### 1. 文件解析器

**文件**: `scripts/utils/file_parser.py`

提供了统一的文件解析接口：
- `extract_text_from_file(file_path)`: 从各种文件格式提取文本
- `get_file_metadata(file_path)`: 获取文件元数据

### 2. 支持的文件格式

- ✅ **.docx**: Microsoft Word 文档
  - 使用 `python-docx` 库
  - 提取段落和表格内容
  
- ✅ **.pdf**: PDF 文档
  - 优先使用 `pdfplumber`（更好的质量）
  - 降级到 `PyPDF2`（如果 pdfplumber 不可用）
  
- ✅ **.txt**: 纯文本文件
- ✅ **.md**: Markdown 文件

### 3. 依赖安装

#### docs-management skill 依赖

```bash
cd .claude/skills/docs-management
pip install -r requirements.txt
```

新增依赖：
- `python-docx>=1.1.0`
- `pdfplumber>=0.10.0` (推荐)
- `PyPDF2>=3.0.0` (备选)

#### 后端依赖

```bash
cd backend
pip install -r requirements.txt
```

新增依赖：
- `python-docx>=1.1.0`
- `pdfplumber>=0.10.0`
- `PyPDF2>=3.0.0`

### 4. 使用示例

#### 在 docs-management 中使用

```python
from scripts.utils.file_parser import extract_text_from_file
from pathlib import Path

file_path = Path("canonical/user-uploads/2/document.docx")
text = extract_text_from_file(file_path)

if text:
    print(f"Extracted {len(text)} characters")
    print(text[:500])  # First 500 characters
```

#### 在 backend 中使用

`FileContentLoader` 类已自动支持 docx 和 pdf：

```python
from services.file_content_loader import FileContentLoader

loader = FileContentLoader(db_service)

# 加载 docx/pdf 文件内容
content = await loader.load_file_content(
    doc_id="user-upload-2-abc123",
    user_id=2
)

# 搜索 docx/pdf 文件内容
snippets = await loader.search_file_content(
    doc_id="user-upload-2-abc123",
    query="关键词",
    user_id=2
)
```

## 技术细节

### DOCX 解析

- 提取所有段落文本
- 提取表格内容（以 `|` 分隔）
- 保留段落之间的空行

### PDF 解析

- **pdfplumber** (推荐):
  - 更好的文本提取质量
  - 支持复杂布局
  - 可能需要系统依赖（poppler-utils）
  
- **PyPDF2** (备选):
  - 纯 Python 实现
  - 无需系统依赖
  - 质量略低于 pdfplumber

### 错误处理

- 如果解析库未安装，返回 `None` 并记录警告
- 如果解析失败，返回 `None` 并记录错误
- 降级策略：尝试多种方法，最后返回文件信息

## 集成点

### 1. FileContentLoader

`backend/services/file_content_loader.py` 已更新：
- `_extract_text_from_file()`: 新增方法，支持 docx/pdf
- `load_file_content()`: 自动使用文件解析器
- `get_file_summary()`: 支持 docx/pdf 文件摘要
- `search_file_content()`: 支持在 docx/pdf 中搜索

### 2. 文件类型检测

自动检测文件类型：
- 通过文件扩展名 (`.docx`, `.pdf`)
- 通过 MIME 类型
- 支持降级到文本读取

## 测试

### 测试文件解析器

```bash
cd .claude/skills/docs-management
python scripts/utils/file_parser.py path/to/file.docx
python scripts/utils/file_parser.py path/to/file.pdf --metadata
```

### 测试后端集成

上传 docx 或 pdf 文件，然后：
1. 使用 `@文件名` 提及文件
2. 查询文件内容
3. 搜索文件中的关键词

## 注意事项

1. **系统依赖**:
   - `pdfplumber` 在 Linux 上可能需要 `poppler-utils`
   - 安装: `sudo apt-get install poppler-utils` (Ubuntu/Debian)

2. **性能**:
   - PDF 解析可能较慢（特别是大文件）
   - 建议使用文件摘要而不是完整内容

3. **质量**:
   - 复杂 PDF 布局可能提取不完整
   - 图片和表格可能丢失格式信息

4. **编码**:
   - DOCX 文件自动处理编码
   - PDF 文本提取可能包含特殊字符

## 未来改进

- [ ] 支持更多文件格式（.xlsx, .pptx 等）
- [ ] 提取图片和表格的元数据
- [ ] 支持 OCR（图片中的文本）
- [ ] 改进 PDF 布局解析
- [ ] 缓存解析结果以提高性能
