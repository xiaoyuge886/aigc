import { useState, useRef, useEffect, useCallback } from 'react';
import { SessionFile } from '../../../services/agentService';

interface UseMentionsProps {
  sessionId: string | null;
  files: Array<{
    id: string;
    name: string;
    type?: string;
    size?: number;
    created_at: Date;
  }>;
  getSessionFiles: (sessionId: string) => Promise<SessionFile[]>;
}

interface MentionPosition {
  top: number;
  left: number;
}

interface UseMentionsReturn {
  mentionFiles: SessionFile[];
  showMentionDropdown: boolean;
  mentionQuery: string;
  mentionPosition: MentionPosition;
  selectedMentionIndex: number;
  inputRef: React.RefObject<HTMLInputElement>;
  mentionDropdownRef: React.RefObject<HTMLDivElement>;
  setShowMentionDropdown: (show: boolean) => void;
  setMentionQuery: (query: string) => void;
  setSelectedMentionIndex: (index: number) => void;
  handleMentionInputChange: (value: string, cursorPos: number, inputElement: HTMLInputElement | null) => void;
  handleMentionKeyDown: (
    e: React.KeyboardEvent<HTMLInputElement>,
    input: string,
    setInput: (value: string) => void,
    onEnter?: () => void
  ) => boolean; // 返回 true 表示已处理，false 表示继续正常处理
  selectMentionFile: (file: SessionFile, input: string, setInput: (value: string) => void) => void;
  closeMentionDropdown: () => void;
}

/**
 * @ 提及功能 Hook
 * 处理文件提及相关的状态和逻辑
 */
export const useMentions = ({
  sessionId,
  files,
  getSessionFiles
}: UseMentionsProps): UseMentionsReturn => {
  const [mentionFiles, setMentionFiles] = useState<SessionFile[]>([]);
  const [showMentionDropdown, setShowMentionDropdown] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [mentionPosition, setMentionPosition] = useState<MentionPosition>({ top: 0, left: 0 });
  const [selectedMentionIndex, setSelectedMentionIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const mentionDropdownRef = useRef<HTMLDivElement>(null);

  // 📁 加载文件列表（用于 @ 提及功能）
  useEffect(() => {
    const loadFiles = async () => {
      if (sessionId) {
        try {
          console.log('%c📁 [loadFiles] 开始加载文件列表，sessionId:', 'color: #5856D6; font-weight: bold', sessionId);
          const sessionFiles = await getSessionFiles(sessionId);
          console.log('%c📁 [loadFiles] 获取到的文件列表:', 'color: #5856D6; font-weight: bold', {
            count: sessionFiles.length,
            files: sessionFiles.map(f => ({ name: f.file_name, doc_id: f.doc_id }))
          });
          // 合并现有文件和从服务器获取的文件（避免覆盖通过文件事件添加的文件）
          setMentionFiles(prev => {
            const existingDocIds = new Set(prev.map(f => f.doc_id));
            const newFiles = sessionFiles.filter(f => !existingDocIds.has(f.doc_id));
            if (newFiles.length > 0) {
              const merged = [...prev, ...newFiles];
              console.log('%c📁 [loadFiles] ✅ 合并文件列表到 mentionFiles:', 'color: #34C759; font-weight: bold', {
                before_count: prev.length,
                new_files: newFiles.length,
                after_count: merged.length,
                files: merged.map(f => f.file_name)
              });
              return merged;
            }
            return prev;
          });
        } catch (error) {
          // 404 错误是正常的（session 可能还没创建），不影响已有的 mentionFiles
          console.warn('⚠️ 加载文件列表失败（可能 session 还未创建）:', error);
        }
      } else {
        console.log('%c📁 [loadFiles] sessionId 为空，跳过加载', 'color: #FF9500');
      }
      // 注意：即使 sessionId 为空，也不清空 mentionFiles，因为可能使用 files 状态中的文件
    };
    loadFiles();
  }, [sessionId, getSessionFiles]);

  // 📁 同步 files 状态到 mentionFiles（用于新对话时文件上传后立即可用）
  useEffect(() => {
    // 如果 files 状态有文件，且 mentionFiles 为空或文件数量不匹配，同步文件
    if (files.length > 0) {
      // 将 FileInfo 转换为 SessionFile 格式
      const sessionFilesFromState: SessionFile[] = files.map(file => ({
        doc_id: file.id, // 使用 file.id 作为临时 doc_id
        file_name: file.name,
        file_type: file.type || 'application/octet-stream',
        file_size: file.size || null,
        uploaded_at: file.created_at.toISOString(),
      }));

      // 合并 mentionFiles 和 files 中的文件（去重）
      const existingFileNames = new Set(mentionFiles.map(f => f.file_name));
      const newFiles = sessionFilesFromState.filter(f => !existingFileNames.has(f.file_name));

      if (newFiles.length > 0) {
        setMentionFiles(prev => [...prev, ...newFiles]);
        console.log('%c📁 同步文件到 @ 提及列表:', 'color: #5856D6; font-weight: bold', {
          new_files: newFiles.map(f => f.file_name),
          total: mentionFiles.length + newFiles.length
        });
      }
    }
  }, [files]); // 监听 files 状态变化

  /**
   * 处理输入变化，检测 @ 符号
   */
  const handleMentionInputChange = useCallback((
    value: string,
    cursorPos: number,
    inputElement: HTMLInputElement | null
  ) => {
    const textBeforeCursor = value.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      // 检查 @ 后是否有空格或换行（如果有，说明不是提及）
      const afterAt = textBeforeCursor.substring(lastAtIndex + 1);
      if (!afterAt.includes(' ') && !afterAt.includes('\n')) {
        const query = afterAt.toLowerCase();
        setMentionQuery(query);

        // 检查是否有可提及的文件
        if (mentionFiles.length > 0) {
          setShowMentionDropdown(true);
          setSelectedMentionIndex(0);

          // 计算下拉菜单位置
          if (inputElement) {
            const rect = inputElement.getBoundingClientRect();
            setMentionPosition({
              top: rect.bottom + 4,
              left: rect.left
            });
          }

          console.log('%c@ 提及下拉菜单显示:', 'color: #007AFF; font-weight: bold', {
            query: query,
            available_files: mentionFiles.length,
            files: mentionFiles.map(f => f.file_name)
          });
        } else {
          // 没有可提及的文件，隐藏下拉菜单
          setShowMentionDropdown(false);
          console.log('%c@ 提及: 没有可用的文件', 'color: #FF9500; font-weight: bold; font-size: 14px', {
            mentionFiles_count: mentionFiles.length,
            files_count: files.length,
            sessionId: sessionId,
            mentionFiles_detail: mentionFiles.map(f => ({ name: f.file_name, doc_id: f.doc_id })),
            files_detail: files.map(f => ({ name: f.name, id: f.id }))
          });
        }

        return;
      }
    }

    // 如果没有 @ 或 @ 后有空格，隐藏下拉菜单
    setShowMentionDropdown(false);
  }, [mentionFiles, files, sessionId]);

  /**
   * 选择提及文件
   */
  const selectMentionFile = useCallback((
    file: SessionFile,
    input: string,
    setInput: (value: string) => void
  ) => {
    if (!inputRef.current) return;

    // 替换 @ 后的文本为文件引用
    const cursorPos = inputRef.current.selectionStart || 0;
    const textBeforeCursor = input.substring(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');
    const textAfterCursor = input.substring(cursorPos);

    const newText =
      input.substring(0, lastAtIndex) +
      `@${file.file_name}` +
      textAfterCursor;

    setInput(newText);
    setShowMentionDropdown(false);

    // 设置光标位置
    setTimeout(() => {
      if (inputRef.current) {
        const newPos = lastAtIndex + file.file_name.length + 1;
        inputRef.current.setSelectionRange(newPos, newPos);
        inputRef.current.focus();
      }
    }, 0);
  }, []);

  /**
   * 处理键盘事件（ArrowDown, ArrowUp, Enter, Tab, Escape）
   * 返回 true 表示已处理，false 表示继续正常处理
   */
  const handleMentionKeyDown = useCallback((
    e: React.KeyboardEvent<HTMLInputElement>,
    input: string,
    setInput: (value: string) => void,
    onEnter?: () => void
  ): boolean => {
    if (showMentionDropdown && mentionFiles.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedMentionIndex(prev =>
          prev < mentionFiles.length - 1 ? prev + 1 : prev
        );
        return true;
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedMentionIndex(prev => prev > 0 ? prev - 1 : 0);
        return true;
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        e.preventDefault();
        const selectedFile = mentionFiles[selectedMentionIndex];
        if (selectedFile) {
          selectMentionFile(selectedFile, input, setInput);
        }
        return true;
      } else if (e.key === 'Escape') {
        e.preventDefault();
        setShowMentionDropdown(false);
        return true;
      } else {
        // 其他按键，继续正常处理
        return false;
      }
    } else {
      // 没有下拉菜单时，正常处理 Enter
      // ⚠️ 重要：不要在这里调用 onEnter，让 ChatInputArea 来处理
      // 这样可以避免重复调用 onSend
      return false;
    }
  }, [showMentionDropdown, mentionFiles, selectedMentionIndex, selectMentionFile]);

  /**
   * 关闭提及下拉菜单
   */
  const closeMentionDropdown = useCallback(() => {
    setShowMentionDropdown(false);
  }, []);

  return {
    mentionFiles,
    showMentionDropdown,
    mentionQuery,
    mentionPosition,
    selectedMentionIndex,
    inputRef,
    mentionDropdownRef,
    setShowMentionDropdown,
    setMentionQuery,
    setSelectedMentionIndex,
    handleMentionInputChange,
    handleMentionKeyDown,
    selectMentionFile,
    closeMentionDropdown
  };
};
