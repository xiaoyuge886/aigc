import React, {
  useState,
  useMemo
} from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Loader2, Share2 } from 'lucide-react';
import { ChartBlock } from '../charts/ChartComponents';
import { MarkmapContainer } from '../mindmap/MarkmapContainer';

// --- 精确版 Markdown 渲染（支持内联图表）---
export const MarkdownRenderer: React.FC<{ content: string; isStreaming?: boolean }> = ({ content, isStreaming }) => {
  return (
    <div className="markdown-content animate-apple-fade max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // 自定义代码块渲染
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';

            if (!inline) {
              // 块级代码块：直接返回 div，p 组件会检测到并转换为 div
              return (
                <div className="my-4" data-code-block="true">
                  <pre className="bg-[#F5F5F7] rounded-xl p-4 overflow-x-auto border border-gray-200">
                    <code className={`text-sm text-gray-800 font-mono whitespace-pre-wrap ${className || ''}`} {...props}>
                      {children}
                    </code>
                  </pre>
                </div>
              );
            }

            // 内联代码
            return (
              <code className="bg-[#F5F5F7] px-1.5 py-0.5 rounded-md text-sm text-gray-800 font-mono border border-gray-200" {...props}>
                {children}
              </code>
            );
          },
          // 自定义标题渲染
          h1({ children }) {
            return <h1 className="text-[28px] font-black text-apple-gray mt-10 mb-6 tracking-tighter">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-[20px] font-bold text-apple-gray mt-8 mb-4 tracking-tight">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-[16px] font-bold text-apple-gray mt-6 mb-3 tracking-tight">{children}</h3>;
          },
          h4({ children }) {
            return <h4 className="text-[14px] font-bold text-apple-gray mt-5 mb-2 tracking-tight">{children}</h4>;
          },
          // 自定义段落渲染：如果包含块级元素，使用 div 替代 p
          p({ node, children, ...props }: any) {
            // 🔥 递归检查 AST 节点是否包含块级代码
            const hasBlockCodeInAST = (astNode: any, depth: number = 0): boolean => {
              if (depth > 20 || !astNode) return false;

              // 检查 element 节点 - ReactMarkdown 的 AST 中 code 节点的 type 是 'element'
              if (astNode.type === 'element') {
                // 检查是否是 code 节点
                if (astNode.tagName === 'code') {
                  console.log('[DEBUG] ✅ Found CODE element!');
                  return true;  // 找到 code 节点，返回 true
                }

                // 检查其他已知的块级元素
                if (['div', 'pre', 'ul', 'ol', 'blockquote', 'table', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(astNode.tagName)) {
                  return true;
                }

                // 递归检查子节点
                if (astNode.children && Array.isArray(astNode.children)) {
                  return astNode.children.some((child: any) => hasBlockCodeInAST(child, depth + 1));
                }
              }

              // 其他节点类型，检查 children
              if (astNode.children && Array.isArray(astNode.children)) {
                return astNode.children.some((child: any) => hasBlockCodeInAST(child, depth + 1));
              }

              return false;
            };

            const hasBlockElements = hasBlockCodeInAST(node);
            console.log('[DEBUG] hasBlockElements:', hasBlockElements);

            // 如果包含块级元素，使用 div 替代 p
            if (hasBlockElements) {
              return <div className="text-[15px] leading-relaxed text-[#424245] my-3 font-medium" {...props}>{children}</div>;
            }
            return <p className="text-[15px] leading-relaxed text-[#424245] my-3 font-medium" {...props}>{children}</p>;
          },
          // 自定义列表渲染
          ul({ children }) {
            return <ul className="space-y-2 my-3 pl-1">{children}</ul>;
          },
          li({ children }) {
            return (
              <li className="flex items-start space-x-3 group">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500/80 mt-2.5 flex-shrink-0 group-hover:scale-125 transition-transform" />
                <span className="text-[15px] font-medium text-[#424245] leading-relaxed">{children}</span>
              </li>
            );
          },
          ol({ children }) {
            return <ol className="space-y-2 my-3 pl-4 list-decimal">{children}</ol>;
          },
          // 自定义链接渲染
          a({ children, href }) {
            return (
              <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                {children}
              </a>
            );
          },
          // 自定义引用渲染
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-blue-200 pl-4 py-2 my-4 bg-blue-50/50 italic text-gray-700">
                {children}
              </blockquote>
            );
          },
          // 自定义表格渲染
          table({ children }) {
            return (
              <div className="my-6 overflow-x-auto -mx-2 px-2">
                <table className="min-w-full border-collapse border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-gray-50 border-b-2 border-gray-300">{children}</thead>;
          },
          tbody({ children }) {
            return <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>;
          },
          tr({ children }) {
            return <tr className="hover:bg-gray-50 transition-colors">{children}</tr>;
          },
          th({ children }) {
            return (
              <th className="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider border-b border-gray-300">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-4 py-3 text-sm text-gray-800 border-b border-gray-100">
                {children}
              </td>
            );
          },
          // 自定义强调渲染
          strong({ children }) {
            return <strong className="font-bold text-[#1D1D1F]">{children}</strong>;
          },
          em({ children }) {
            return <em className="italic text-gray-600">{children}</em>;
          },
          // 自定义水平线渲染
          hr() {
            return <hr className="my-6 border-t border-gray-200" />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
      {isStreaming && <span className="inline-block w-1.5 h-4 ml-1.5 bg-blue-600 animate-pulse align-middle rounded-full shadow-[0_0_8px_rgba(37,99,235,0.5)]" />}
    </div>
  );
};


// --- 带内联图表的 Markdown 渲染器 ---
export const MarkdownRendererWithCharts: React.FC<{ content: string; isStreaming?: boolean }> = ({ content, isStreaming }) => {
  // 检测是否为 ECharts 配置对象
  const isEChartsConfig = (obj: any): boolean => {
    if (!obj || typeof obj !== 'object') return false;
    // 检测常见的 ECharts 配置键
    const chartKeys = ['xAxis', 'yAxis', 'series', 'dataset', 'angleAxis', 'radiusAxis', 'parallel', 'radar', 'visualMap'];
    return chartKeys.some(key => key in obj);
  };

  // 尝试从代码块中提取并解析图表配置
  const tryParseChartFromCodeBlock = (code: string): any | null => {
    // 清理代码块标记和变量声明
    let cleanCode = code
      .replace(/```(json|javascript|js)/gi, '')
      .replace(/```/g, '')
      .trim();

    // 清理变量声明（如 "var option = "）
    cleanCode = cleanCode.replace(/(?:var|let|const)\s+\w+\s*=\s*/, '');

    try {
      // 尝试 JSON 解析
      const parsed = JSON.parse(cleanCode);
      if (isEChartsConfig(parsed)) return parsed;
    } catch (e) {
      // JSON 解析失败，尝试 JavaScript 解析
      try {
        const parsed = new Function(`return (${cleanCode})`)();
        if (isEChartsConfig(parsed)) return parsed;
      } catch (e2) {
        // 解析失败，返回 null
      }
    }
    return null;
  };

  const parseContentWithCharts = (text: string) => {
    if (!text || text.trim() === '') {
      // 如果文本为空，返回一个空文本块
      return [{ type: 'text' as const, content: '' }];
    }

    console.log('[Chart Parser] Content length:', text.length);
    console.log('[Chart Parser] Contains [CHART_START]:', text.includes('[CHART_START]'));
    console.log('[Chart Parser] Contains [CHART_END]:', text.includes('[CHART_END]'));

    const chartStartTag = '[CHART_START]';
    const chartEndTag = '[CHART_END]';
    const blocks: Array<{ type: 'text' | 'chart'; content: string; chartOption?: any }> = [];
    let currentIndex = 0;

    while (currentIndex < text.length) {
      const startIndex = text.indexOf(chartStartTag, currentIndex);

      if (startIndex === -1) {
        // 没有显式图表标记，检查剩余文本中的代码块
        const remainingText = text.substring(currentIndex);
        
        // 如果没有剩余文本，跳出循环
        if (!remainingText || remainingText.trim() === '') {
          break;
        }
        
        // 使用更精确的代码块正则，确保匹配完整的代码块（包含换行符）
        const codeBlockRegex = /```(?:json|javascript|js)?\n([\s\S]*?)```/g;
        let lastIndex = 0;
        let match;
        
        // 重置正则的 lastIndex
        codeBlockRegex.lastIndex = 0;

        while ((match = codeBlockRegex.exec(remainingText)) !== null) {
          // 添加代码块前的文本
          if (match.index > lastIndex) {
            const beforeText = remainingText.substring(lastIndex, match.index);
            if (beforeText.trim()) {
              blocks.push({ type: 'text', content: beforeText });
            }
          }

          // 尝试解析为图表
          const chartOption = tryParseChartFromCodeBlock(match[1]);
          if (chartOption) {
            blocks.push({ type: 'chart', content: '', chartOption });
          } else {
            // 不是图表，保留为代码块（包含代码块标记）
            blocks.push({ type: 'text', content: match[0] });
          }

          lastIndex = match.index + match[0].length;
        }

        // 添加剩余文本
        if (lastIndex < remainingText.length) {
          const finalText = remainingText.substring(lastIndex);
          if (finalText.trim()) {
            blocks.push({ type: 'text', content: finalText });
          }
        } else if (lastIndex === 0) {
          // 如果没有匹配到任何代码块，整个文本作为一个文本块
          blocks.push({ type: 'text', content: remainingText });
        }

        break;
      }

      // 添加图表前的文本
      if (startIndex > currentIndex) {
        blocks.push({ type: 'text', content: text.substring(currentIndex, startIndex) });
      }

      const endIndex = text.indexOf(chartEndTag, startIndex + chartStartTag.length);

      if (endIndex === -1) {
        // 只有开始标签，图表数据未传输完成
        blocks.push({ type: 'text', content: text.substring(startIndex) });
        break;
      }

      // 提取图表 JSON 数据（显式标记）
      let rawJson = text.substring(startIndex + chartStartTag.length, endIndex);

      // 清理代码块标记
      let cleanJson = rawJson
        .replace(/```(json|javascript|js)/gi, '')
        .replace(/```/g, '')
        .trim();

      // 清理变量声明（如 "var option = " 或 "const option = "）
      cleanJson = cleanJson.replace(/(?:var|let|const)\s+\w+\s*=\s*/, '');

      try {
        // 尝试直接解析 JSON
        let chartOption = JSON.parse(cleanJson);
        blocks.push({ type: 'chart', content: '', chartOption });
      } catch (e) {
        // JSON 解析失败，尝试解析 JavaScript 对象字面量（更宽松）
        try {
          const chartOption = new Function(`return (${cleanJson})`)();
          blocks.push({ type: 'chart', content: '', chartOption });
        } catch (e2) {
          
          blocks.push({ type: 'text', content: text.substring(startIndex, endIndex + chartEndTag.length) });
        }
      }

      currentIndex = endIndex + chartEndTag.length;
    }

    // 确保至少返回一个文本块
    if (blocks.length === 0) {
      return [{ type: 'text' as const, content: text }];
    }

    return blocks;
  };

  const blocks = parseContentWithCharts(content);

  console.log('[Chart Parser] Total blocks parsed:', blocks.length);
  console.log('[Chart Parser] Block types:', blocks.map(b => b.type));
  console.log('[Chart Parser] Chart blocks:', blocks.filter(b => b.type === 'chart').length);

  // 如果没有 blocks，直接渲染原始内容
  if (!blocks || blocks.length === 0) {
    console.log('[Chart Parser] No blocks found, rendering raw content');
    return (
      <div className="markdown-content animate-apple-fade max-w-none space-y-6">
        <MarkdownRenderer content={content} isStreaming={isStreaming} />
        {isStreaming && <span className="inline-block w-1.5 h-4 ml-1.5 bg-blue-600 animate-pulse align-middle rounded-full shadow-[0_0_8px_rgba(37,99,235,0.5)]" />}
      </div>
    );
  }

  return (
    <div className="markdown-content animate-apple-fade max-w-none space-y-6">
      {blocks.map((block, idx) => {
        console.log(`[Chart Renderer] Block ${idx}: type=${block.type}, hasChartOption=${!!block.chartOption}`);
        if (block.type === 'chart') {
          console.log(`[Chart Renderer] Rendering chart block ${idx} with option:`, block.chartOption);
          return <ChartBlock key={idx} chartOption={block.chartOption} blockIdx={idx} />;
        } else {
          // 渲染文本块，处理代码块
          const textContent = block.content;
          
          // 如果没有内容，直接返回
          if (!textContent || textContent.trim() === '') {
            return null;
          }

          // 使用更精确的代码块正则，确保不会误匹配表格等内容
          // 匹配 ```language\n...``` 格式的代码块（必须包含换行符）
          const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
          const parts: Array<{ type: 'text' | 'code'; content: string; language?: string }> = [];
          let lastIndex = 0;
          let match;

          // 重置正则的 lastIndex，确保每次都能正确匹配
          codeBlockRegex.lastIndex = 0;
          
          while ((match = codeBlockRegex.exec(textContent)) !== null) {
            // 添加代码块前的文本
            if (match.index > lastIndex) {
              const beforeText = textContent.substring(lastIndex, match.index);
              if (beforeText.trim()) {
                parts.push({ type: 'text', content: beforeText });
              }
            }
            // 添加代码块
            parts.push({ type: 'code', content: match[2], language: match[1] });
            lastIndex = match.index + match[0].length;
          }

          // 添加剩余文本
          if (lastIndex < textContent.length) {
            const remainingText = textContent.substring(lastIndex);
            if (remainingText.trim()) {
              parts.push({ type: 'text', content: remainingText });
            }
          }

          // 如果没有提取到任何部分，说明整个内容都是普通文本（没有代码块），直接渲染
          // 注意：这里传递 isStreaming={false}，避免内部添加光标，只在最外层添加一个光标
          if (parts.length === 0) {
            return (
              <div key={idx} className="w-full">
                <MarkdownRenderer content={textContent} isStreaming={false} />
              </div>
            );
          }

          return (
            <div key={idx} className="w-full">
              {parts.map((part, partIdx) => {
                if (part.type === 'code') {
                  return (
                    <div key={partIdx} className="my-4">
                      <pre className="bg-[#F5F5F7] rounded-xl p-4 overflow-x-auto border border-gray-200">
                        <code className="text-sm text-gray-800 font-mono whitespace-pre-wrap">
                          {part.content}
                        </code>
                      </pre>
                    </div>
                  );
                } else {
                  // 确保文本内容不为空才渲染
                  // 注意：这里传递 isStreaming={false}，避免内部添加光标，只在最外层添加一个光标
                  if (part.content && part.content.trim()) {
                    return (
                      <div key={partIdx} className="w-full">
                        <MarkdownRenderer content={part.content} isStreaming={false} />
                      </div>
                    );
                  }
                  return null;
                }
              })}
            </div>
          );
        }
      })}
      {isStreaming && <span className="inline-block w-1.5 h-4 ml-1.5 bg-blue-600 animate-pulse align-middle rounded-full shadow-[0_0_8px_rgba(37,99,235,0.5)]" />}
    </div>
  );
};


// --- 格式化响应组件 ---
export const FormattedResponse: React.FC<{ text: string; isStreaming?: boolean }> = ({ text, isStreaming }) => {
  const [viewMode, setViewMode] = useState<'doc' | 'mindmap'>('doc');

  const hasIncompleteChart = useMemo(() => {
    return text.includes('[CHART_START]') && !text.includes('[CHART_END]');
  }, [text]);

  const cleanText = useMemo(() => {
    if (!hasIncompleteChart) return text;
    const startIndex = text.indexOf('[CHART_START]');
    return text.substring(0, startIndex).trim();
  }, [text, hasIncompleteChart]);

  const isMindmapEligible = !isStreaming && cleanText && !hasIncompleteChart && (cleanText.includes('#') || cleanText.split('\n').filter((l: string) => l.trim().startsWith('- ')).length > 2);

  return (
    <div className="w-full space-y-6">
      {/* 工具栏：移除 sticky 和悬浮效果，回归正常文档流 */}
      <div className="flex items-center justify-between pb-4 border-b border-black/[0.04] mb-6">
        <div className="flex bg-[#F2F2F7] p-1 rounded-xl">
           <button onClick={() => setViewMode('doc')} className={`px-4 py-1.5 text-[11px] font-bold rounded-lg transition-all ${viewMode === 'doc' ? 'bg-white shadow-sm text-black' : 'text-gray-400 hover:text-gray-600'}`}>分析报告</button>
           {isMindmapEligible && <button onClick={() => setViewMode('mindmap')} className={`px-4 py-1.5 text-[11px] font-bold rounded-lg transition-all ${viewMode === 'mindmap' ? 'bg-white shadow-sm text-black' : 'text-gray-400 hover:text-gray-600'}`}>深度全景</button>}
        </div>
        <div className="flex items-center space-x-2">
           <button className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-all"><Share2 size={16}/></button>
        </div>
      </div>

      {/* 单栏布局：内容与内联图表 */}
      <div className="w-full">
        <div className="min-h-[200px] animate-apple-fade">
          {hasIncompleteChart ? (
            <div className="space-y-6">
              <MarkdownRenderer content={cleanText} isStreaming={false} />
              <div className="p-10 rounded-[32px] border border-dashed border-blue-200 bg-blue-50/30 flex flex-col items-center justify-center space-y-6 animate-pulse h-[400px]">
                 <Loader2 className="animate-spin text-blue-500" size={32} />
                 <span className="text-[11px] font-black text-blue-500 uppercase tracking-[0.3em]">Processing Visuals...</span>
              </div>
            </div>
          ) : viewMode === 'doc' ? (
            <div className="px-1">
              <MarkdownRendererWithCharts content={text} isStreaming={isStreaming} />
            </div>
          ) : (
            <MarkmapContainer markdown={cleanText} height="600px" />
          )}
        </div>
      </div>
    </div>
  );
};

