# -*- coding: utf-8 -*-
"""
XAgent 文件系统数据加载器

实现Claude Skill的核心特性：动态按需加载文件系统数据
支持配置文件、数据文件、模板文件、知识库文件的动态加载
"""

import os
import json
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class FileSystemLoader:
    """
    文件系统数据加载器

    功能：
    1. 动态加载配置文件（SOP模板、分析框架等）
    2. 按需读取数据文件（CSV、JSON、Excel等）
    3. 加载模板文件（prompt模板、报告模板等）
    4. 加载知识库文件（领域专业知识、最佳实践等）
    5. 支持文件变更监控和缓存机制
    """

    def __init__(self, base_path: str = None):
        """
        初始化文件系统加载器

        Args:
            base_path: 基础路径，默认为当前技能目录
        """
        if base_path is None:
            self.base_path = Path(__file__).parent.parent
        else:
            self.base_path = Path(base_path)

        # 定义各个数据目录
        self.data_dirs = {
            'sop_templates': self.base_path / 'data' / 'sop_templates',
            'analysis_frameworks': self.base_path / 'data' / 'analysis_frameworks',
            'domain_knowledge': self.base_path / 'data' / 'domain_knowledge',
            'prompt_templates': self.base_path / 'templates' / 'prompts',
            'report_templates': self.base_path / 'templates' / 'reports',
            'reference_data': self.base_path / 'data' / 'reference',
            'user_data': self.base_path / 'data' / 'user',
            'config': self.base_path / 'config'
        }

        # 文件缓存
        self.file_cache = {}
        self.file_timestamps = {}

        # 支持的文件格式
        self.supported_formats = {
            '.json': self._load_json,
            '.yaml': self._load_yaml,
            '.yml': self._load_yaml,
            '.csv': self._load_csv,
            '.xlsx': self._load_excel,
            '.md': self._load_markdown,
            '.txt': self._load_text,
            '.py': self._load_python
        }

        # 初始化目录结构
        self._ensure_directories()

        logger.info(f"文件系统加载器初始化完成，基础路径: {self.base_path}")

    def _ensure_directories(self):
        """确保所有必要的目录存在"""
        for dir_name, dir_path in self.data_dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"确保目录存在: {dir_path}")

    def load_sop_template(self, template_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        动态加载SOP模板

        Args:
            template_name: 模板名称
            force_reload: 是否强制重新加载

        Returns:
            SOP模板数据
        """
        return self._load_file('sop_templates', template_name, force_reload)

    def load_analysis_framework(self, framework_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        动态加载分析框架

        Args:
            framework_name: 框架名称
            force_reload: 是否强制重新加载

        Returns:
            分析框架数据
        """
        return self._load_file('analysis_frameworks', framework_name, force_reload)

    def load_domain_knowledge(self, domain: str, topic: str = None, force_reload: bool = False) -> Dict[str, Any]:
        """
        动态加载领域知识

        Args:
            domain: 领域名称（如finance, marketing, technology等）
            topic: 具体主题（可选）
            force_reload: 是否强制重新加载

        Returns:
            领域知识数据
        """
        if topic:
            knowledge_path = f"{domain}/{topic}"
        else:
            knowledge_path = domain

        return self._load_file('domain_knowledge', knowledge_path, force_reload)

    def load_prompt_template(self, template_name: str, force_reload: bool = False) -> str:
        """
        动态加载prompt模板

        Args:
            template_name: 模板名称
            force_reload: 是否强制重新加载

        Returns:
            prompt模板内容
        """
        return self._load_file('prompt_templates', template_name, force_reload)

    def load_report_template(self, template_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        动态加载报告模板

        Args:
            template_name: 模板名称
            force_reload: 是否强制重新加载

        Returns:
            报告模板数据
        """
        return self._load_file('report_templates', template_name, force_reload)

    def load_reference_data(self, dataset_name: str, force_reload: bool = False) -> Union[pd.DataFrame, Dict]:
        """
        动态加载参考数据

        Args:
            dataset_name: 数据集名称
            force_reload: 是否强制重新加载

        Returns:
            参考数据
        """
        return self._load_file('reference_data', dataset_name, force_reload)

    def load_user_data(self, user_id: str, data_type: str, force_reload: bool = False) -> Union[pd.DataFrame, Dict]:
        """
        动态加载用户数据

        Args:
            user_id: 用户ID
            data_type: 数据类型
            force_reload: 是否强制重新加载

        Returns:
            用户数据
        """
        data_path = f"{user_id}/{data_type}"
        return self._load_file('user_data', data_path, force_reload)

    def load_config(self, config_name: str, force_reload: bool = False) -> Dict[str, Any]:
        """
        动态加载配置文件

        Args:
            config_name: 配置名称
            force_reload: 是否强制重新加载

        Returns:
            配置数据
        """
        return self._load_file('config', config_name, force_reload)

    def _load_file(self, data_type: str, file_path: str, force_reload: bool = False) -> Any:
        """
        通用文件加载方法

        Args:
            data_type: 数据类型（对应data_dirs中的key）
            file_path: 文件路径（相对于数据类型目录）
            force_reload: 是否强制重新加载

        Returns:
            加载的数据
        """
        # 构建完整文件路径
        full_path = self.data_dirs[data_type] / file_path

        # 检查是否需要重新加载
        cache_key = f"{data_type}:{file_path}"

        if not force_reload and self._is_cache_valid(cache_key, full_path):
            logger.debug(f"从缓存加载文件: {file_path}")
            return self.file_cache[cache_key]

        try:
            # 确定文件格式
            file_ext = self._get_file_extension(full_path)

            if file_ext not in self.supported_formats:
                raise ValueError(f"不支持的文件格式: {file_ext}")

            # 加载文件
            loader_func = self.supported_formats[file_ext]
            data = loader_func(full_path)

            # 缓存数据
            self.file_cache[cache_key] = data
            self.file_timestamps[cache_key] = datetime.now().timestamp()

            logger.info(f"成功加载文件: {file_path} (类型: {data_type})")
            return data

        except Exception as e:
            logger.error(f"加载文件失败 {file_path}: {str(e)}")
            # 返回默认值或重新抛出异常
            if data_type in ['sop_templates', 'analysis_frameworks']:
                return self._get_default_template(data_type, file_path)
            else:
                raise

    def _is_cache_valid(self, cache_key: str, file_path: Path) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.file_cache:
            return False

        if cache_key not in self.file_timestamps:
            return False

        # 检查文件是否存在
        if not file_path.exists():
            return False

        # 检查文件修改时间
        file_mtime = file_path.stat().st_mtime
        cache_time = self.file_timestamps[cache_key]

        return file_mtime <= cache_time

    def _get_file_extension(self, file_path: Path) -> str:
        """获取文件扩展名"""
        # 如果直接指定了文件，获取其扩展名
        if file_path.suffix:
            return file_path.suffix.lower()

        # 如果是目录路径，查找可能的文件
        for ext in self.supported_formats.keys():
            potential_file = file_path.with_suffix(ext)
            if potential_file.exists():
                return ext.lower()

        # 尝试添加.json扩展名
        json_file = file_path.with_suffix('.json')
        if json_file.exists():
            return '.json'

        raise FileNotFoundError(f"找不到文件: {file_path}")

    def _load_json(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """加载YAML文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_csv(self, file_path: Path) -> pd.DataFrame:
        """加载CSV文件"""
        return pd.read_csv(file_path, encoding='utf-8')

    def _load_excel(self, file_path: Path) -> pd.DataFrame:
        """加载Excel文件"""
        return pd.read_excel(file_path)

    def _load_markdown(self, file_path: Path) -> str:
        """加载Markdown文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_text(self, file_path: Path) -> str:
        """加载文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_python(self, file_path: Path) -> Dict[str, Any]:
        """加载Python配置文件"""
        # 简单的Python文件加载，主要用于配置
        namespace = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            exec(f.read(), namespace)

        # 提取配置项（排除内置属性）
        config = {k: v for k, v in namespace.items()
                 if not k.startswith('__') and not callable(v)}
        return config

    def _get_default_template(self, data_type: str, file_path: str) -> Dict[str, Any]:
        """获取默认模板"""
        defaults = {
            'sop_templates': {
                "name": f"默认SOP模板: {file_path}",
                "description": "默认的SOP模板，当指定模板不存在时使用",
                "steps": [
                    {"step": 1, "title": "需求分析", "description": "分析用户需求"},
                    {"step": 2, "title": "数据收集", "description": "收集相关数据"},
                    {"step": 3, "title": "分析执行", "description": "执行分析任务"},
                    {"step": 4, "title": "结果总结", "description": "总结分析结果"}
                ]
            },
            'analysis_frameworks': {
                "name": f"默认分析框架: {file_path}",
                "description": "默认的分析框架",
                "stages": ["描述性分析", "诊断分析", "预测分析", "指导性分析"],
                "methods": ["统计分析", "趋势分析", "比较分析", "根因分析"]
            }
        }

        return defaults.get(data_type, {})

    def list_available_files(self, data_type: str) -> List[str]:
        """
        列出指定类型的可用文件

        Args:
            data_type: 数据类型

        Returns:
            文件列表
        """
        if data_type not in self.data_dirs:
            raise ValueError(f"不支持的数据类型: {data_type}")

        dir_path = self.data_dirs[data_type]
        if not dir_path.exists():
            return []

        files = []
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                # 返回相对于数据目录的路径
                relative_path = file_path.relative_to(dir_path)
                # 移除扩展名
                files.append(str(relative_path.with_suffix('')))

        return sorted(files)

    def save_data(self, data_type: str, file_path: str, data: Any, format: str = 'json'):
        """
        保存数据到文件

        Args:
            data_type: 数据类型
            file_path: 文件路径
            data: 要保存的数据
            format: 文件格式
        """
        full_path = self.data_dirs[data_type] / file_path

        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format == 'json':
                with open(full_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            elif format == 'yaml':
                with open(full_path.with_suffix('.yaml'), 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            elif format == 'csv' and isinstance(data, pd.DataFrame):
                data.to_csv(full_path.with_suffix('.csv'), index=False, encoding='utf-8')
            elif format == 'text':
                with open(full_path.with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    f.write(str(data))
            else:
                raise ValueError(f"不支持的保存格式: {format}")

            logger.info(f"成功保存文件: {file_path} (类型: {data_type})")

            # 清除缓存
            cache_key = f"{data_type}:{file_path}"
            if cache_key in self.file_cache:
                del self.file_cache[cache_key]
            if cache_key in self.file_timestamps:
                del self.file_timestamps[cache_key]

        except Exception as e:
            logger.error(f"保存文件失败 {file_path}: {str(e)}")
            raise

    def clear_cache(self, data_type: str = None):
        """
        清除缓存

        Args:
            data_type: 要清除的缓存类型，None表示清除所有
        """
        if data_type is None:
            self.file_cache.clear()
            self.file_timestamps.clear()
            logger.info("清除所有缓存")
        else:
            keys_to_remove = [k for k in self.file_cache.keys() if k.startswith(f"{data_type}:")]
            for key in keys_to_remove:
                del self.file_cache[key]
                if key in self.file_timestamps:
                    del self.file_timestamps[key]
            logger.info(f"清除缓存类型: {data_type}")

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        return {
            'cached_files': len(self.file_cache),
            'cache_keys': list(self.file_cache.keys()),
            'data_directories': {k: str(v) for k, v in self.data_dirs.items()}
        }


# 全局文件加载器实例
_file_loader = None

def get_file_loader() -> FileSystemLoader:
    """获取全局文件加载器实例"""
    global _file_loader
    if _file_loader is None:
        _file_loader = FileSystemLoader()
    return _file_loader