"""
场景提供器服务

核心设计原则：
1. 充分依赖模型规划能力 - 提供场景列表，让模型自主选择
2. 完整的默认配置体系 - 必须包含默认场景
3. 渐进式配置 - 默认场景 + 公开场景 + 用户私有场景

职责：
1. 获取用户可用的场景列表（包括默认场景、公开场景、用户私有场景）
2. 将数据库中的BusinessScenarioDB转换为字典格式
"""
from typing import List, Dict, Optional
import json
import logging

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import BusinessScenarioDB
from services.default_config import DefaultConfig
from services.database import DatabaseService

logger = logging.getLogger(__name__)


class ScenarioProvider:
    """场景提供器"""
    
    def __init__(self, db_service: DatabaseService):
        """
        初始化场景提供器
        
        Args:
            db_service: 数据库服务实例
        """
        self.db_service = db_service
    
    async def get_available_scenarios(
        self, 
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """
        获取用户可用的场景列表
        
        核心设计原则：
        - 模型驱动：提供场景列表，让模型自主选择和组合
        - 默认场景必须：所有用户都有默认场景
        - 渐进式配置：默认场景 + 公开场景 + 用户私有场景
        
        包括：
        1. 默认场景（必须，所有用户都有）
        2. 公开场景（is_public=True）
        3. 用户创建的私有场景（user_id匹配）
        
        Args:
            user_id: 用户ID（可选），如果提供则包含用户私有场景
            
        Returns:
            List[Dict]: 场景列表，每个场景是字典格式
        """
        scenarios = []
        
        # 1. 从数据库获取所有场景（包括默认场景、公开场景和用户私有场景）
        db_scenarios = await self._get_scenarios_from_db(user_id, include_default=True)
        scenarios.extend(db_scenarios)
        
        # 2. 如果数据库中没有默认场景，尝试从数据库读取 is_default=True 的场景
        has_default = any(s.get("is_default") for s in scenarios)
        if not has_default:
            # 从数据库读取默认场景（如果数据库中没有，会返回硬编码的 DEFAULT_SCENARIO）
            default_scenario = await DefaultConfig.get_default_scenario_from_db(self.db_service)
            scenarios.insert(0, default_scenario)  # 插入到最前面
            logger.debug(f"[ScenarioProvider] 添加默认场景: id={default_scenario.get('id')}")
        
        logger.info(
            f"[ScenarioProvider] 用户 {user_id} 可用场景数: {len(scenarios)} "
            f"(默认: 1, 数据库: {len(db_scenarios)})"
        )
        
        return scenarios
    
    async def _get_scenarios_from_db(
        self, 
        user_id: Optional[int] = None,
        include_default: bool = True
    ) -> List[Dict]:
        """
        从数据库获取场景（公开场景 + 用户私有场景）
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            List[Dict]: 场景字典列表
        """
        async with self.db_service.async_session() as session:
            # 构建查询：公开场景 或 用户创建的私有场景
            if user_id:
                # 同时包含用户创建的私有场景
                stmt = select(BusinessScenarioDB).where(
                    or_(
                        BusinessScenarioDB.is_public == True,
                        BusinessScenarioDB.created_by == user_id
                    )
                )
            else:
                # 只包含公开场景
                stmt = select(BusinessScenarioDB).where(
                    BusinessScenarioDB.is_public == True
                )
            
            result = await session.execute(stmt)
            db_scenarios = result.scalars().all()
            
            # 转换为字典格式
            scenarios = []
            for db_scenario in db_scenarios:
                # 如果 include_default=False，跳过默认场景
                if not include_default and db_scenario.is_default:
                    continue
                
                scenario_dict = {
                    "id": db_scenario.id,  # 使用整数ID
                    "name": db_scenario.name,
                    "description": db_scenario.description or "",
                    "category": db_scenario.category or "",
                    "meta": db_scenario.meta or {},  # Meta 信息：tags, capabilities, keywords 等
                    "system_prompt": db_scenario.system_prompt or "",
                    "is_public": db_scenario.is_public,
                    "is_default": db_scenario.is_default if hasattr(db_scenario, 'is_default') else False,
                }
                scenarios.append(scenario_dict)
            
            return scenarios
    
    @classmethod
    def get_default_scenario(cls) -> Dict:
        """
        获取默认场景（静态方法，方便调用）
        
        Returns:
            Dict: 默认场景配置
        """
        return DefaultConfig.get_default_scenario()
