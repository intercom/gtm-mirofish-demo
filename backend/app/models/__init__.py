"""
数据模型模块
"""

from .task import TaskManager, TaskStatus
from .project import Project, ProjectStatus, ProjectManager
from .cpq import (
    Product, PriceBookEntry, Quote, QuoteLine,
    QuoteStatus, BillingFrequency,
    INTERCOM_PRODUCTS, INTERCOM_PRICEBOOK,
    generate_demo_quotes,
)

__all__ = [
    'TaskManager', 'TaskStatus',
    'Project', 'ProjectStatus', 'ProjectManager',
    'Product', 'PriceBookEntry', 'Quote', 'QuoteLine',
    'QuoteStatus', 'BillingFrequency',
    'INTERCOM_PRODUCTS', 'INTERCOM_PRICEBOOK',
    'generate_demo_quotes',
]

