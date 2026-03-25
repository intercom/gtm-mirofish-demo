"""
数据模型模块
"""

from .task import TaskManager, TaskStatus
from .project import Project, ProjectStatus, ProjectManager
from .pipeline import (
    PipelineStage,
    FunnelSnapshot,
    ConversionEvent,
    FUNNEL_STAGES,
    default_funnel_stages,
)
from .custom_agent import (
    CustomAgentConfig, CustomAgentManager,
    PersonalityVector, VALID_COMMUNICATION_STYLES,
)

__all__ = [
    'TaskManager', 'TaskStatus',
    'Project', 'ProjectStatus', 'ProjectManager',
    'PipelineStage', 'FunnelSnapshot', 'ConversionEvent',
    'FUNNEL_STAGES', 'default_funnel_stages',
    'CustomAgentConfig', 'CustomAgentManager',
    'PersonalityVector', 'VALID_COMMUNICATION_STYLES',
]

