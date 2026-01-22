import { useState, useRef, useEffect } from 'react';

export interface UseMediaCaptureReturn {
  // 摄像头相关
  isCameraActive: boolean;
  toggleCamera: () => Promise<void>;
  videoRef: React.RefObject<HTMLVideoElement>;
  videoPosition: { x: number; y: number };
  isDragging: boolean;
  dragOffset: { x: number; y: number };
  videoContainerRef: React.RefObject<HTMLDivElement>;
  handleVideoMouseDown: (e: React.MouseEvent) => void;
  
  // 录音相关
  isRecording: boolean;
  recordingTime: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  toggleRecording: () => void;
}

export const useMediaCapture = (
  onRecordingComplete: (audioData: { name: string; type: string; data: string }) => void
): UseMediaCaptureReturn => {
  // 摄像头相关状态
  const [isCameraActive, setIsCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  
  // 语音录制相关状态
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<number | null>(null);
  
  // 视频框位置：使用 fixed 定位，相对于视口
  const [videoPosition, setVideoPosition] = useState(() => {
    // 从 localStorage 恢复位置，如果没有则默认在右下角
    const saved = localStorage.getItem('videoCameraPosition');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return { x: window.innerWidth - 168, y: window.innerHeight - 168 };
      }
    }
    return { x: window.innerWidth - 168, y: window.innerHeight - 168 };
  });
  
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const videoContainerRef = useRef<HTMLDivElement>(null);

  // 摄像头切换
  const toggleCamera = async () => {
    if (isCameraActive) {
      streamRef.current?.getTracks().forEach(track => track.stop());
      streamRef.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setIsCameraActive(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 480, height: 480 }, audio: false });
        streamRef.current = stream;
        setIsCameraActive(true);
        // 使用 setTimeout 确保 DOM 更新后再设置视频流
        setTimeout(() => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
            videoRef.current.play().catch(err => {
              console.error("视频播放失败:", err);
            });
          }
        }, 100);
      } catch (err) {
        console.error("无法开启摄像头:", err);
        alert("无法访问摄像头，请检查权限设置");
      }
    }
  };

  // 确保视频流正确加载
  useEffect(() => {
    if (isCameraActive && streamRef.current && videoRef.current) {
      if (videoRef.current.srcObject !== streamRef.current) {
        videoRef.current.srcObject = streamRef.current;
        videoRef.current.play().catch(err => {
          console.error("视频播放失败:", err);
        });
      }
    }
  }, [isCameraActive]);

  // 视频框拖拽功能 - 全页面拖拽
  const handleVideoMouseDown = (e: React.MouseEvent) => {
    if (!videoContainerRef.current) return;
    e.preventDefault(); // 防止文本选择
    const rect = videoContainerRef.current.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    });
    setIsDragging(true);
  };

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      
      if (!videoContainerRef.current) return;
      
      const videoWidth = 128; // 视频框宽度
      const videoHeight = 128; // 视频框高度
      
      // 计算相对于视口的位置（fixed 定位）
      let newX = e.clientX - dragOffset.x;
      let newY = e.clientY - dragOffset.y;
      
      // 限制在视口范围内（防止拖出屏幕）
      const maxX = window.innerWidth - videoWidth;
      const maxY = window.innerHeight - videoHeight;
      
      newX = Math.max(0, Math.min(maxX, newX));
      newY = Math.max(0, Math.min(maxY, newY));
      
      const newPosition = { x: newX, y: newY };
      setVideoPosition(newPosition);
      // 实时保存位置到 localStorage
      localStorage.setItem('videoCameraPosition', JSON.stringify(newPosition));
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.body.style.cursor = 'grabbing';
    document.body.style.userSelect = 'none';
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isDragging, dragOffset, videoPosition]);

  // 窗口大小改变时，调整视频框位置（防止超出视口）
  useEffect(() => {
    const handleResize = () => {
      const videoWidth = 128;
      const videoHeight = 128;
      setVideoPosition(prev => ({
        x: Math.min(prev.x, window.innerWidth - videoWidth),
        y: Math.min(prev.y, window.innerHeight - videoHeight)
      }));
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 语音录制功能
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        // 停止所有音频轨道
        stream.getTracks().forEach(track => track.stop());
        
        // 将录制的音频转换为 base64
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64Audio = (reader.result as string).split(',')[1];
          // 调用回调函数，将音频添加到待发送文件列表
          onRecordingComplete({
            name: `语音_${new Date().toLocaleTimeString()}.webm`,
            type: 'audio/webm',
            data: base64Audio
          });
        };
        reader.readAsDataURL(audioBlob);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      // 注意：计时器由 useEffect 管理，这里不需要手动启动
      
    } catch (err) {
      console.error("无法访问麦克风:", err);
      alert("无法访问麦克风，请检查权限设置");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      setRecordingTime(0);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // 使用 useEffect 管理计时器，确保状态同步
  useEffect(() => {
    if (isRecording) {
      // 如果正在录制，启动计时器
      if (!recordingTimerRef.current) {
        setRecordingTime(0);
        recordingTimerRef.current = window.setInterval(() => {
          setRecordingTime(prev => {
            const newTime = prev + 1;
            console.log('录制时长更新:', newTime); // 调试日志
            return newTime;
          });
        }, 1000);
        console.log('useEffect: 计时器已启动');
      }
    } else {
      // 如果停止录制，清除计时器
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
        console.log('useEffect: 计时器已清除');
      }
    }
    
    return () => {
      if (recordingTimerRef.current) {
        window.clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    };
  }, [isRecording]);

  return {
    // 摄像头相关
    isCameraActive,
    toggleCamera,
    videoRef,
    videoPosition,
    isDragging,
    dragOffset,
    videoContainerRef,
    handleVideoMouseDown,
    
    // 录音相关
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    toggleRecording,
  };
};
