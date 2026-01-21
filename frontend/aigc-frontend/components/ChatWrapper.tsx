// Chat 接口包装器 - 支持后端切换
import React, { useState } from 'react';
import { ChatInterface } from './ChatInterface';

interface ChatWrapperProps {
  isWorkspaceOpen: boolean;
  setIsWorkspaceOpen: (open: boolean) => void;
}

export const ChatWrapper: React.FC<ChatWrapperProps> = ({ isWorkspaceOpen, setIsWorkspaceOpen }) => {
  // 默认使用 claude 后端
  const [backendProvider, setBackendProvider] = useState<'gemini' | 'claude'>('claude');

  return (
    <div className="relative h-full w-full">
      {/* 后端选择器 - 可以在需要时显示 */}
      {/* {process.env.NODE_ENV === 'development' && (
        <div className="absolute top-4 right-4 z-50 bg-black/5 backdrop-blur-sm rounded-lg p-2">
          <select
            value={backendProvider}
            onChange={(e) => setBackendProvider(e.target.value as 'gemini' | 'claude')}
            className="bg-transparent text-sm font-medium outline-none cursor-pointer"
          >
            <option value="claude">Claude Agent (后端)</option>
            <option value="gemini">Gemini (Google)</option>
          </select>
        </div>
      )} */}

      <ChatInterface
        isWorkspaceOpen={isWorkspaceOpen}
        setIsWorkspaceOpen={setIsWorkspaceOpen}
        backendProvider={backendProvider}
      />
    </div>
  );
};
