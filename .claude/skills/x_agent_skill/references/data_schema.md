# XAgent 数据模式参考

本文档描述了XAgent技能支持的标准数据模式和格式要求。

## 概述

XAgent支持多种数据格式和模式，包括结构化数据、半结构化数据和非结构化数据的处理。为了获得最佳分析效果，建议按照以下模式准备数据。

## 支持的数据格式

### 1. CSV格式 (推荐)

**文件扩展名**: `.csv`

**编码**: UTF-8

**分隔符**: 逗号 (,)

```csv
date,product,category,region,sales,quantity,price,customer_id
2024-01-01,Product A,Electronics,North,1000.00,5,200.00,CUST001
2024-01-02,Product B,Clothing,South,800.00,8,100.00,CUST002
```

**特点**:
- 易于创建和编辑
- 支持大量数据处理
- 跨平台兼容性好

### 2. JSON格式

**文件扩展名**: `.json`

**编码**: UTF-8

**结构**: 数组格式或记录格式

```json
{
  "records": [
    {
      "date": "2024-01-01",
      "product": "Product A",
      "category": "Electronics",
      "region": "North",
      "sales": 1000.00,
      "quantity": 5,
      "price": 200.00,
      "customer_id": "CUST001"
    },
    {
      "date": "2024-01-02",
      "product": "Product B",
      "category": "Clothing",
      "region": "South",
      "sales": 800.00,
      "quantity": 8,
      "price": 100.00,
      "customer_id": "CUST002"
    }
  ]
}
```

### 3. Excel格式

**文件扩展名**: `.xlsx`, `.xls`

**要求**:
- 第一个工作表作为数据源
- 第一行作为列标题
- 避免合并单元格

## 标准数据模式

### 1. 销售数据模式

**用途**: 销售业绩分析、趋势分析、预测

**必需字段**:
- `date` (日期): 交易日期 (YYYY-MM-DD格式)
- `sales` (数值): 销售金额
- `quantity` (数值): 销售数量

**推荐字段**:
- `product`: 产品名称
- `category`: 产品类别
- `region`: 销售区域
- `customer_id`: 客户ID
- `price`: 单价
- `discount`: 折扣金额

**示例**:
```csv
date,product,category,region,sales,quantity,customer_id
2024-01-01,iPhone 15,Electronics,North,999.00,1,CUST001
2024-01-01,MacBook Pro,Electronics,North,2499.00,1,CUST002
2024-01-02,T-Shirt,Clothing,South,29.99,2,CUST003
```

### 2. 客户数据模式

**用途**: 客户行为分析、流失预测、细分

**必需字段**:
- `customer_id` (文本): 唯一客户标识
- `registration_date` (日期): 注册日期

**推荐字段**:
- `age`: 年龄
- `gender`: 性别
- `location`: 地理位置
- `total_purchases`: 总购买次数
- `total_spend`: 总消费金额
- `last_purchase_date`: 最后购买日期
- `churn`: 是否流失 (1/0)

**示例**:
```csv
customer_id,registration_date,age,gender,location,total_purchases,total_spend,last_purchase_date,churn
CUST001,2023-01-15,35,Male,Beijing,12,3500.00,2024-01-10,0
CUST002,2023-02-20,28,Female,Shanghai,8,2100.00,2023-11-15,1
```

### 3. 网站流量数据模式

**用途**: 用户行为分析、转化率分析、网站优化

**必需字段**:
- `timestamp` (日期时间): 访问时间
- `page_url`: 页面URL
- `user_id` (可选): 用户ID

**推荐字段**:
- `session_id`: 会话ID
- `referrer`: 来源页面
- `device_type`: 设备类型
- `browser`: 浏览器
- `country`: 国家
- `city`: 城市
- `action`: 用户操作
- `duration`: 停留时间

**示例**:
```csv
timestamp,page_url,session_id,referrer,device_type,country,action
2024-01-01 10:30:00,/home,SES001,direct,desktop,China,view
2024-01-01 10:32:15,/products,SES001,/home,mobile,China,click
```

### 4. 财务数据模式

**用途**: 财务分析、预算分析、成本优化

**必需字段**:
- `date` (日期): 日期
- `account`: 账户名称
- `amount`: 金额

**推荐字段**:
- `category`: 费用类别
- `department`: 部门
- `description`: 描述
- `transaction_type`: 交易类型 (income/expense)
- `currency`: 货币

**示例**:
```csv
date,account,category,department,amount,transaction_type,currency
2024-01-01,销售收入,Sales,销售部,15000.00,income,CNY
2024-01-02,办公费用,Office,行政部,500.00,expense,CNY
```

## 数据质量要求

### 1. 完整性

- **缺失值比例**: 任意列的缺失值不应超过20%
- **必需字段**: 必须字段的缺失值不应超过5%
- **记录数量**: 建议至少50条记录以进行有意义分析

### 2. 一致性

- **日期格式**: 统一使用 YYYY-MM-DD 格式
- **数值格式**: 使用标准数字格式，避免千位分隔符
- **文本编码**: 统一使用 UTF-8 编码
- **命名规范**: 列名使用下划线分隔的小写格式

### 3. 准确性

- **数值范围**: 数值应在合理范围内
- **日期有效性**: 日期应为有效日期
- **ID唯一性**: 标识字段应保持唯一性
- **分类一致性**: 相同类别使用相同的表示方式

## 数据预处理建议

### 1. 数据清洗

```python
# 示例：基础数据清洗
import pandas as pd

def clean_data(df):
    # 删除重复记录
    df = df.drop_duplicates()

    # 处理缺失值
    df = df.dropna(subset=['required_column'])  # 删除必需字段的缺失值
    df['optional_column'].fillna(df['optional_column'].mean(), inplace=True)  # 填充可选字段

    # 标准化日期格式
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

    # 标准化文本字段
    df['text_column'] = df['text_column'].str.strip().str.lower()

    return df
```

### 2. 数据验证

```python
# 示例：数据质量检查
def validate_data(df, schema):
    issues = []

    # 检查必需字段
    for field in schema['required_fields']:
        if field not in df.columns:
            issues.append(f"缺少必需字段: {field}")

    # 检查数据类型
    for field, expected_type in schema['field_types'].items():
        if field in df.columns:
            if not df[field].dtype.name.startswith(expected_type):
                issues.append(f"字段 {field} 类型错误: 期望 {expected_type}, 实际 {df[field].dtype}")

    # 检查缺失值比例
    for field in df.columns:
        missing_ratio = df[field].isnull().sum() / len(df)
        if missing_ratio > 0.2:
            issues.append(f"字段 {field} 缺失值过高: {missing_ratio:.2%}")

    return issues
```

## 最佳实践

### 1. 数据收集

- 定期收集数据，保持时间连续性
- 建立数据收集标准和流程
- 确保数据源的一致性和可靠性

### 2. 数据存储

- 使用版本控制管理数据文件变更
- 建立数据备份机制
- 保留原始数据，处理后的数据单独存储

### 3. 数据安全

- 敏感数据进行匿名化处理
- 控制数据访问权限
- 遵守相关数据保护法规

### 4. 文档记录

- 记录数据来源和收集方式
- 说明数据字段含义和计算方法
- 保留数据变更历史

## 错误处理

### 常见数据错误

1. **格式错误**: 日期格式不统一、数值包含文本
2. **编码问题**: 中文乱码、特殊字符
3. **结构问题**: 列数不一致、缺少表头
4. **内容错误**: 明显不合理的数值、拼写错误

### 解决方案

1. **使用数据验证工具**: 在导入时验证数据格式
2. **建立数据字典**: 明确定义每个字段的格式和含义
3. **定期数据审核**: 定期检查数据质量问题
4. **用户培训**: 培训数据录入人员正确格式化数据

## 性能优化

### 大数据集处理

- 使用分块读取处理大型CSV文件
- 考虑使用数据库存储大量数据
- 实施数据采样进行初步分析

### 内存优化

- 选择合适的数据类型 (category, int32, float32)
- 及时删除不需要的数据列
- 使用高效的数据结构

---

**最后更新**: 2024-12-14
**版本**: 1.0.0
**维护者**: XAgent团队