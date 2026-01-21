/**
 * 工具选择器组件
 *
 * 用于场景配置中选择可用工具
 * 支持按分类筛选、搜索、多选等功能
 */
import React, { useState, useEffect } from 'react';
import { Check, ChevronDown, Search, Wrench, Database, Cpu } from 'lucide-react';
import { apiClient } from '../services/api';

interface Tool {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  category: string;  // standard, custom
  tool_type: string;  // builtin, mcp
  mcp_server: string | null;
  is_enabled: boolean;
  is_public: boolean;
}

interface ToolSelectorProps {
  selectedTools: string[];
  onChange: (tools: string[]) => void;
  category?: 'all' | 'standard' | 'custom';
  multiSelect?: boolean;
  className?: string;
}

export const ToolSelector: React.FC<ToolSelectorProps> = ({
  selectedTools,
  onChange,
  category = 'all',
  multiSelect = true,
  className = ''
}) => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState<'all' | 'standard' | 'custom'>(category);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['standard', 'custom']));

  // 加载工具列表
  useEffect(() => {
    loadTools();
  }, [filterCategory]);

  const loadTools = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterCategory !== 'all') {
        params.append('category', filterCategory);
      }

      const queryString = params.toString();
      const endpoint = `/api/v1/platform/tools${queryString ? `?${queryString}` : ''}`;

      const response = await apiClient.get<Tool[]>(endpoint);
      if (response.error) {
        throw new Error(response.error);
      }

      setTools(response.data || []);
    } catch (err) {
      console.error('加载工具失败:', err);
    } finally {
      setLoading(false);
    }
  };

  // 切换分组展开/收起
  const toggleGroup = (group: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(group)) {
      newExpanded.delete(group);
    } else {
      newExpanded.add(group);
    }
    setExpandedGroups(newExpanded);
  };

  // 选择/取消选择工具
  const toggleTool = (toolName: string) => {
    if (multiSelect) {
      if (selectedTools.includes(toolName)) {
        onChange(selectedTools.filter(t => t !== toolName));
      } else {
        onChange([...selectedTools, toolName]);
      }
    } else {
      // 单选模式
      onChange(selectedTools.includes(toolName) ? [] : [toolName]);
    }
  };

  // 按分类分组工具
  const groupedTools = tools.reduce((acc, tool) => {
    if (!acc[tool.category]) {
      acc[tool.category] = [];
    }
    acc[tool.category].push(tool);
    return acc;
  }, {} as Record<string, Tool[]>);

  // 过滤工具
  const filterTools = (toolList: Tool[]) => {
    if (!searchTerm) return toolList;
    const term = searchTerm.toLowerCase();
    return toolList.filter(tool =>
      tool.name.toLowerCase().includes(term) ||
      tool.display_name.toLowerCase().includes(term) ||
      (tool.description && tool.description.toLowerCase().includes(term))
    );
  };

  // 获取分类图标和名称
  const getCategoryInfo = (category: string) => {
    switch (category) {
      case 'standard':
        return {
          name: '标准工具',
          icon: <Wrench size={18} />,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50'
        };
      case 'custom':
        return {
          name: '自定义工具',
          icon: <Cpu size={18} />,
          color: 'text-purple-600',
          bgColor: 'bg-purple-50'
        };
      default:
        return {
          name: category,
          icon: <Database size={18} />,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50'
        };
    }
  };

  // 获取工具类型图标
  const getToolTypeIcon = (tool: Tool) => {
    if (tool.tool_type === 'mcp') {
      return <span className="text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded">MCP</span>;
    }
    return <span className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">内置</span>;
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2" />
        <span className="text-gray-600">加载工具中...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 搜索和筛选 */}
      <div className="flex gap-4">
        {/* 搜索框 */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <input
            type="text"
            placeholder="搜索工具名称或描述..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* 分类筛选 */}
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value as 'all' | 'standard' | 'custom')}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">全部工具</option>
          <option value="standard">标准工具</option>
          <option value="custom">自定义工具</option>
        </select>
      </div>

      {/* 已选择工具统计 */}
      {selectedTools.length > 0 && (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-600">已选择</span>
          <span className="font-semibold text-blue-600">{selectedTools.length}</span>
          <span className="text-gray-600">个工具</span>
          <button
            onClick={() => onChange([])}
            className="ml-auto text-red-600 hover:text-red-700 text-sm"
          >
            清空选择
          </button>
        </div>
      )}

      {/* 工具列表 */}
      <div className="space-y-3">
        {Object.entries(groupedTools).map(([category, categoryTools]) => {
          const categoryInfo = getCategoryInfo(category);
          const filteredTools = filterTools(categoryTools);
          const isExpanded = expandedGroups.has(category);

          if (filteredTools.length === 0) return null;

          return (
            <div key={category} className="border border-gray-200 rounded-lg overflow-hidden">
              {/* 分类标题 */}
              <button
                onClick={() => toggleGroup(category)}
                className={`w-full flex items-center justify-between px-4 py-3 ${categoryInfo.bgColor} hover:opacity-90 transition-opacity`}
              >
                <div className="flex items-center gap-2">
                  {categoryInfo.icon}
                  <span className={`font-semibold ${categoryInfo.color}`}>
                    {categoryInfo.name}
                  </span>
                  <span className="text-sm text-gray-500">
                    ({filteredTools.length} 个)
                  </span>
                </div>
                <ChevronDown
                  size={20}
                  className={`transition-transform ${isExpanded ? '' : '-rotate-90'}`}
                />
              </button>

              {/* 工具列表 */}
              {isExpanded && (
                <div className="p-2 space-y-1 bg-white">
                  {filteredTools.map((tool) => {
                    const isSelected = selectedTools.includes(tool.name);

                    return (
                      <div
                        key={tool.id}
                        onClick={() => toggleTool(tool.name)}
                        className={`
                          flex items-center justify-between p-3 rounded-lg cursor-pointer
                          transition-colors border
                          ${isSelected
                            ? 'bg-blue-50 border-blue-200 hover:bg-blue-100'
                            : 'bg-white border-gray-200 hover:bg-gray-50'
                          }
                        `}
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          {/* 选中标记 */}
                          <div className={`
                            flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center
                            ${isSelected
                              ? 'bg-blue-600 border-blue-600'
                              : 'border-gray-300'
                            }
                          `}>
                            {isSelected && <Check size={14} className="text-white" />}
                          </div>

                          {/* 工具信息 */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                                {tool.display_name}
                              </span>
                              {getToolTypeIcon(tool)}
                            </div>
                            <div className={`text-xs mt-1 ${isSelected ? 'text-blue-700' : 'text-gray-500'}`}>
                              {tool.name}
                            </div>
                            {tool.description && (
                              <div className={`text-xs mt-1 truncate ${isSelected ? 'text-blue-600' : 'text-gray-400'}`}>
                                {tool.description}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}

        {Object.keys(groupedTools).length === 0 && (
          <div className="text-center py-8 text-gray-500">
            暂无工具
          </div>
        )}

        {searchTerm && Object.values(groupedTools).every(tools => filterTools(tools).length === 0) && (
          <div className="text-center py-8 text-gray-500">
            未找到匹配的工具
          </div>
        )}
      </div>
    </div>
  );
};
