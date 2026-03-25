"""
数据模型模块
"""

from .task import TaskManager, TaskStatus
from .project import Project, ProjectStatus, ProjectManager
from .report_builder import (
    ReportTemplate,
    ReportSection,
    GeneratedReport,
    ReportBuilderManager,
    SectionType,
    SectionWidth,
    GenerationMethod,
)

__all__ = [
    'TaskManager', 'TaskStatus',
    'Project', 'ProjectStatus', 'ProjectManager',
    'ReportTemplate', 'ReportSection', 'GeneratedReport',
    'ReportBuilderManager', 'SectionType', 'SectionWidth', 'GenerationMethod',
]

