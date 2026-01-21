"""
统一查询服务接口

提供统一的数据库查询接口，方便后续切换到 MySQL、ES 等数据库
所有数据库查询都应该通过这个服务进行，而不是直接使用 SQLAlchemy
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger


class QueryService(ABC):
    """查询服务抽象基类
    
    所有数据库查询都应该通过这个接口进行，方便后续切换数据库实现
    """
    
    # =========================================================================
    # System Prompt 查询
    # =========================================================================
    
    @abstractmethod
    async def get_default_system_prompt(self) -> Optional[Dict[str, Any]]:
        """获取默认的系统提示词（is_default=True）"""
        pass
    
    @abstractmethod
    async def get_system_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """根据 prompt_id 获取系统提示词"""
        pass
    
    @abstractmethod
    async def list_system_prompts(
        self,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> List[Dict[str, Any]]:
        """列出系统提示词"""
        pass
    
    @abstractmethod
    async def create_system_prompt(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建系统提示词"""
        pass
    
    @abstractmethod
    async def update_system_prompt(self, prompt_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统提示词"""
        pass
    
    @abstractmethod
    async def delete_system_prompt(self, prompt_id: str) -> bool:
        """删除系统提示词"""
        pass
    
    # =========================================================================
    # Skill 查询
    # =========================================================================
    
    @abstractmethod
    async def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """根据 skill_id 获取技能"""
        pass
    
    @abstractmethod
    async def list_skills(
        self,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> List[Dict[str, Any]]:
        """列出技能"""
        pass
    
    @abstractmethod
    async def create_skill(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建技能"""
        pass
    
    @abstractmethod
    async def update_skill(self, skill_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新技能"""
        pass
    
    @abstractmethod
    async def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        pass
    
    # =========================================================================
    # Business Scenario 查询
    # =========================================================================
    
    @abstractmethod
    async def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """根据 scenario_id 获取业务场景"""
        pass
    
    @abstractmethod
    async def list_scenarios(
        self,
        is_public: Optional[bool] = None,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> List[Dict[str, Any]]:
        """列出业务场景"""
        pass
    
    @abstractmethod
    async def create_scenario(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建业务场景"""
        pass
    
    @abstractmethod
    async def update_scenario(self, scenario_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新业务场景"""
        pass
    
    @abstractmethod
    async def delete_scenario(self, scenario_id: str) -> bool:
        """删除业务场景"""
        pass
    
    # =========================================================================
    # Session 查询
    # =========================================================================
    
    @abstractmethod
    async def get_session(self, session_id: str, include_inactive: bool = False) -> Optional[Dict[str, Any]]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def list_sessions(
        self,
        user_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        include_inactive: bool = True,
    ) -> List[Dict[str, Any]]:
        """列出会话"""
        pass
    
    @abstractmethod
    async def count_sessions(self, user_id: Optional[int] = None, include_inactive: bool = True) -> int:
        """统计会话数量"""
        pass
    
    @abstractmethod
    async def create_session(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建会话"""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新会话"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    # =========================================================================
    # Message 查询
    # =========================================================================
    
    @abstractmethod
    async def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        """获取消息"""
        pass
    
    @abstractmethod
    async def list_messages(
        self,
        session_id: str,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出消息"""
        pass
    
    @abstractmethod
    async def count_messages(self, session_id: str) -> int:
        """统计消息数量"""
        pass
    
    @abstractmethod
    async def create_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建消息"""
        pass
    
    @abstractmethod
    async def delete_message(self, message_id: int) -> bool:
        """删除消息"""
        pass
    
    # =========================================================================
    # User 查询
    # =========================================================================
    
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户"""
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根据邮箱获取用户"""
        pass
    
    @abstractmethod
    async def list_users(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出用户"""
        pass
    
    @abstractmethod
    async def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        pass
    
    # =========================================================================
    # User Config 查询
    # =========================================================================
    
    @abstractmethod
    async def get_user_config(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户配置"""
        pass
    
    @abstractmethod
    async def create_user_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户配置"""
        pass
    
    @abstractmethod
    async def update_user_config(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户配置"""
        pass
    
    @abstractmethod
    async def delete_user_config(self, user_id: int) -> bool:
        """删除用户配置"""
        pass
