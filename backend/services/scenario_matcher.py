"""
场景匹配器 - 使用模型能力根据用户输入自动匹配场景

核心设计原则：
- 充分依赖模型规划能力：使用模型智能分析用户需求，选择最合适的场景
- 不硬编码匹配规则：让模型根据场景的完整信息（名称、描述、meta信息）进行判断

核心功能：
1. 获取用户可用的场景列表（管理员配置的场景）
2. 使用模型分析用户输入和场景信息，智能选择最合适的场景
3. 返回模型选择的场景（只返回一个）
"""
from typing import Optional, List, Dict
import json
import hashlib
from loguru import logger
from services.scenario_provider import ScenarioProvider
from services.database import DatabaseService
from services.agent_service import AgentService
from services.default_config import DefaultConfig
from claude_agent_sdk import ClaudeAgentOptions


class ScenarioMatcher:
    """场景匹配器 - 使用模型能力进行智能匹配"""
    
    # 类级别的缓存（简单的内存缓存，可以后续改为 Redis）
    _match_cache: Dict[str, Dict] = {}
    _cache_max_size = 100  # 最多缓存100个匹配结果
    
    def __init__(self, db_service: DatabaseService, agent_service: Optional[AgentService] = None):
        self.db_service = db_service
        self.scenario_provider = ScenarioProvider(db_service)
        self.agent_service = agent_service
    
    def _get_cache_key(self, user_query: str, user_id: Optional[int], available_scenarios: List[Dict]) -> str:
        """生成缓存键"""
        # 使用用户查询、用户ID和场景列表的hash作为缓存键
        scenarios_hash = hashlib.md5(
            json.dumps([s.get("id") for s in available_scenarios], sort_keys=True).encode()
        ).hexdigest()[:8]
        query_hash = hashlib.md5(user_query.encode()).hexdigest()[:8]
        return f"match_{user_id}_{query_hash}_{scenarios_hash}"
    
    async def match_scenario(
        self,
        user_query: str,
        user_id: Optional[int] = None,
        agent_service: Optional[AgentService] = None
    ) -> Optional[Dict]:
        """
        根据用户输入匹配场景（使用模型能力）
        
        匹配策略：
        1. 获取用户可用的场景列表（管理员配置的场景）
        2. 使用模型分析用户输入和场景信息，智能选择最合适的场景
        3. 返回模型选择的场景（只返回一个）
        
        优化：
        - 使用缓存机制，避免重复匹配相同的查询
        - 优化场景信息格式化，减少 token 消耗
        - 改进场景ID提取逻辑，提高准确性
        
        Args:
            user_query: 用户输入
            user_id: 用户ID（可选）
            agent_service: Agent服务（用于调用模型，可选）
            
        Returns:
            Optional[Dict]: 匹配的场景，如果没有匹配则返回 None
        """
        # 1. 获取用户可用的场景列表
        available_scenarios = await self.scenario_provider.get_available_scenarios(user_id=user_id)
        
        # 检查缓存（如果场景列表没有变化，可以复用之前的匹配结果）
        cache_key = self._get_cache_key(user_query, user_id, available_scenarios)
        if cache_key in self._match_cache:
            cached_result = self._match_cache[cache_key]
            logger.debug(f"[ScenarioMatcher] 使用缓存匹配结果: id={cached_result.get('id')}")
            return cached_result
        
        if not available_scenarios or len(available_scenarios) == 0:
            logger.debug("[ScenarioMatcher] 用户没有可用场景，返回默认场景")
            # 从数据库读取默认场景（如果数据库中没有，会返回硬编码的 DEFAULT_SCENARIO）
            if self.agent_service and hasattr(self.agent_service, 'db_service'):
                return await DefaultConfig.get_default_scenario_from_db(self.agent_service.db_service)
            return DefaultConfig.get_default_scenario()
        
        # 2. 分离默认场景和其他场景
        default_scenario = None
        other_scenarios = []
        
        for s in available_scenarios:
            # 检查是否是默认场景：scenario_id == "default" 或 is_default == True
            if s.get("scenario_id") == "default" or s.get("is_default"):
                default_scenario = s
            else:
                other_scenarios.append(s)
        
        # 如果没有其他场景，返回默认场景
        if not other_scenarios:
            logger.debug("[ScenarioMatcher] 只有默认场景，返回默认场景")
            # 如果没有找到默认场景，从数据库读取（如果数据库中没有，会返回硬编码的 DEFAULT_SCENARIO）
            if not default_scenario:
                if self.agent_service and hasattr(self.agent_service, 'db_service'):
                    return await DefaultConfig.get_default_scenario_from_db(self.agent_service.db_service)
                return DefaultConfig.get_default_scenario()
            return default_scenario
        
        # 如果只有一个场景（且不是默认场景），直接返回
        if len(other_scenarios) == 1:
            logger.info(f"[ScenarioMatcher] ✅ 只有一个可用场景，直接返回: {other_scenarios[0].get('name')}")
            return other_scenarios[0]
        
        # 3. 使用模型能力选择场景
        agent_service_to_use = agent_service or self.agent_service
        if not agent_service_to_use:
            logger.warning("[ScenarioMatcher] 没有提供 AgentService，无法使用模型匹配，返回默认场景")
            # 如果没有找到默认场景，从数据库读取（如果数据库中没有，会返回硬编码的 DEFAULT_SCENARIO）
            if not default_scenario:
                if self.agent_service and hasattr(self.agent_service, 'db_service'):
                    return await DefaultConfig.get_default_scenario_from_db(self.agent_service.db_service)
                return DefaultConfig.get_default_scenario()
            return default_scenario
        
        try:
            matched_scenario = await self._match_with_model(
                user_query, 
                other_scenarios,  # 只让模型从非默认场景中选择
                agent_service_to_use
            )
            
            if matched_scenario:
                scenario_name = matched_scenario.get('name', '未知场景')
                scenario_id = matched_scenario.get('id', '未知ID')
                logger.info(
                    f"[ScenarioMatcher] ✅ 模型匹配到场景: {scenario_name} "
                    f"(id: {scenario_id})"
                )
                logger.debug(
                    f"[ScenarioMatcher] 匹配场景详情: "
                    f"描述={matched_scenario.get('description', '')[:50]}..., "
                    f"分类={matched_scenario.get('category', '无')}, "
                    f"meta={matched_scenario.get('meta', {})}"
                )
                # 缓存匹配结果
                if len(self._match_cache) >= self._cache_max_size:
                    # 如果缓存已满，删除最旧的条目（简单策略：清空一半）
                    keys_to_remove = list(self._match_cache.keys())[:self._cache_max_size // 2]
                    for key in keys_to_remove:
                        del self._match_cache[key]
                self._match_cache[cache_key] = matched_scenario
                return matched_scenario
            else:
                # 如果模型没有匹配到场景，返回默认场景
                logger.info("[ScenarioMatcher] 模型未匹配到场景，返回默认场景")
                # 如果没有找到默认场景，从数据库读取（如果数据库中没有，会返回硬编码的 DEFAULT_SCENARIO）
                if not default_scenario:
                    if self.agent_service and hasattr(self.agent_service, 'db_service'):
                        return await DefaultConfig.get_default_scenario_from_db(self.agent_service.db_service)
                    return DefaultConfig.get_default_scenario()
                return default_scenario
        except Exception as e:
            logger.error(f"[ScenarioMatcher] 模型匹配场景失败: {e}，返回默认场景", exc_info=True)
            # 如果没有找到默认场景，从数据库读取（如果数据库中没有，会返回硬编码的 DEFAULT_SCENARIO）
            if not default_scenario:
                if self.agent_service and hasattr(self.agent_service, 'db_service'):
                    return await DefaultConfig.get_default_scenario_from_db(self.agent_service.db_service)
                return DefaultConfig.get_default_scenario()
            return default_scenario
    
    async def _match_with_model(
        self,
        user_query: str,
        available_scenarios: List[Dict],
        agent_service: AgentService
    ) -> Optional[Dict]:
        """
        使用模型能力匹配场景
        
        Args:
            user_query: 用户输入
            available_scenarios: 可用场景列表
            agent_service: Agent服务
            
        Returns:
            Optional[Dict]: 匹配的场景
        """
        # 构建场景选择 prompt
        scenarios_info = self._format_scenarios_for_model(available_scenarios)
        
        logger.debug(f"[ScenarioMatcher] 格式化后的场景信息:\n{scenarios_info}")
        
        selection_prompt = f"""你是一个智能场景选择助手。根据用户输入，从可用场景中选择最合适的一个场景。

## 用户输入
{user_query}

## 可用场景列表
{scenarios_info}

## 选择规则
1. **优先匹配**：根据用户输入的关键词、意图和场景的标签、关键词、能力进行匹配
2. **精确匹配**：如果用户需求明确对应某个场景的能力，选择该场景
3. **模糊匹配**：如果用户需求与多个场景相关，选择最相关的场景
4. **默认场景**：如果用户需求是通用对话或无法匹配任何场景，返回默认场景的ID

## 输出格式
**必须严格按照以下格式输出，只返回一行：**
id: <场景ID（整数）>

示例：
- 如果选择场景1（id: 1）：id: 1
- 如果选择场景2（id: 2）：id: 2
- 如果没有合适场景，选择默认场景（id: 3）：id: 3

现在请分析用户输入并选择最合适的场景："""
        
        logger.debug(f"[ScenarioMatcher] 场景选择 prompt 长度: {len(selection_prompt)}")
        
        try:
            # 使用模型进行场景选择
            system_prompt = """你是一个专业的场景选择助手，擅长根据用户需求选择最合适的场景。

**重要规则**：
1. 仔细分析用户输入的关键词和意图
2. 对比每个场景的标签、关键词、能力和描述
3. 选择最匹配的场景，如果没有明确匹配则返回 default
4. **必须严格按照格式输出**：id: <场景ID（整数）>
5. 只返回一行，不要添加任何其他内容"""
            
            # 调用模型（query_once 返回异步迭代器）
            response_text = ""
            from models.schemas import AssistantMessage
            
            # 🔧 修复：场景匹配时禁用 can_use_tool callback，避免流式模式要求
            # 创建一个不包含 security callback 的临时 options
            from claude_agent_sdk import ClaudeAgentOptions
            temp_options = ClaudeAgentOptions(
                system_prompt=system_prompt,
                model="sonnet",  # 使用快速模型进行场景选择
                # 不设置 can_use_tool，避免流式模式要求
            )
            
            # 直接使用 query() 函数，而不是 query_once（避免 security callback）
            from claude_agent_sdk import query, AssistantMessage as SDKAssistantMessage, TextBlock
            
            try:
                async for sdk_message in query(prompt=selection_prompt, options=temp_options):
                    # Process SDK message structure correctly
                    # SDKAssistantMessage has content attribute which is a list containing TextBlock objects
                    if isinstance(sdk_message, SDKAssistantMessage):
                        if hasattr(sdk_message, 'content') and sdk_message.content:
                            for block in sdk_message.content:
                                if isinstance(block, TextBlock):
                                    if hasattr(block, 'text') and block.text:
                                        # Skip error messages
                                        if "API Error" not in block.text and "Error:" not in block.text:
                                            response_text += block.text
            except Exception as e:
                logger.error(f"[ScenarioMatcher] query() 调用失败: {e}", exc_info=True)
                return None
            
            # Parse scenario ID from model response
            if response_text:
                scenario_id = self._extract_scenario_id(response_text)
                logger.debug(f"[ScenarioMatcher] Extracted scenario ID: {scenario_id}")
                
                if scenario_id and str(scenario_id).lower() != "none":
                    # Find matching scenario (supports integer and string ID conversion)
                    for scenario in available_scenarios:
                        scenario_id_int = scenario.get("id")
                        scenario_name = scenario.get("name", "Unknown")
                        logger.debug(f"[ScenarioMatcher] Comparing scenario: {scenario_name} (id: {scenario_id_int}) vs extracted ID: {scenario_id}")
                        # Support integer ID matching
                        if scenario_id_int is not None and (scenario_id_int == scenario_id or str(scenario_id_int) == str(scenario_id)):
                            logger.info(f"[ScenarioMatcher] Matched scenario: {scenario_name} (id: {scenario_id_int})")
                            return scenario
                    
                    logger.warning(f"[ScenarioMatcher] Scenario ID from model not found: {scenario_id}, available IDs: {[s.get('id') for s in available_scenarios]}")
                else:
                    logger.debug(f"[ScenarioMatcher] Model determined no suitable scenario (extracted ID: {scenario_id}), returning None")
            else:
                logger.warning("[ScenarioMatcher] Model returned no response text")
            
            # 返回 None，让调用方决定是否使用默认场景
            return None
            
        except Exception as e:
            logger.error(f"[ScenarioMatcher] 模型调用失败: {e}", exc_info=True)
            return None
    
    def _format_scenarios_for_model(self, scenarios: List[Dict]) -> str:
        """
        格式化场景信息供模型分析（优化版：更简洁，减少 token 消耗）
        
        Args:
            scenarios: 场景列表
            
        Returns:
            str: 格式化后的场景信息
        """
        formatted = []
        for i, scenario in enumerate(scenarios, 1):
            scenario_id = scenario.get("id", "")
            name = scenario.get("name", "")
            description = scenario.get("description", "") or ""
            category = scenario.get("category", "") or ""
            meta = scenario.get("meta", {}) or {}
            
            # 构建场景信息（更紧凑的格式）
            parts = [f"场景{i}: {name} (id: {scenario_id})"]
            
            if description:
                # 限制描述长度，避免过长
                desc = description[:100] + "..." if len(description) > 100 else description
                parts.append(f"描述: {desc}")
            
            if category:
                parts.append(f"分类: {category}")
            
            # 添加 meta 信息（标签、关键词、能力）
            meta_parts = []
            if isinstance(meta, dict):
                # 标签
                if meta.get("tags"):
                    tags = meta.get("tags")
                    if isinstance(tags, list):
                        tags_str = ",".join(str(t) for t in tags[:5])  # 最多5个标签
                    else:
                        tags_str = str(tags)
                    meta_parts.append(f"标签:{tags_str}")
                
                # 关键词（最重要，用于匹配）
                if meta.get("keywords"):
                    keywords = meta.get("keywords")
                    if isinstance(keywords, list):
                        keywords_str = ",".join(str(k) for k in keywords[:10])  # 最多10个关键词
                    else:
                        keywords_str = str(keywords)
                    meta_parts.append(f"关键词:{keywords_str}")
                
                # 能力
                if meta.get("capabilities"):
                    capabilities = meta.get("capabilities")
                    if isinstance(capabilities, list):
                        cap_str = ",".join(str(c) for c in capabilities[:5])  # 最多5个能力
                    else:
                        cap_str = str(capabilities)
                    meta_parts.append(f"能力:{cap_str}")
            
            if meta_parts:
                parts.append("|".join(meta_parts))
            
            formatted.append(" | ".join(parts))
        
        return "\n".join(formatted)
    
    def _extract_scenario_id(self, response_text: str) -> Optional[int]:
        """
        从模型响应中提取场景ID（整数）
        
        Args:
            response_text: 模型响应文本
            
        Returns:
            Optional[int]: 提取的场景ID（整数），如果提取失败则返回None
        """
        if not response_text:
            return None
        
        # 清理响应文本
        response_text = response_text.strip()
        
        # 方法1：查找 "id:" 后面的内容（优先，支持整数）
        import re
        pattern1 = r'id\s*:\s*(\d+)'
        match1 = re.search(pattern1, response_text, re.IGNORECASE)
        if match1:
            try:
                scenario_id = int(match1.group(1).strip())
                if scenario_id > 0:
                    return scenario_id
            except ValueError:
                pass
        
        # 方法2：查找 "scenario_id:" 后面的内容（向后兼容）
        pattern2 = r'scenario_id\s*:\s*([^\s,;:!?\.\n]+)'
        match2 = re.search(pattern2, response_text, re.IGNORECASE)
        if match2:
            scenario_id_str = match2.group(1).strip().strip("'\"")
            # 尝试转换为整数
            try:
                scenario_id = int(scenario_id_str)
                if scenario_id > 0:
                    return scenario_id
            except ValueError:
                # 如果不是整数，可能是旧的字符串ID，返回None让调用方处理
                pass
        
        # 方法3：查找 "id:" 后面的内容（兼容格式）
        if "id:" in response_text.lower():
            parts = response_text.lower().split("id:", 1)
            if len(parts) > 1:
                scenario_id_str = parts[1].strip().split()[0] if parts[1].strip().split() else parts[1].strip()
                scenario_id_str = scenario_id_str.strip(".,;:!?\"'\n\r")
                try:
                    scenario_id = int(scenario_id_str)
                    if scenario_id > 0:
                        return scenario_id
                except ValueError:
                    pass
        
        # 方法3：尝试提取第一行非空内容（可能是纯ID）
        lines = response_text.split("\n")
        for line in lines:
            cleaned = line.strip()
            if cleaned and cleaned.lower() != "none":
                # 移除可能的标点符号
                cleaned = cleaned.strip(".,;:!?\"'")
                if cleaned and len(cleaned) < 50:  # 场景ID通常不会太长
                    return cleaned
        
        return None
