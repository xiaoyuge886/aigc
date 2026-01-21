/**
 * Skill Galaxy Component
 * 
 * 技能银河视图 - 将技能以星星的形式散落在银河/星空背景上
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Sparkles, CheckCircle2, Info, Star } from 'lucide-react';

interface Skill {
  skill_id: string;
  name: string;
  description?: string;
  category?: string;
  skill_content?: string;
  skill_config?: any;
}

interface SkillGalaxyProps {
  skills: Skill[];
  selectedSkills: string[];
  onSelect: (skillId: string) => void;
  onDeselect: (skillId: string) => void;
  onClose: () => void;
}

interface StarPosition {
  skillId: string;
  x: number;
  y: number;
  size: number;
  brightness: number;
  twinkle: number;
}

export const SkillGalaxy: React.FC<SkillGalaxyProps> = ({
  skills,
  selectedSkills,
  onSelect,
  onDeselect,
  onClose
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [starPositions, setStarPositions] = useState<StarPosition[]>([]);
  const [selectedStar, setSelectedStar] = useState<string | null>(null);
  const [hoveredStar, setHoveredStar] = useState<string | null>(null);
  const animationFrameRef = useRef<number>();

  // 初始化星星位置
  useEffect(() => {
    if (skills.length === 0 || !containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 生成星星位置（避免重叠）
    const positions: StarPosition[] = [];
    const minDistance = 120; // 最小距离，避免重叠

    for (const skill of skills) {
      let attempts = 0;
      let x: number, y: number;
      let valid = false;

      while (!valid && attempts < 50) {
        x = Math.random() * (width - 100) + 50;
        y = Math.random() * (height - 100) + 50;

        // 检查是否与其他星星太近
        valid = positions.every(pos => {
          const dx = pos.x - x;
          const dy = pos.y - y;
          return Math.sqrt(dx * dx + dy * dy) >= minDistance;
        });

        attempts++;
      }

      if (valid) {
        positions.push({
          skillId: skill.name,  // 使用技能名称而不是ID（数据库现在存储的是名称数组）
          x: x!,
          y: y!,
          size: Math.random() * 8 + 6, // 6-14px
          brightness: Math.random() * 0.5 + 0.5, // 0.5-1.0
          twinkle: Math.random() * Math.PI * 2, // 闪烁相位
        });
      }
    }

    setStarPositions(positions);
  }, [skills]);

  // 绘制星空背景和星星
  const drawGalaxy = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const globalTime = Date.now() * 0.0003; // 慢速动画（用于背景）
    const starTime = Date.now() * 0.001; // 快速动画（用于星星闪烁）

    // 清除画布
    ctx.clearRect(0, 0, width, height);

    // 绘制 Apple 风格的深空背景（简洁优雅）
    const bgGradient = ctx.createLinearGradient(0, 0, 0, height);
    bgGradient.addColorStop(0, '#000000');
    bgGradient.addColorStop(0.5, '#0a0a0f');
    bgGradient.addColorStop(1, '#000000');
    ctx.fillStyle = bgGradient;
    ctx.fillRect(0, 0, width, height);

    // 绘制微妙的中心光晕（Apple 风格）
    const centerX = width / 2;
    const centerY = height / 2;
    const maxRadius = Math.max(width, height);
    
    const subtleGlow = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius * 0.6);
    subtleGlow.addColorStop(0, 'rgba(255, 255, 255, 0.03)');
    subtleGlow.addColorStop(0.5, 'rgba(200, 200, 255, 0.01)');
    subtleGlow.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = subtleGlow;
    ctx.beginPath();
    ctx.arc(centerX, centerY, maxRadius * 0.6, 0, Math.PI * 2);
    ctx.fill();

    // 绘制 Apple 风格的精致星空（简洁、优雅）
    // 使用固定的星星位置，避免随机移动
    const starCount = 600;
    
    // 初始化星星位置（只初始化一次）
    if (starBasePositionsRef.current.length === 0) {
      for (let i = 0; i < starCount; i++) {
        starBasePositionsRef.current.push({
          x: Math.random() * width,
          y: Math.random() * height,
          size: Math.random() * 1.2 + 0.5,
          brightness: Math.random() * 0.4 + 0.6,
          twinklePhase: Math.random() * Math.PI * 2
        });
      }
    }
    
    // 绘制星星（Apple 风格：简洁、精致）
    ctx.fillStyle = 'rgba(255, 255, 255, 1)';
    for (let i = 0; i < starCount; i++) {
      const star = starBasePositionsRef.current[i];
      if (!star) continue;
      
      // 精致的闪烁效果（非常缓慢）
      const twinkle = Math.sin(starTime * 0.5 + star.twinklePhase) * 0.15 + 0.85;
      const alpha = star.brightness * twinkle;
      
      ctx.globalAlpha = alpha;
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fill();
      
      // 部分星星添加微妙的十字光效（Apple 风格）
      if (star.size > 1 && Math.random() > 0.9) {
        ctx.strokeStyle = `rgba(255, 255, 255, ${alpha * 0.3})`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(star.x - star.size * 2, star.y);
        ctx.lineTo(star.x + star.size * 2, star.y);
        ctx.moveTo(star.x, star.y - star.size * 2);
        ctx.lineTo(star.x, star.y + star.size * 2);
        ctx.stroke();
      }
    }
    ctx.globalAlpha = 1;

    // 绘制技能星星
    starPositions.forEach((star) => {
      const skill = skills.find(s => s.skill_id === star.skillId);
      if (!skill) return;

      const isSelected = selectedSkills.includes(star.skillId);
      const isHovered = hoveredStar === star.skillId;
      const isSelectedStar = selectedStar === star.skillId;

      // 闪烁效果（使用星星时间）
      const twinkle = Math.sin(starTime * 2 + star.twinkle) * 0.3 + 0.7;
      const currentBrightness = star.brightness * twinkle;

      // 选中或悬停时更亮
      let brightness = currentBrightness;
      if (isSelected) brightness = 1.0;
      if (isHovered) brightness = Math.min(1.0, brightness + 0.3);

      // 绘制 Apple 风格的光晕（精致、优雅）
      if (isSelected || isHovered) {
        const glowSize = isSelected ? star.size * 4 : star.size * 2.5;
        const glowGradient = ctx.createRadialGradient(
          star.x,
          star.y,
          0,
          star.x,
          star.y,
          glowSize
        );
        if (isSelected) {
          // Apple 蓝色渐变
          glowGradient.addColorStop(0, `rgba(0, 122, 255, ${brightness * 0.6})`);
          glowGradient.addColorStop(0.5, `rgba(0, 122, 255, ${brightness * 0.3})`);
          glowGradient.addColorStop(1, 'rgba(0, 122, 255, 0)');
        } else {
          // 白色光晕
          glowGradient.addColorStop(0, `rgba(255, 255, 255, ${brightness * 0.3})`);
          glowGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
        }
        ctx.fillStyle = glowGradient;
        ctx.beginPath();
        ctx.arc(star.x, star.y, glowSize, 0, Math.PI * 2);
        ctx.fill();
      }

      // 绘制星星主体
      const starSize = isHovered || isSelected ? star.size * 1.5 : star.size;
      const color = isSelected 
        ? `rgba(59, 130, 246, ${brightness})` 
        : `rgba(255, 255, 255, ${brightness})`;

      // 绘制 Apple 风格的星星（简洁、精致）
      if (isSelected) {
        // 选中的星星：Apple 蓝色，带精致光效
        ctx.save();
        ctx.shadowBlur = 12;
        ctx.shadowColor = 'rgba(0, 122, 255, 0.6)';
        ctx.fillStyle = '#007AFF'; // Apple 蓝色
        ctx.beginPath();
        ctx.arc(star.x, star.y, starSize, 0, Math.PI * 2);
        ctx.fill();
        
        // 内部高光
        ctx.fillStyle = `rgba(255, 255, 255, ${brightness * 0.5})`;
        ctx.beginPath();
        ctx.arc(star.x - starSize * 0.3, star.y - starSize * 0.3, starSize * 0.4, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      } else {
        // 未选中的星星：白色，简洁
        ctx.save();
        ctx.shadowBlur = isHovered ? 8 : 4;
        ctx.shadowColor = 'rgba(255, 255, 255, 0.4)';
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(star.x, star.y, starSize, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }

      // 绘制 Apple 风格的连接线（简洁、优雅）
      if (isSelected && selectedStar === star.skillId) {
        ctx.save();
        const centerX = width / 2;
        const centerY = height / 2;
        
        // Apple 风格的连接线（简洁的蓝色）
        ctx.strokeStyle = 'rgba(0, 122, 255, 0.3)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(star.x, star.y);
        ctx.lineTo(centerX, centerY);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.restore();
      }
    });

    animationFrameRef.current = requestAnimationFrame(drawGalaxy);
  }, [starPositions, skills, selectedSkills, hoveredStar, selectedStar]);

  // 绘制五角星
  const drawStar = (ctx: CanvasRenderingContext2D, cx: number, cy: number, outerRadius: number, innerRadius: number, spikes: number) => {
    let rot = Math.PI / 2 * 3;
    let x = cx;
    let y = cy;
    const step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);
    for (let i = 0; i < spikes; i++) {
      x = cx + Math.cos(rot) * outerRadius;
      y = cy + Math.sin(rot) * outerRadius;
      ctx.lineTo(x, y);
      rot += step;

      x = cx + Math.cos(rot) * innerRadius;
      y = cy + Math.sin(rot) * innerRadius;
      ctx.lineTo(x, y);
      rot += step;
    }
    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();
  };

  // 启动动画
  useEffect(() => {
    if (canvasRef.current && containerRef.current) {
      const container = containerRef.current;
      canvasRef.current.width = container.clientWidth;
      canvasRef.current.height = container.clientHeight;
      drawGalaxy();
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [drawGalaxy]);

  // 处理窗口大小变化
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current && containerRef.current) {
        const container = containerRef.current;
        canvasRef.current.width = container.clientWidth;
        canvasRef.current.height = container.clientHeight;
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 处理点击
  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // 查找点击的星星
    for (const star of starPositions) {
      const dx = star.x - x;
      const dy = star.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance <= star.size * 2) {
        if (selectedSkills.includes(star.skillId)) {
          onDeselect(star.skillId);
        } else {
          onSelect(star.skillId);
        }
        setSelectedStar(star.skillId);
        return;
      }
    }

    // 点击空白处，取消选中
    setSelectedStar(null);
  };

  // 处理鼠标移动（悬停效果）
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    let found = false;
    for (const star of starPositions) {
      const dx = star.x - x;
      const dy = star.y - y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance <= star.size * 2) {
        setHoveredStar(star.skillId);
        found = true;
        break;
      }
    }

    if (!found) {
      setHoveredStar(null);
    }
  };

  const selectedSkill = selectedStar ? skills.find(s => s.skill_id === selectedStar) : null;

  return (
    <div className="fixed inset-0 z-50 bg-black" style={{ fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif' }}>
      {/* 画布背景 */}
      <div 
        ref={containerRef}
        className="absolute inset-0 w-full h-full"
        onClick={handleClick}
        onMouseMove={handleMouseMove}
      >
        <canvas
          ref={canvasRef}
          className="absolute inset-0 w-full h-full"
        />
      </div>

      {/* 顶部控制栏 - Apple 风格 */}
      <div className="absolute top-0 left-0 right-0 z-10 p-8" style={{ 
        background: 'linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)'
      }}>
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center backdrop-blur-sm">
                <Sparkles size={18} className="text-white" style={{ filter: 'drop-shadow(0 0 4px rgba(255,255,255,0.3))' }} />
              </div>
              <h1 className="text-2xl font-semibold text-white tracking-tight" style={{ 
                letterSpacing: '-0.02em',
                fontWeight: 600
              }}>
                技能星空
              </h1>
            </div>
            <div className="flex items-center space-x-2 px-4 py-2 rounded-full" style={{
              background: 'rgba(255, 255, 255, 0.08)',
              backdropFilter: 'blur(10px)',
              WebkitBackdropFilter: 'blur(10px)'
            }}>
              <Star size={14} className="text-white/80" />
              <span className="text-sm text-white/90 font-medium" style={{ letterSpacing: '-0.01em' }}>
                已选择 <span className="text-white font-semibold">{selectedSkills.length}</span> 个技能
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200 ease-in-out hover:bg-white/10 active:scale-95"
            style={{ backdropFilter: 'blur(10px)', WebkitBackdropFilter: 'blur(10px)' }}
          >
            <X size={20} className="text-white/80" />
          </button>
        </div>
      </div>

      {/* 技能详情面板 - Apple 风格 */}
      {selectedSkill && (
        <div className="absolute bottom-0 left-0 right-0 z-10 p-8" style={{
          background: 'linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.8) 50%, rgba(0,0,0,0) 100%)',
          backdropFilter: 'blur(30px)',
          WebkitBackdropFilter: 'blur(30px)'
        }}>
          <div className="max-w-4xl mx-auto">
            <div className="rounded-3xl p-8" style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
            }}>
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <div className="flex items-center space-x-4 mb-3">
                    <h3 className="text-3xl font-semibold text-white tracking-tight" style={{ 
                      letterSpacing: '-0.03em',
                      fontWeight: 600
                    }}>
                      {selectedSkill.name}
                    </h3>
                    {selectedSkills.includes(selectedSkill.skill_id) && (
                      <CheckCircle2 size={24} className="text-[#007AFF]" style={{ filter: 'drop-shadow(0 0 8px rgba(0, 122, 255, 0.5))' }} />
                    )}
                    {selectedSkill.category && (
                      <span className="px-3 py-1.5 rounded-full text-xs font-medium text-white/70" style={{
                        background: 'rgba(255, 255, 255, 0.1)',
                        backdropFilter: 'blur(10px)',
                        WebkitBackdropFilter: 'blur(10px)',
                        letterSpacing: '0.01em'
                      }}>
                        {selectedSkill.category}
                      </span>
                    )}
                  </div>
                  {selectedSkill.description && (
                    <p className="text-white/70 text-base leading-relaxed mb-6" style={{ 
                      letterSpacing: '-0.01em',
                      lineHeight: '1.6'
                    }}>
                      {selectedSkill.description}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => {
                    if (selectedSkills.includes(selectedSkill.skill_id)) {
                      onDeselect(selectedSkill.skill_id);
                    } else {
                      onSelect(selectedSkill.skill_id);
                    }
                  }}
                  className="px-6 py-3 rounded-full font-semibold transition-all duration-200 ease-in-out active:scale-95"
                  style={{
                    background: selectedSkills.includes(selectedSkill.skill_id) 
                      ? '#007AFF' 
                      : 'rgba(255, 255, 255, 0.15)',
                    color: '#FFFFFF',
                    letterSpacing: '-0.01em',
                    backdropFilter: 'blur(10px)',
                    WebkitBackdropFilter: 'blur(10px)'
                  }}
                  onMouseEnter={(e) => {
                    if (!selectedSkills.includes(selectedSkill.skill_id)) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.25)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!selectedSkills.includes(selectedSkill.skill_id)) {
                      e.currentTarget.style.background = 'rgba(255, 255, 255, 0.15)';
                    }
                  }}
                >
                  {selectedSkills.includes(selectedSkill.skill_id) ? '已选中' : '选择技能'}
                </button>
              </div>

              {selectedSkill.skill_content && (
                <div className="mt-6 p-5 rounded-2xl" style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  backdropFilter: 'blur(10px)',
                  WebkitBackdropFilter: 'blur(10px)'
                }}>
                  <h4 className="text-sm font-semibold text-white/90 mb-3" style={{ letterSpacing: '-0.01em' }}>技能内容</h4>
                  <p className="text-sm text-white/60 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto leading-relaxed" style={{ 
                    letterSpacing: '0.01em',
                    lineHeight: '1.6'
                  }}>
                    {selectedSkill.skill_content.length > 500 
                      ? selectedSkill.skill_content.substring(0, 500) + '...'
                      : selectedSkill.skill_content}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 提示信息 - Apple 风格 */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-10">
        <div className="px-6 py-3 rounded-full" style={{
          background: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <p className="text-xs text-white/60 text-center font-medium" style={{ letterSpacing: '0.02em' }}>
            点击星星选择技能 • 悬停查看详情 • 已选择 <span className="text-white/80 font-semibold">{selectedSkills.length}</span> 个技能
          </p>
        </div>
      </div>
    </div>
  );
};
