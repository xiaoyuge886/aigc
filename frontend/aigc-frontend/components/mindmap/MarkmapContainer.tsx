import React, { useRef, useEffect } from 'react';

// --- Markmap 渲染组件 ---
export const MarkmapContainer: React.FC<{ markdown: string; height?: string }> = ({ markdown, height = '300px' }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const mmInstance = useRef<any>(null);
  const isInitializing = useRef(false);

  useEffect(() => {
    // 防止重复初始化
    if (isInitializing.current) {
      return;
    }

    const markmapGlobal = (window as any).markmap;
    const d3 = (window as any).d3;

    if (!svgRef.current || !markmapGlobal || !markmapGlobal.Markmap || !markmapGlobal.Transformer || !d3) {
      return;
    }

    isInitializing.current = true;

    try {
      // 使用 d3 彻底清理 SVG 内的所有内容
      if (svgRef.current) {
        const svgElement = d3.select(svgRef.current);
        svgElement.selectAll("*").remove();
      }

      // 销毁旧实例
      if (mmInstance.current) {
        mmInstance.current = null;
      }

      const transformer = new markmapGlobal.Transformer();
      const { root } = transformer.transform(markdown || "");

      if (!root) {
        isInitializing.current = false;
        return;
      }

      // 创建新实例
      mmInstance.current = markmapGlobal.Markmap.create(svgRef.current, {
        autoFit: true,
        duration: 500,
        paddingX: 16,
        paddingY: 16,
        fitRatio: 1
      }, root);

      // 多次调用 fit() 确保完全居中
      const fitMap = () => {
        if (mmInstance.current) {
          mmInstance.current.fit();
        }
      };

      fitMap();
      setTimeout(fitMap, 50);
      setTimeout(fitMap, 150);
      setTimeout(fitMap, 300);

    } catch (err) {
      // 静默处理错误
    } finally {
      isInitializing.current = false;
    }

    // 组件卸载时清理
    return () => {
      if (svgRef.current) {
        const svgElement = d3.select(svgRef.current);
        svgElement.selectAll("*").remove();
      }
      if (mmInstance.current) {
        mmInstance.current = null;
      }
      isInitializing.current = false;
    };
  }, [markdown]);

  return (
    <div style={{ height }} className="w-full bg-[#F5F5F7]/50 rounded-[32px] border border-black/[0.04] p-6 overflow-hidden animate-apple-fade relative">
      <svg ref={svgRef} className="w-full h-full"></svg>
    </div>
  );
};
