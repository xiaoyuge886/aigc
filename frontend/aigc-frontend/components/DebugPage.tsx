import React, { useState } from 'react';
import { Bug, RefreshCw, Trash2, Download, Settings } from 'lucide-react';

interface DebugLog {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  details?: any;
}

export const DebugPage: React.FC = () => {
  const [logs, setLogs] = useState<DebugLog[]>([
    {
      id: '1',
      timestamp: new Date().toISOString(),
      level: 'info',
      message: '调试系统已启动',
    }
  ]);
  const [filter, setFilter] = useState<'all' | 'info' | 'warn' | 'error' | 'debug'>('all');

  const addLog = (level: DebugLog['level'], message: string) => {
    const newLog: DebugLog = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      level,
      message,
    };
    setLogs(prev => [newLog, ...prev]);
  };

  const clearLogs = () => {
    setLogs([]);
    addLog('info', '日志已清空');
  };

  const exportLogs = () => {
    const dataStr = JSON.stringify(logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `debug-logs-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
    addLog('info', '日志已导出');
  };

  const testAPI = async () => {
    try {
      addLog('info', '测试 API 连接...');
      const response = await fetch('/api/v1/health');
      if (response.ok) {
        addLog('info', 'API 连接正常');
      } else {
        addLog('warn', `API 返回状态码: ${response.status}`);
      }
    } catch (error) {
      addLog('error', `API 连接失败: ${error}`);
    }
  };

  const clearCache = () => {
    localStorage.clear();
    sessionStorage.clear();
    addLog('info', '浏览器缓存已清空');
  };

  const getLevelColor = (level: DebugLog['level']) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      case 'warn': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'info': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'debug': return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getLevelBadge = (level: DebugLog['level']) => {
    switch (level) {
      case 'error': return '错误';
      case 'warn': return '警告';
      case 'info': return '信息';
      case 'debug': return '调试';
    }
  };

  const filteredLogs = filter === 'all' ? logs : logs.filter(log => log.level === filter);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-2 rounded-lg">
                <Bug className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-gray-900">调试系统</h1>
                <p className="text-sm text-gray-500">系统诊断和调试工具</p>
              </div>
            </div>
            <div className="text-sm text-gray-500">
              共 {logs.length} 条日志
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Tools */}
          <div className="lg:col-span-1 space-y-6">
            {/* System Info */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Settings className="w-5 h-5 text-gray-600" />
                <h2 className="text-lg font-bold text-gray-900">系统信息</h2>
              </div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">浏览器</span>
                  <span className="text-gray-900 font-medium">{navigator.userAgent.split(' ').slice(-2)[0]}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">平台</span>
                  <span className="text-gray-900 font-medium">{navigator.platform}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">语言</span>
                  <span className="text-gray-900 font-medium">{navigator.language}</span>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">快捷操作</h2>
              <div className="space-y-3">
                <button
                  onClick={testAPI}
                  className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-3 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all font-medium"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>测试 API 连接</span>
                </button>

                <button
                  onClick={clearCache}
                  className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white px-4 py-3 rounded-lg hover:from-orange-600 hover:to-orange-700 transition-all font-medium"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>清空浏览器缓存</span>
                </button>

                <button
                  onClick={exportLogs}
                  className="w-full flex items-center justify-center space-x-2 bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-3 rounded-lg hover:from-green-600 hover:to-green-700 transition-all font-medium"
                >
                  <Download className="w-4 h-4" />
                  <span>导出调试日志</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel - Logs */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {/* Log Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold text-gray-900">调试日志</h2>
                  <button
                    onClick={clearLogs}
                    className="text-sm text-red-600 hover:text-red-700 font-medium flex items-center space-x-1"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>清空</span>
                  </button>
                </div>

                {/* Filter */}
                <div className="flex space-x-2">
                  {(['all', 'info', 'warn', 'error', 'debug'] as const).map((f) => (
                    <button
                      key={f}
                      onClick={() => setFilter(f)}
                      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                        filter === f
                          ? 'bg-gray-900 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {f === 'all' ? '全部' : getLevelBadge(f as DebugLog['level'])}
                    </button>
                  ))}
                </div>
              </div>

              {/* Log List */}
              <div className="p-6 max-h-[600px] overflow-y-auto">
                {filteredLogs.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <Bug className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>暂无日志</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {filteredLogs.map((log) => (
                      <div
                        key={log.id}
                        className={`p-3 rounded-lg border ${getLevelColor(log.level)}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="text-xs font-medium uppercase">
                                {getLevelBadge(log.level)}
                              </span>
                              <span className="text-xs text-gray-500">
                                {new Date(log.timestamp).toLocaleString('zh-CN')}
                              </span>
                            </div>
                            <p className="text-sm font-medium">{log.message}</p>
                            {log.details && (
                              <pre className="mt-2 text-xs overflow-x-auto">
                                {JSON.stringify(log.details, null, 2)}
                              </pre>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
