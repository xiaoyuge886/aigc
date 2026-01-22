"""
默认配置管理服务

核心设计原则：
1. 充分依赖模型规划能力 - 默认配置提供基础能力定义，让模型自主选择
2. 完整的默认配置体系 - 零配置可用，所有用户共享
3. 渐进式配置 - 默认配置是基础层，用户可选择性配置
4. 能力不限制 - 默认场景不限制工具和能力，让模型自主判断

职责：
1. 定义默认系统prompt模板
2. 定义默认场景（通用、不限制能力）
3. 提供默认配置获取接口
4. 支持从数据库读取系统默认配置（系统管理员可配置）
"""
from typing import List, Dict, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.database import DatabaseService
from models.database import SystemDefaultConfigDB, BusinessScenarioDB

logger = logging.getLogger(__name__)


class DefaultConfig:
    """默认配置管理"""
    
    # 默认系统prompt模板（包含可用场景列表占位符）
    DEFAULT_SYSTEM_PROMPT_TEMPLATE = """你是一个强大的AI助手，具备自主规划和执行任务的能力。

## 核心能力
- 任务理解：仔细理解用户需求
- 自主规划：根据任务复杂度决定是否需要分解步骤
- 工具使用：根据需要选择合适的工具
- 自我检查：持续验证结果，发现错误及时调整

## 可用场景能力
你可以根据用户需求自主选择和组合使用以下场景能力，或直接使用通用能力：

{available_scenarios_list}

## 使用原则
- 根据用户需求自主判断需要哪些场景能力
- 可以组合多个场景能力
- 如果用户需求不匹配任何场景，使用通用能力即可
- 灵活应对，不限制自己的能力边界

使用ReAct范式（推理-行动-观察-反思）循环执行任务，确保准确完成用户目标。"""
    
    # 默认场景定义（通用、不限制能力）
    DEFAULT_SCENARIO = {
        "id": None,  # 硬编码场景没有数据库ID，使用None表示
        "name": "通用场景",
        "description": "不限制能力的通用场景，让模型自主规划",
        "system_prompt": "",  # 空，主要依赖系统默认prompt
        "allowed_tools": None,  # None表示不限制
        "is_default": True
    }
    
    @classmethod
    def get_default_system_prompt(cls, available_scenarios: Optional[List[Dict]] = None) -> str:
        """
        获取默认系统提示（包含可用场景列表）
        
        核心设计原则：
        - 模型驱动：在系统prompt中告诉模型可用场景，让模型自主选择
        - 不限制能力：默认场景不限制工具和能力
        
        Args:
            available_scenarios: 可用场景列表（可选），如果为None则只显示通用场景说明
            
        Returns:
            str: 格式化后的系统prompt
        """
        if available_scenarios is None or len(available_scenarios) == 0:
            # 如果没有场景列表，只显示通用场景说明
            scenarios_list = "- 通用场景：不限制能力的通用场景，可以根据用户需求灵活应对"
        else:
            # 格式化场景列表（包含 meta 信息）
            scenario_items = []
            for scenario in available_scenarios:
                name = scenario.get("name", "未知场景")
                description = scenario.get("description", "")
                category = scenario.get("category", "")
                meta = scenario.get("meta", {})
                
                # 构建场景信息字符串
                scenario_info = f"- **{name}**"
                
                # 添加分类
                if category:
                    scenario_info += f" [{category}]"
                
                # 添加描述
                if description:
                    scenario_info += f"：{description}"
                
                # 添加 meta 信息（tags, capabilities, keywords）
                meta_parts = []
                if isinstance(meta, dict):
                    # Tags（标签）
                    if "tags" in meta and meta["tags"]:
                        tags = meta["tags"]
                        if isinstance(tags, list):
                            meta_parts.append(f"标签: {', '.join(tags)}")
                        elif isinstance(tags, str):
                            meta_parts.append(f"标签: {tags}")
                    
                    # Capabilities（能力）
                    if "capabilities" in meta and meta["capabilities"]:
                        capabilities = meta["capabilities"]
                        if isinstance(capabilities, list):
                            meta_parts.append(f"能力: {', '.join(capabilities)}")
                        elif isinstance(capabilities, str):
                            meta_parts.append(f"能力: {capabilities}")
                    
                    # Keywords（关键词）
                    if "keywords" in meta and meta["keywords"]:
                        keywords = meta["keywords"]
                        if isinstance(keywords, list):
                            meta_parts.append(f"关键词: {', '.join(keywords)}")
                        elif isinstance(keywords, str):
                            meta_parts.append(f"关键词: {keywords}")
                
                # 如果有 meta 信息，添加到场景信息中
                if meta_parts:
                    scenario_info += f" | {', '.join(meta_parts)}"
                
                scenario_items.append(scenario_info)
            
            scenarios_list = "\n".join(scenario_items)
        
        # 替换占位符
        system_prompt = cls.DEFAULT_SYSTEM_PROMPT_TEMPLATE.format(
            available_scenarios_list=scenarios_list
        )
        
        logger.debug(f"[DefaultConfig] 生成默认系统prompt，场景数量: {len(available_scenarios) if available_scenarios else 0}")
        
        return system_prompt
    
    @classmethod
    async def get_system_default_prompt_from_db(
        cls, 
        db_service: Optional[DatabaseService] = None
    ) -> Optional[str]:
        """
        从数据库获取系统默认prompt模板
        
        如果数据库中有配置，则使用数据库配置；否则使用类中定义的默认模板。
        
        Args:
            db_service: 数据库服务实例（可选）
            
        Returns:
            Optional[str]: 系统默认prompt模板，如果数据库中没有配置则返回None
        """
        if not db_service:
            return None
        
        try:
            async with db_service.async_session() as session:
                stmt = select(SystemDefaultConfigDB).where(
                    SystemDefaultConfigDB.config_key == "default_system_prompt_template"
                )
                result = await session.execute(stmt)
                config = result.scalar_one_or_none()
                
                if config:
                    logger.debug("[DefaultConfig] 从数据库读取系统默认prompt模板")
                    return config.config_value
                
                return None
        except Exception as e:
            logger.warning(f"[DefaultConfig] 从数据库读取系统默认prompt失败: {e}")
            return None
    
    @classmethod
    async def get_default_system_prompt_with_db(
        cls,
        available_scenarios: Optional[List[Dict]] = None,
        db_service: Optional[DatabaseService] = None
    ) -> str:
        """
        获取默认系统提示（优先从数据库读取模板）
        
        优先级：
        1. 数据库中的系统默认prompt模板（如果存在）
        2. 类中定义的默认模板
        
        Args:
            available_scenarios: 可用场景列表（可选）
            db_service: 数据库服务实例（可选）
            
        Returns:
            str: 格式化后的系统prompt
        """
        # 尝试从数据库读取模板
        template = None
        if db_service:
            template = await cls.get_system_default_prompt_from_db(db_service)
        
        # 如果数据库中没有，使用类中定义的默认模板
        if not template:
            template = cls.DEFAULT_SYSTEM_PROMPT_TEMPLATE
        
        # 格式化场景列表（包含 meta 信息）
        if available_scenarios is None or len(available_scenarios) == 0:
            scenarios_list = "- 通用场景：不限制能力的通用场景，可以根据用户需求灵活应对"
        else:
            scenario_items = []
            for scenario in available_scenarios:
                name = scenario.get("name", "未知场景")
                description = scenario.get("description", "")
                category = scenario.get("category", "")
                meta = scenario.get("meta", {})
                
                # 构建场景信息字符串
                scenario_info = f"- **{name}**"
                
                # 添加分类
                if category:
                    scenario_info += f" [{category}]"
                
                # 添加描述
                if description:
                    scenario_info += f"：{description}"
                
                # 添加 meta 信息（tags, capabilities, keywords）
                meta_parts = []
                if isinstance(meta, dict):
                    # Tags（标签）
                    if "tags" in meta and meta["tags"]:
                        tags = meta["tags"]
                        if isinstance(tags, list):
                            meta_parts.append(f"标签: {', '.join(tags)}")
                        elif isinstance(tags, str):
                            meta_parts.append(f"标签: {tags}")
                    
                    # Capabilities（能力）
                    if "capabilities" in meta and meta["capabilities"]:
                        capabilities = meta["capabilities"]
                        if isinstance(capabilities, list):
                            meta_parts.append(f"能力: {', '.join(capabilities)}")
                        elif isinstance(capabilities, str):
                            meta_parts.append(f"能力: {capabilities}")
                    
                    # Keywords（关键词）
                    if "keywords" in meta and meta["keywords"]:
                        keywords = meta["keywords"]
                        if isinstance(keywords, list):
                            meta_parts.append(f"关键词: {', '.join(keywords)}")
                        elif isinstance(keywords, str):
                            meta_parts.append(f"关键词: {keywords}")
                
                # 如果有 meta 信息，添加到场景信息中
                if meta_parts:
                    scenario_info += f" | {', '.join(meta_parts)}"
                
                scenario_items.append(scenario_info)
            
            scenarios_list = "\n".join(scenario_items)
        
        # 替换占位符
        system_prompt = template.format(
            available_scenarios_list=scenarios_list
        )
        
        logger.debug(f"[DefaultConfig] 生成默认系统prompt，场景数量: {len(available_scenarios) if available_scenarios else 0}")
        
        return system_prompt
    
    @classmethod
    async def get_default_scenario_from_db(
        cls,
        db_service: Optional[DatabaseService] = None
    ) -> Dict:
        """
        从数据库获取默认场景（is_default=True），如果数据库中没有则使用硬编码的 DEFAULT_SCENARIO
        
        Args:
            db_service: 数据库服务实例（可选）
            
        Returns:
            Dict: 默认场景配置，如果数据库中没有则返回硬编码的 DEFAULT_SCENARIO
        """
        if not db_service:
            logger.debug("[DefaultConfig] 没有提供 db_service，使用硬编码的 DEFAULT_SCENARIO")
            return cls.DEFAULT_SCENARIO.copy()
        
        try:
            async with db_service.async_session() as session:
                stmt = select(BusinessScenarioDB).where(
                    BusinessScenarioDB.is_default == True
                ).limit(1)
                result = await session.execute(stmt)
                scenario = result.scalar_one_or_none()
                
                if scenario:
                    import json
                    logger.debug(f"[DefaultConfig] 从数据库读取默认场景: id={scenario.id}")
                    return {
                        "id": scenario.id,  # 使用整数ID
                        "name": scenario.name,
                        "description": scenario.description or "",
                        "category": scenario.category or "",
                        "meta": scenario.meta or {},
                        "system_prompt": scenario.system_prompt or "",
                        "allowed_tools": json.loads(scenario.allowed_tools) if scenario.allowed_tools else None,
                        "recommended_model": scenario.recommended_model,
                        "custom_tools": scenario.custom_tools,
                        "skills": json.loads(scenario.skills) if scenario.skills else None,
                        "workflow": scenario.workflow,
                        "permission_mode": scenario.permission_mode,
                        "max_turns": scenario.max_turns,
                        "work_dir": scenario.work_dir,
                        "is_public": scenario.is_public,
                        "is_default": bool(scenario.is_default) if hasattr(scenario, 'is_default') and scenario.is_default is not None else True,
                    }
                
                # 如果数据库中没有，使用硬编码的 DEFAULT_SCENARIO
                logger.debug("[DefaultConfig] 数据库中没有默认场景，使用硬编码的 DEFAULT_SCENARIO")
                return cls.DEFAULT_SCENARIO.copy()
        except Exception as e:
            logger.warning(f"[DefaultConfig] 从数据库读取默认场景失败: {e}，使用硬编码的 DEFAULT_SCENARIO")
            return cls.DEFAULT_SCENARIO.copy()
    
    @classmethod
    def get_default_scenario(cls) -> Dict:
        """
        获取默认场景配置（同步方法，使用硬编码作为后备）
        
        注意：此方法返回硬编码的默认场景。如果需要从数据库读取，
        请使用 get_default_scenario_from_db 异步方法。
        
        核心设计原则：
        - 不限制能力边界：allowed_tools为None表示不限制
        - 模型自主规划：system_prompt为空，主要依赖系统默认prompt
        - 零配置可用：所有用户都可以使用
        
        Returns:
            Dict: 默认场景配置
        """
        return cls.DEFAULT_SCENARIO.copy()
    
    @classmethod
    async def get_default_scenario_async(
        cls,
        db_service: Optional[DatabaseService] = None
    ) -> Dict:
        """
        获取默认场景配置（异步方法，优先从数据库读取）
        
        优先级：
        1. 数据库中的默认场景（is_default=True）
        2. 硬编码的 DEFAULT_SCENARIO（作为后备）
        
        Args:
            db_service: 数据库服务实例（可选）
            
        Returns:
            Dict: 默认场景配置
        """
        # 尝试从数据库读取
        if db_service:
            db_scenario = await cls.get_default_scenario_from_db(db_service)
            if db_scenario:
                logger.debug("[DefaultConfig] 使用数据库中的默认场景")
                return db_scenario
        
        # 如果数据库中没有，使用硬编码的 DEFAULT_SCENARIO 作为后备
        logger.debug("[DefaultConfig] 使用硬编码的 DEFAULT_SCENARIO 作为后备")
        return cls.DEFAULT_SCENARIO.copy()
    
    @classmethod
    def get_default_scenario_id(cls) -> Optional[int]:
        """获取默认场景ID（整数，如果是硬编码场景则返回None）"""
        return cls.DEFAULT_SCENARIO.get("id")
