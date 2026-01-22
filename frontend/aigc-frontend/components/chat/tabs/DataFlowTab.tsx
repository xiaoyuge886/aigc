import React from 'react';
import { GitGraph } from 'lucide-react';
import { DataFlowTimeline } from '../../DataFlowTimeline';

interface DataFlowTabProps {
  selectedTurnId: string | null;
}

/**
 * 数据流标签页组件
 * 显示数据流时间线
 */
export const DataFlowTab: React.FC<DataFlowTabProps> = ({
  selectedTurnId,
}) => {
  return (
    <div className="w-full max-w-[1800px] mx-auto animate-apple-fade">
      {selectedTurnId ? (
        <DataFlowTimeline conversationTurnId={selectedTurnId} />
      ) : (
        <div className="text-center py-20">
          <GitGraph size={48} className="text-gray-300 mx-auto mb-4" />
          <p className="text-[14px] text-gray-400">请先选择一个对话轮次</p>
          <p className="text-[11px] text-gray-300 mt-2">在"工具"或"库"标签页中选择一个轮次后，即可查看数据链路图</p>
        </div>
      )}
    </div>
  );
};
