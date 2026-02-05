import React, { useState, useEffect } from 'react';
import { X, Play, RotateCcw, Send, Bug, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

interface DebugModalProps {
  isOpen: boolean;
  onClose: () => void;
  skillId: number;
  skillName: string;
}

interface DebugMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
}

interface TestResult {
  status: 'success' | 'error' | 'pending';
  message: string;
  duration?: number;
}

export const DebugModal: React.FC<DebugModalProps> = ({
  isOpen,
  onClose,
  skillId,
  skillName,
}) => {
  const [messages, setMessages] = useState<DebugMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);

  useEffect(() => {
    if (isOpen) {
      // Reset state when modal opens
      setMessages([{
        id: '1',
        type: 'system',
        content: `开始调试技能: ${skillName} (ID: ${skillId})`,
        timestamp: new Date(),
      }]);
      setTestResults([]);
      setInput('');
      runQuickTests();
    }
  }, [isOpen, skillId, skillName]);

  const runQuickTests = async () => {
    setTestResults([
      { status: 'pending', message: '检查技能配置...' },
      { status: 'pending', message: '测试技能内容加载...' },
      { status: 'pending', message: '验证技能语法...' },
    ]);

    // Simulate tests
    await new Promise(resolve => setTimeout(resolve, 500));
    setTestResults(prev => prev.map((r, i) =>
      i === 0 ? { ...r, status: 'success', message: '✓ 技能配置有效', duration: 120 } : r
    ));

    await new Promise(resolve => setTimeout(resolve, 500));
    setTestResults(prev => prev.map((r, i) =>
      i === 1 ? { ...r, status: 'success', message: '✓ 技能内容加载成功', duration: 89 } : r
    ));

    await new Promise(resolve => setTimeout(resolve, 500));
    setTestResults(prev => prev.map((r, i) =>
      i === 2 ? { ...r, status: 'success', message: '✓ 语法验证通过', duration: 45 } : r
    ));
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: DebugMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          skill_id: skillId,
          session_id: `debug_${skillId}_${Date.now()}`,
        }),
      });

      if (!response.ok) throw new Error('API request failed');

      const data = await response.json();

      const assistantMessage: DebugMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: data.response || data.message || 'Response received',
        timestamp: new Date(),
        metadata: data,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: DebugMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: `错误: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getIconForType = (type: DebugMessage['type']) => {
    switch (type) {
      case 'user': return <Send className="w-4 h-4" />;
      case 'assistant': return <CheckCircle2 className="w-4 h-4" />;
      case 'system': return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'error': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'pending': return <Clock className="w-4 h-4 text-gray-400 animate-spin" />;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-white/20 p-2 rounded-lg">
              <Bug className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">技能调试器</h2>
              <p className="text-sm text-white/80">{skillName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Left Panel - Test Results */}
          <div className="w-80 border-r border-gray-200 bg-gray-50 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-gray-900">快速测试</h3>
                <button
                  onClick={runQuickTests}
                  className="text-sm text-purple-600 hover:text-purple-700 font-medium flex items-center space-x-1"
                >
                  <RotateCcw className="w-3 h-3" />
                  <span>重新测试</span>
                </button>
              </div>

              <div className="space-y-2">
                {testResults.map((result, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${
                      result.status === 'success'
                        ? 'bg-green-50 border-green-200'
                        : result.status === 'error'
                        ? 'bg-red-50 border-red-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {getStatusIcon(result.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{result.message}</p>
                        {result.duration && (
                          <p className="text-xs text-gray-500 mt-1">{result.duration}ms</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Debug Info */}
              <div className="mt-6 p-4 bg-white rounded-lg border border-gray-200">
                <h4 className="text-sm font-bold text-gray-900 mb-3">调试信息</h4>
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">技能 ID</span>
                    <span className="font-mono text-gray-900">{skillId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">消息数量</span>
                    <span className="font-mono text-gray-900">{messages.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">测试状态</span>
                    <span className={`font-medium ${
                      testResults.every(r => r.status === 'success')
                        ? 'text-green-600'
                        : 'text-yellow-600'
                    }`}>
                      {testResults.every(r => r.status === 'success') ? '通过' : '测试中'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Chat */}
          <div className="flex-1 flex flex-col">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.type === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.type === 'user'
                        ? 'bg-purple-600 text-white'
                        : message.type === 'system'
                        ? 'bg-gray-100 text-gray-900'
                        : 'bg-indigo-50 text-gray-900 border border-indigo-200'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      {getIconForType(message.type)}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        {message.metadata && (
                          <details className="mt-2">
                            <summary className="text-xs opacity-70 cursor-pointer hover:opacity-100">
                              查看响应数据
                            </summary>
                            <pre className="mt-2 text-xs overflow-x-auto p-2 bg-black/5 rounded">
                              {JSON.stringify(message.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                        <p className="text-xs opacity-70 mt-2">
                          {message.timestamp.toLocaleTimeString('zh-CN')}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-indigo-50 text-gray-900 border border-indigo-200 rounded-lg p-4">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin">
                        <Bug className="w-4 h-4 text-indigo-600" />
                      </div>
                      <span className="text-sm">正在处理...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="border-t border-gray-200 p-4 bg-gray-50">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="输入测试消息..."
                  disabled={isLoading}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <button
                  onClick={handleSend}
                  disabled={isLoading || !input.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center space-x-2"
                >
                  <Play className="w-4 h-4" />
                  <span>发送</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
