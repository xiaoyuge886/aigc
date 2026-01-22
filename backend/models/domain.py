"""领域模型定义"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from enum import Enum
from pydantic import BaseModel, Field


class TaskComplexity(str, Enum):
    """任务复杂度"""
    SIMPLE = "simple"      # 简单任务：直接执行
    MEDIUM = "medium"      # 中等任务：需要分解
    COMPLEX = "complex"    # 复杂任务：需要详细规划


class TaskType(str, Enum):
    """任务类型"""
    DATA_ANALYSIS = "data-analysis"
    CODE_REVIEW = "code-review"
    CONTENT_WRITING = "content-writing"
    QUESTION_ANSWERING = "qa"
    GENERAL = "general"


class StepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Step(BaseModel):
    """任务步骤"""
    id: int = Field(..., description="步骤ID")
    name: str = Field(..., description="步骤名称")
    description: str = Field(..., description="步骤描述")
    agent: Optional[str] = Field(None, description="使用的Agent")
    skills: List[str] = Field(default_factory=list, description="需要的Skills")
    tools: List[str] = Field(default_factory=list, description="需要的Tools")
    dependencies: List[int] = Field(default_factory=list, description="依赖的步骤ID")
    estimated_time: Optional[int] = Field(None, description="预估时间（秒）")

    # 执行状态
    status: StepStatus = Field(default=StepStatus.PENDING, description="步骤状态")
    result: Optional[str] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class TaskPlan(BaseModel):
    """任务执行计划"""
    task_id: str = Field(..., description="任务ID")
    task_description: str = Field(..., description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    complexity: TaskComplexity = Field(..., description="任务复杂度")

    # 执行步骤
    steps: List[Step] = Field(default_factory=list, description="执行步骤")

    # 推荐配置
    suggested_agents: List[str] = Field(default_factory=list, description="推荐的Agents")
    suggested_skills: List[str] = Field(default_factory=list, description="推荐的Skills")
    suggested_model: Optional[str] = Field(None, description="推荐的模型")

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    estimated_duration: Optional[int] = Field(None, description="预估总时长（秒）")
    estimated_cost: Optional[float] = Field(None, description="预估成本（USD）")

    def get_next_step(self) -> Optional[Step]:
        """获取下一个待执行的步骤"""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # 检查依赖是否完成
                dependencies_met = all(
                    self.steps[dep_id - 1].status == StepStatus.COMPLETED
                    for dep_id in step.dependencies
                )
                if dependencies_met:
                    return step
        return None

    def get_pending_steps(self) -> List[Step]:
        """获取所有待执行的步骤"""
        return [step for step in self.steps if step.status == StepStatus.PENDING]

    def is_completed(self) -> bool:
        """检查计划是否完成"""
        return all(
            step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
            for step in self.steps
        )

    def get_progress(self) -> float:
        """获取进度百分比"""
        if not self.steps:
            return 0.0
        completed = sum(
            1 for step in self.steps
            if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
        )
        return completed / len(self.steps)


class TaskAnalysis(BaseModel):
    """任务分析结果"""
    task_description: str = Field(..., description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    complexity: TaskComplexity = Field(..., description="任务复杂度")
    requires_breakdown: bool = Field(default=False, description="是否需要分解")
    suggested_steps: List[str] = Field(default_factory=list, description="建议的步骤")
    confidence: float = Field(default=0.0, description="分析置信度（0-1）")
    reasoning: str = Field(default="", description="分析推理过程")


class ExecutionResult(BaseModel):
    """执行结果"""
    task_id: str = Field(..., description="任务ID")
    success: bool = Field(..., description="是否成功")
    result: str = Field(default="", description="执行结果")
    steps_taken: List[Step] = Field(default_factory=list, description="执行的步骤")
    duration_seconds: int = Field(default=0, description="耗时（秒）")
    cost_usd: float = Field(default=0.0, description="成本（USD）")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
