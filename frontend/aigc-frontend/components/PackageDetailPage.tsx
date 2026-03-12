/**
 * Capability Package Detail Page
 * 能力包详情页面 - 从后端加载真实文件
 */
import React, { useState, useEffect } from 'react';
import {
  ArrowLeft, File, Folder, FolderOpen, FileText,
  Settings, Users, Calendar, Crown,
  ChevronRight, ChevronDown, Copy, Check,
  Terminal, Globe, Layers, RefreshCw
} from 'lucide-react';
import { platformService, CapabilityPackage, PackageFile } from '../services/platformService';

interface PackageDetailPageProps {
  packageId: number;
  onBack: () => void;
}

// 前端文件节点类型（用于树形显示）
interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  content?: string;
  children?: FileNode[];
  isOpen?: boolean;
  path: string;
  size?: number;
}

export const PackageDetailPage: React.FC<PackageDetailPageProps> = ({ packageId, onBack }) => {
  const [pkg, setPkg] = useState<CapabilityPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 文件数据
  const [fileType, setFileType] = useState<'plugin' | 'database'>('database');
  const [files, setFiles] = useState<PackageFile[]>([]);
  const [fileTree, setFileTree] = useState<FileNode | null>(null);
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [copied, setCopied] = useState(false);
  const [loadingFiles, setLoadingFiles] = useState(false);

  // 加载能力包详情
  useEffect(() => {
    loadPackageDetail();
  }, [packageId]);

  const loadPackageDetail = async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行加载能力包信息和文件
      const [pkgData, filesData] = await Promise.all([
        platformService.getPackage(packageId),
        platformService.getPackageFiles(packageId)
      ]);

      setPkg(pkgData);
      setFileType(filesData.type);
      setFiles(filesData.files);

      // 构建文件树
      const tree = buildFileTree(pkgData.name, filesData.files);
      setFileTree(tree);

      // 默认选中 README.md 或第一个文件
      const readme = tree.children?.find(c => c.name === 'README.md');
      if (readme) {
        setSelectedFile(readme);
      } else if (tree.children && tree.children.length > 0) {
        const firstFile = findFirstFile(tree);
        if (firstFile) setSelectedFile(firstFile);
      }

    } catch (err: any) {
      console.error('Failed to load package:', err);
      setError(err.message || '加载能力包失败');
    } finally {
      setLoading(false);
    }
  };

  // 构建文件树
  const buildFileTree = (pkgName: string, files: PackageFile[]): FileNode => {
    return {
      id: 'root',
      name: pkgName,
      type: 'folder',
      path: '',
      isOpen: true,
      children: files.map(f => convertToFileNode(f))
    };
  };

  // 转换文件节点
  const convertToFileNode = (file: PackageFile): FileNode => ({
    id: file.path,
    name: file.name,
    type: file.type,
    path: file.path,
    content: file.content,
    size: file.size,
    isOpen: file.type === 'folder' ? true : undefined,
    children: file.children?.map(c => convertToFileNode(c))
  });

  // 找到第一个文件
  const findFirstFile = (node: FileNode): FileNode | null => {
    if (node.type === 'file') return node;
    if (node.children) {
      for (const child of node.children) {
        const found = findFirstFile(child);
        if (found) return found;
      }
    }
    return null;
  };

  // 切换文件夹
  const toggleFolder = (node: FileNode) => {
    if (node.type !== 'folder' || !fileTree) return;

    const updateNode = (n: FileNode): FileNode => {
      if (n.id === node.id) {
        return { ...n, isOpen: !n.isOpen };
      }
      if (n.children) {
        return { ...n, children: n.children.map(updateNode) };
      }
      return n;
    };

    setFileTree(updateNode(fileTree));
  };

  // 选择文件
  const selectFile = async (node: FileNode) => {
    if (node.type === 'file') {
      // 如果文件内容为空，尝试从后端加载
      if (!node.content && fileType === 'plugin') {
        setLoadingFiles(true);
        try {
          const filesData = await platformService.getPackageFiles(packageId, node.path);
          if (filesData.files.length > 0 && filesData.files[0].content) {
            node = { ...node, content: filesData.files[0].content };
            // 更新树中的节点
            if (fileTree) {
              const updateNode = (n: FileNode): FileNode => {
                if (n.id === node.id) return node;
                if (n.children) return { ...n, children: n.children.map(updateNode) };
                return n;
              };
              setFileTree(updateNode(fileTree));
            }
          }
        } catch (e) {
          console.error('Failed to load file content:', e);
        } finally {
          setLoadingFiles(false);
        }
      }
      setSelectedFile(node);
    }
  };

  // 复制内容
  const handleCopy = () => {
    if (selectedFile?.content) {
      navigator.clipboard.writeText(selectedFile.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // 刷新文件
  const handleRefresh = async () => {
    setLoadingFiles(true);
    try {
      const filesData = await platformService.getPackageFiles(packageId);
      setFiles(filesData.files);
      const tree = buildFileTree(pkg?.name || 'package', filesData.files);
      setFileTree(tree);
    } catch (e) {
      console.error('Failed to refresh:', e);
    } finally {
      setLoadingFiles(false);
    }
  };

  // 渲染文件树节点
  const renderTreeNode = (node: FileNode, depth: number = 0) => {
    const isSelected = selectedFile?.id === node.id;
    const isFolder = node.type === 'folder';
    const hasChildren = isFolder && node.children && node.children.length > 0;

    return (
      <div key={node.id}>
        <div
          onClick={() => isFolder ? toggleFolder(node) : selectFile(node)}
          className={`flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer transition-colors ${
            isSelected && !isFolder
              ? 'bg-slate-900 text-white'
              : 'text-slate-700 hover:bg-slate-100'
          }`}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
        >
          {/* 展开/折叠图标 */}
          {isFolder && hasChildren && (
            <span className="w-4 h-4 flex items-center justify-center">
              {node.isOpen ? (
                <ChevronDown size={14} className={isSelected && !isFolder ? 'text-white' : 'text-slate-400'} />
              ) : (
                <ChevronRight size={14} className={isSelected && !isFolder ? 'text-white' : 'text-slate-400'} />
              )}
            </span>
          )}
          {!isFolder && <span className="w-4" />}

          {/* 文件/文件夹图标 */}
          {isFolder ? (
            node.isOpen ? (
              <FolderOpen size={16} className="text-amber-500" />
            ) : (
              <Folder size={16} className="text-amber-500" />
            )
          ) : (
            <FileText size={16} className={isSelected && !isFolder ? 'text-white' : 'text-slate-400'} />
          )}

          {/* 文件名 */}
          <span className="text-[13px] font-medium truncate">{node.name}</span>

          {/* 文件大小 */}
          {node.size && (
            <span className="text-[10px] text-slate-400 ml-auto">
              {formatSize(node.size)}
            </span>
          )}
        </div>

        {/* 子节点 */}
        {isFolder && node.isOpen && hasChildren && (
          <div>
            {node.children!.map(child => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  // 格式化文件大小
  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  // 获取文件语言（用于语法高亮提示）
  const getFileLanguage = (filename: string): string => {
    if (filename.endsWith('.json')) return 'json';
    if (filename.endsWith('.md')) return 'markdown';
    if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'typescript';
    if (filename.endsWith('.js') || filename.endsWith('.jsx')) return 'javascript';
    if (filename.endsWith('.py')) return 'python';
    if (filename.endsWith('.yaml') || filename.endsWith('.yml')) return 'yaml';
    return 'text';
  };

  // 加载状态
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-[#fbfbfd]">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-10 h-10 border-2 border-slate-800 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-medium text-slate-500">加载能力包详情...</p>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error || !pkg) {
    return (
      <div className="h-full flex items-center justify-center bg-[#fbfbfd]">
        <div className="text-center">
          <p className="text-slate-600 font-medium">{error || '能力包不存在'}</p>
          <button
            onClick={onBack}
            className="mt-4 px-6 py-2 bg-slate-900 text-white rounded-full text-xs font-semibold hover:bg-slate-800 transition-colors"
          >
            返回
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-[#fbfbfd]" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", sans-serif' }}>
      {/* 头部 */}
      <header className="flex-shrink-0 bg-white border-b border-black/[0.04] px-6 py-4">
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-slate-500 hover:text-slate-900 font-medium text-[13px] transition-colors"
          >
            <ArrowLeft size={18} strokeWidth={1.5} />
            返回能力包市场
          </button>

          <div className="flex items-center gap-3">
            {/* 文件类型标签 */}
            <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full ${
              fileType === 'plugin'
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-slate-100 text-slate-600'
            }`}>
              {fileType === 'plugin' ? '本地插件' : '数据库'}
            </span>
            {pkg.is_official && (
              <span className="px-3 py-1 bg-slate-900 text-white text-[10px] font-semibold rounded-full flex items-center gap-1">
                <Crown size={12} /> 官方
              </span>
            )}
            <span className="text-xs text-slate-400">v{pkg.version || '1.0.0'}</span>
          </div>
        </div>

        {/* 标题区 */}
        <div className="mt-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{pkg.display_name}</h1>
            <p className="text-sm text-slate-500 mt-1">{pkg.name}</p>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <Users size={14} strokeWidth={1.5} />
              {pkg.usage_count || 0} 次使用
            </span>
            <span className="flex items-center gap-1">
              <Calendar size={14} strokeWidth={1.5} />
              {new Date(pkg.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* 描述 */}
        <p className="mt-3 text-sm text-slate-600 leading-relaxed">{pkg.description || '暂无描述'}</p>

        {/* 标签 */}
        {pkg.tags && pkg.tags.length > 0 && (
          <div className="flex items-center gap-2 mt-3">
            {pkg.tags.map(tag => (
              <span key={tag} className="px-2 py-0.5 bg-slate-100 text-slate-600 text-[11px] font-medium rounded">
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* 能力概览 */}
        <div className="flex items-center gap-6 mt-4 pt-4 border-t border-black/[0.04]">
          {pkg.skills && pkg.skills.length > 0 && (
            <div className="flex items-center gap-2">
              <Layers size={14} className="text-slate-400" />
              <span className="text-xs text-slate-600">{pkg.skills.length} 个技能</span>
            </div>
          )}
          {pkg.allowed_tools && pkg.allowed_tools.length > 0 && (
            <div className="flex items-center gap-2">
              <Settings size={14} className="text-slate-400" />
              <span className="text-xs text-slate-600">{pkg.allowed_tools.length} 个工具</span>
            </div>
          )}
          {pkg.mcp_servers && Object.keys(pkg.mcp_servers).length > 0 && (
            <div className="flex items-center gap-2">
              <Globe size={14} className="text-slate-400" />
              <span className="text-xs text-slate-600">{Object.keys(pkg.mcp_servers).length} 个 MCP 服务</span>
            </div>
          )}
          {pkg.plugin_path && (
            <div className="flex items-center gap-2">
              <Terminal size={14} className="text-slate-400" />
              <span className="text-xs text-slate-600 font-mono">{pkg.plugin_path}</span>
            </div>
          )}
        </div>
      </header>

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧文件树 */}
        <aside className="w-64 flex-shrink-0 bg-white border-r border-black/[0.04] overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                文件结构
              </h2>
              <button
                onClick={handleRefresh}
                className="p-1 hover:bg-slate-100 rounded transition-colors"
                title="刷新"
              >
                <RefreshCw size={12} className={`text-slate-400 ${loadingFiles ? 'animate-spin' : ''}`} />
              </button>
            </div>
            {fileTree && (
              <div className="space-y-0.5">
                {fileTree.children?.map(child => renderTreeNode(child))}
              </div>
            )}
          </div>
        </aside>

        {/* 右侧文件内容 */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {selectedFile ? (
            <>
              {/* 文件路径栏 */}
              <div className="flex-shrink-0 bg-white border-b border-black/[0.04] px-6 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText size={16} className="text-slate-400" />
                  <span className="text-[13px] font-medium text-slate-700">{selectedFile.path}</span>
                  {selectedFile.size && (
                    <span className="text-[11px] text-slate-400">({formatSize(selectedFile.size)})</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-slate-400 uppercase">{getFileLanguage(selectedFile.name)}</span>
                  <button
                    onClick={handleCopy}
                    disabled={!selectedFile.content}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {copied ? (
                      <>
                        <Check size={14} className="text-green-500" />
                        已复制
                      </>
                    ) : (
                      <>
                        <Copy size={14} />
                        复制
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* 文件内容 */}
              <div className="flex-1 overflow-auto bg-white">
                {loadingFiles ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="flex flex-col items-center space-y-3">
                      <div className="w-8 h-8 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
                      <p className="text-xs text-slate-400">加载文件内容...</p>
                    </div>
                  </div>
                ) : selectedFile.content ? (
                  <pre className="p-6 text-[13px] leading-relaxed text-slate-700 font-mono whitespace-pre-wrap overflow-x-auto">
                    {selectedFile.content}
                  </pre>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-400">
                    <div className="text-center">
                      <File size={32} strokeWidth={1} />
                      <p className="mt-2 text-sm">文件内容不可用</p>
                      <p className="text-xs mt-1">可能是二进制文件或需要单独加载</p>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-white">
              <div className="text-center text-slate-400">
                <File size={48} strokeWidth={1} />
                <p className="mt-3 text-sm">选择文件查看内容</p>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default PackageDetailPage;