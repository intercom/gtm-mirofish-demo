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
from .salesforce import Account, Opportunity, Contact, Lead
from .cpq import (
    Product, PriceBookEntry, Quote, QuoteLine,
    QuoteStatus, BillingFrequency,
    INTERCOM_PRODUCTS, INTERCOM_PRICEBOOK,
    generate_demo_quotes,
)
from .revenue import (
    RevenueMetric, CustomerRevenue, ChurnEvent, ExpansionEvent,
    ExpansionType, ChurnReason, PlanTier,
)
from .order_to_cash import (
    Order, OrderStatus,
    ProvisioningStep, ProvisioningStatus,
    BillingRecord, BillingStatus,
    ValidationResult, ValidationStatus,
)
from .reconciliation import (
    ReconciliationRecord,
    ReconciliationRun,
    ReconciliationRule,
    ReconciliationStatus,
    DiscrepancyType,
    RuleAction,
    RuleCheckType,
)

__all__ = [
    'TaskManager', 'TaskStatus',
    'Project', 'ProjectStatus', 'ProjectManager',
    'PipelineStage', 'FunnelSnapshot', 'ConversionEvent',
    'FUNNEL_STAGES', 'default_funnel_stages',
    'CustomAgentConfig', 'CustomAgentManager',
    'PersonalityVector', 'VALID_COMMUNICATION_STYLES',
    'Account', 'Opportunity', 'Contact', 'Lead',
    'Product', 'PriceBookEntry', 'Quote', 'QuoteLine',
    'QuoteStatus', 'BillingFrequency',
    'INTERCOM_PRODUCTS', 'INTERCOM_PRICEBOOK',
    'generate_demo_quotes',
    'RevenueMetric', 'CustomerRevenue', 'ChurnEvent', 'ExpansionEvent',
    'ExpansionType', 'ChurnReason', 'PlanTier',
    'Order', 'OrderStatus',
    'ProvisioningStep', 'ProvisioningStatus',
    'BillingRecord', 'BillingStatus',
    'ValidationResult', 'ValidationStatus',
    'ReconciliationRecord', 'ReconciliationRun', 'ReconciliationRule',
    'ReconciliationStatus', 'DiscrepancyType', 'RuleAction', 'RuleCheckType',
]
