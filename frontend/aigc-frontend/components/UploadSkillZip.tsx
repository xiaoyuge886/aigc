/**
 * Upload Skill ZIP Component
 * 上传技能 ZIP 包组件
 */
import React, { useState, useRef } from 'react';
import { X, Upload, FileArchive, Check, AlertCircle, Loader2 } from 'lucide-react';

interface UploadSkillZipProps {
  onClose: () => void;
  onSkillUploaded?: () => void;
}

export const UploadSkillZip: React.FC<UploadSkillZipProps> = ({ onClose, onSkillUploaded }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [extractedFiles, setExtractedFiles] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // 验证文件类型
      if (!selectedFile.name.endsWith('.zip')) {
        setErrorMessage('请选择 ZIP 格式的文件');
        setUploadStatus('error');
        return;
      }

      // 验证文件大小（最大 50MB）
      if (selectedFile.size > 50 * 1024 * 1024) {
        setErrorMessage('文件大小不能超过 50MB');
        setUploadStatus('error');
        return;
      }

      setFile(selectedFile);
      setUploadStatus('idle');
      setErrorMessage('');
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (!droppedFile.name.endsWith('.zip')) {
        setErrorMessage('请选择 ZIP 格式的文件');
        setUploadStatus('error');
        return;
      }
      setFile(droppedFile);
      setUploadStatus('idle');
      setErrorMessage('');
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('idle');
    setErrorMessage('');

    try {
      const formData = new FormData();
      formData.append('file', file);

      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/skills/upload', {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setExtractedFiles(data.files || []);
        setUploadStatus('success');

        // 3秒后自动关闭
        setTimeout(() => {
          onSkillUploaded?.();
          onClose();
        }, 3000);
      } else {
        const error = await response.json();
        setErrorMessage(error.detail || '上传失败');
        setUploadStatus('error');
      }
    } catch (error) {
      setErrorMessage('网络错误，请稍后重试');
      setUploadStatus('error');
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-[40px] p-10 max-w-2xl w-full mx-4 shadow-2xl animate-in fade-in zoom-in duration-300">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white">
              <Upload size={24} />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">上传技能 ZIP</h2>
              <p className="text-sm text-gray-500">上传本地技能压缩包</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors"
          >
            <X size={16} className="text-gray-600" />
          </button>
        </div>

        {/* Upload Area */}
        <div className="mb-6">
          {!file ? (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-gray-300 rounded-2xl p-12 text-center cursor-pointer hover:border-green-500 hover:bg-green-50/50 transition-all"
            >
              <FileArchive size={48} className="mx-auto mb-4 text-gray-400" />
              <p className="text-lg font-semibold text-gray-700 mb-2">
                点击或拖拽 ZIP 文件到这里
              </p>
              <p className="text-sm text-gray-500 mb-4">
                支持 .zip 格式，最大 50MB
              </p>
              <p className="text-xs text-gray-400">
                ZIP 文件应包含 SKILL.md 或 skill.md 文件
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          ) : (
            <div className="border-2 border-green-200 bg-green-50 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <FileArchive size={32} className="text-green-600" />
                  <div>
                    <p className="font-semibold text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setFile(null);
                    setUploadStatus('idle');
                    setErrorMessage('');
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Upload Status */}
              {uploadStatus === 'success' && (
                <div className="flex items-center space-x-2 text-green-600 bg-green-100 rounded-xl px-4 py-3 mb-4">
                  <Check size={20} />
                  <span className="text-sm font-semibold">上传成功！正在关闭...</span>
                </div>
              )}

              {uploadStatus === 'error' && (
                <div className="flex items-center space-x-2 text-red-600 bg-red-100 rounded-xl px-4 py-3 mb-4">
                  <AlertCircle size={20} />
                  <span className="text-sm">{errorMessage}</span>
                </div>
              )}

              {/* Extracted Files */}
              {extractedFiles.length > 0 && (
                <div className="bg-white rounded-xl p-4 mb-4">
                  <p className="text-xs font-semibold text-gray-700 mb-2">解压的文件：</p>
                  <div className="max-h-32 overflow-y-auto">
                    {extractedFiles.map((fileName, index) => (
                      <p key={index} className="text-xs text-gray-600 py-1">
                        • {fileName}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isUploading}
            className="px-6 py-3 rounded-xl text-gray-700 hover:bg-gray-100 font-semibold text-sm transition-colors disabled:opacity-50"
          >
            取消
          </button>
          {file && uploadStatus !== 'success' && (
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 font-semibold text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isUploading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  <span>上传中...</span>
                </>
              ) : (
                <>
                  <Upload size={16} />
                  <span>开始上传</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Help Text */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <p className="text-xs text-gray-500 text-center">
            ZIP 文件结构示例：my-skill/SKILL.md, my-skill/skill.json 等
          </p>
        </div>
      </div>
    </div>
  );
};
