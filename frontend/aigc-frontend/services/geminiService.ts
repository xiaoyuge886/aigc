
import { GenerateContentResponse, Part } from "@google/genai";
// import { GoogleGenAI } from "@google/genai"; // Mock 模式下暂不使用
import { Logger, PerformanceLogger } from "../utils/logger";

// Always use named parameter and direct process.env.API_KEY access
// const ai = new GoogleGenAI({ apiKey: process.env.API_KEY }); // Mock 模式下暂不使用

/**
 * 模拟 SSE (Server-Sent Events) 流式生成器
 */
async function* mockStreamResponse(message: string, hasMultimodal: boolean): AsyncGenerator<GenerateContentResponse> {
  Logger.info('🤖 启动 Mock 流式响应', { message, hasMultimodal });
  PerformanceLogger.start('mock-stream');

  const testData = [
    "# 智能分析报告\n\n",
    hasMultimodal ? "## 多模态数据感知\n\n已接收到您的多模态输入（视觉/文件/语音），系统正在跨维度解析信号...\n\n" : "## 指令接收\n\n收到您的查询：「" + message + "」。正在连接 X 边缘计算节点进行分析...\n\n",
    "---\n\n",
    "## 核心发现\n\n",
    "### 1. 信号采集状态\n\n",
    "- **视觉/文件链路**：" + (hasMultimodal ? "✅ 已连接" : "❌ 未开启") + "\n",
    "- **语义分析引擎**：🔄 运行中\n",
    "- **实时同步率**：100%\n",
    "- **数据完整性**：99.8%\n\n",
    "### 2. 关键指标分析\n\n",
    "基于当前数据集，系统识别出以下关键趋势：\n\n",
    "- 整体性能呈现 **上升趋势**，环比增长 +15.3%\n",
    "- 核心指标稳定在 **92分** 以上\n",
    "- 异常检测率降低至 **0.02%**\n\n",
    "### 3. 数据可视化\n\n",
    "以下图表展示了详细的数据分布情况：\n\n",
    "[CHART_START]{",
    "\"title\":{\"text\":\"核心指标趋势分析\",\"textStyle\":{\"color\":\"#1d1d1f\",\"fontSize\":16}},",
    "\"xAxis\":{\"type\":\"category\",\"data\":[\"1月\",\"2月\",\"3月\",\"4月\",\"5月\",\"6月\"]},",
    "\"yAxis\":{\"type\":\"value\",\"name\":\"指数\"},",
    "\"series\":[",
    "{\"name\":\"增长\",\"data\":[820,932,901,934,1290,1330],\"type\":\"bar\",\"itemStyle\":{\"color\":\"#007AFF\",\"borderRadius\":[4,4,0,0]}},",
    "{\"name\":\"基准\",\"data\":[700,750,800,820,900,950],\"type\":\"line\",\"smooth\":true,\"itemStyle\":{\"color\":\"#34C759\"},\"lineStyle\":{\"width\":3}}",
    "]}",
    "[CHART_END]\n\n",
    "## 深度洞察\n\n",
    "### 优化建议\n\n",
    "根据分析结果，我们建议：\n\n",
    "1. **优先级 P0**：立即优化配置参数\n",
    "2. **优先级 P1**：增强数据同步机制\n",
    "3. **优先级 P2**：升级视觉识别模型\n\n",
    "### 风险评估\n\n",
    "- 当前风险等级：🟢 **低风险**\n",
    "- 建议复查周期：**7 天**\n\n",
    "---\n\n",
    "## 结论\n\n",
    "X 系统已完成多维数据建模。所有分析结果已同步至工作区，您可以继续追问以获取更详细的信息。"
  ];

  let chunkCount = 0;
  for (const segment of testData) {
    const words = segment.split('');
    for (let i = 0; i < words.length; i += 3) {
      const chunk = words.slice(i, i + 3).join('');
      await new Promise(resolve => setTimeout(resolve, Math.random() * 20 + 5));
      chunkCount++;
      Logger.stream(chunk, chunkCount);
      yield {
        text: chunk,
        candidates: [{
          content: { parts: [{ text: chunk }] },
          index: 0,
          finishReason: 'STOP'
        }]
      } as any;
    }
    await new Promise(resolve => setTimeout(resolve, 150));
  }

  PerformanceLogger.end('mock-stream');
  Logger.info('✅ Mock 流式响应完成', { totalChunks: chunkCount });
}

export const streamGeminiResponse = async (
  message: string,
  history: { role: string; parts: Part[] }[],
  multimodalParts: Part[] = []
): Promise<AsyncGenerator<GenerateContentResponse>> => {

  Logger.group('📤 Gemini API 请求');
  Logger.info('请求参数', {
    messageLength: message.length,
    historyLength: history.length,
    multimodalPartsCount: multimodalParts.length,
    apiKeyConfigured: !!process.env.API_KEY
  });
  PerformanceLogger.start('gemini-request');

  const hasMultimodal = multimodalParts.length > 0;

  // 🔴 强制使用 Mock 模式（忽略 API Key）
  Logger.warn('🧪 强制 Mock 模式已启用');
  PerformanceLogger.end('gemini-request');
  Logger.groupEnd();
  return mockStreamResponse(message, hasMultimodal);

  // 以下是真实的 API 调用代码（已禁用）
  /*
  if (!process.env.API_KEY || process.env.API_KEY === '') {
    Logger.warn('⚠️  API Key 未配置，使用 Mock 模式');
    PerformanceLogger.end('gemini-request');
    Logger.groupEnd();
    return mockStreamResponse(message, hasMultimodal);
  }

  try {
    Logger.request('POST', 'gemini-3-flash-preview', {
      message: message.substring(0, 100) + (message.length > 100 ? '...' : ''),
      historyItems: history.length,
      multimodal: hasMultimodal
    });

    const chat = ai.chats.create({
      model: 'gemini-3-flash-preview',
      config: {
        temperature: 0.8,
        systemInstruction: "你是一个嵌入在高级仪表盘中的 AI 顾问，具备视觉、听觉和文档分析能力。请提供简洁、专业的 Markdown 格式回答。当用户提供视频帧、语音或文件时，请综合分析这些信息。如果涉及数据展示，请输出 [CHART_START]{ECharts JSON}[CHART_END] 格式。"
      },
      history: history
    });

    // 组合所有输入部分：文本 + 多模态（图片/文件/音频）
    const combinedParts: Part[] = [{ text: message || "分析当前输入的多模态数据。" }, ...multimodalParts];

    Logger.info('🔄 正在调用 Gemini API...');
    const stream = await chat.sendMessageStream({ message: combinedParts });

    PerformanceLogger.end('gemini-request');
    Logger.response('gemini-3-flash-preview', 200, '流式响应已建立');
    Logger.groupEnd();

    return stream;
  } catch (error) {
    Logger.error('❌ Gemini API 异常，切换至 Mock 模式', error);
    PerformanceLogger.end('gemini-request');
    Logger.groupEnd();
    return mockStreamResponse(message, hasMultimodal);
  }
  */
};
