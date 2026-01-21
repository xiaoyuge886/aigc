# 日志系统使用说明

## 概述

已为前端应用添加完整的日志系统，包括请求日志、响应日志和性能监控。

## 日志功能

### 1. 自动日志记录

#### 服务层日志 (`services/geminiService.ts`)
- ✅ 请求参数日志
- ✅ API 调用计时
- ✅ 流式响应进度
- ✅ 错误和警告日志

#### 组件层日志 (`components/ChatInterface.tsx`)
- ✅ 用户发送消息日志
- ✅ 摄像头状态
- ✅ 附件信息
- ✅ 流式响应接收进度（每 20 个 chunk）
- ✅ 响应完成统计

### 2. 日志级别

```typescript
Logger.info()      // 信息日志（绿色）
Logger.warn()      // 警告日志（黄色）
Logger.error()     // 错误日志（红色）
Logger.request()   // 请求日志（蓝色）
Logger.response()  // 响应日志（绿色/红色）
Logger.stream()    // 流式日志（青色）
```

### 3. 性能监控

```typescript
PerformanceLogger.start('label');   // 开始计时
PerformanceLogger.end('label');     // 结束计时并输出耗时
```

### 4. 日志输出示例

```
[2025-12-27 17:55:32] [INFO] 💬 用户发送消息
  文本内容: 帮我分析一下这个数据
  摄像头状态: 关闭
  附件数量: 0
  历史消息数: 0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📤 Gemini API 请求
[2025-12-27 17:55:32] [INFO] 请求参数 {messageLength: 11, historyLength: 0, ...}
⏱️  开始计时: gemini-request
[2025-12-27 17:55:32] [REQ] POST gemini-3-flash-preview
🔄 正在调用 Gemini API...
⏱️  计时结束: gemini-request (123.45ms)
[2025-12-27 17:55:32] [RES] gemini-3-flash-preview (200)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 开始接收流式响应
  📦 Chunk #20 | 总长度: 450 字符
  📦 Chunk #40 | 总长度: 850 字符
✅ 流式响应完成 | 总共 56 chunks | 1234 字符
```

## 开发模式

日志仅在 **开发模式** 下输出（`import.meta.env.DEV === true`），生产环境自动禁用。

## 查看日志

打开浏览器控制台（F12 或右键 → 检查 → Console 标签），所有日志都会显示在那里。

## 日志配置

日志配置文件：`utils/logger.ts`

可以自定义：
- 日志级别
- 时间格式
- 颜色方案
- 输出频率
