"""
数据模型模块
"""

from .task import TaskManager, TaskStatus
from .project import Project, ProjectStatus, ProjectManager
from .pipeline import (
    PipelineStage,
    FunnelSnapshot,
    ConversionEvent,
    PIPELINE_STAGES,
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
    Order, OrderStatus, LineItem,
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
from .campaign import (
    Campaign,
    CampaignCostBreakdown,
    CampaignAttribution,
)
from .data_pipeline import (
    SyncJob, SyncStatus, SyncDirection,
    DbtModel, DbtMaterialization, DbtModelStatus,
    DbtTest, DbtTestStatus, DbtTestSeverity,
    DataFreshness,
)
from .report_builder import (
    ReportTemplate,
    ReportSection,
    GeneratedReport,
    ReportBuilderManager,
    SectionType,
    SectionWidth,
    GenerationMethod,
    PageOrientation,
)
from .scenario_template import (
    ScenarioTemplate,
    ScenarioCategory,
    ScenarioDifficulty,
    ScenarioTemplateManager,
)
from .session import Session, SessionStatus, SessionManager

__all__ = [
    'TaskManager', 'TaskStatus',
    'Project', 'ProjectStatus', 'ProjectManager',
    'PipelineStage', 'FunnelSnapshot', 'ConversionEvent',
    'PIPELINE_STAGES',
    'CustomAgentConfig', 'CustomAgentManager',
    'PersonalityVector', 'VALID_COMMUNICATION_STYLES',
    'Account', 'Opportunity', 'Contact', 'Lead',
    'Product', 'PriceBookEntry', 'Quote', 'QuoteLine',
    'QuoteStatus', 'BillingFrequency',
    'INTERCOM_PRODUCTS', 'INTERCOM_PRICEBOOK',
    'generate_demo_quotes',
    'RevenueMetric', 'CustomerRevenue', 'ChurnEvent', 'ExpansionEvent',
    'ExpansionType', 'ChurnReason', 'PlanTier',
    'Order', 'OrderStatus', 'LineItem',
    'ProvisioningStep', 'ProvisioningStatus',
    'BillingRecord', 'BillingStatus',
    'ValidationResult', 'ValidationStatus',
    'ReconciliationRecord', 'ReconciliationRun', 'ReconciliationRule',
    'ReconciliationStatus', 'DiscrepancyType', 'RuleAction', 'RuleCheckType',
    'Campaign', 'CampaignCostBreakdown', 'CampaignAttribution',
    'SyncJob', 'SyncStatus', 'SyncDirection',
    'DbtModel', 'DbtMaterialization', 'DbtModelStatus',
    'DbtTest', 'DbtTestStatus', 'DbtTestSeverity',
    'DataFreshness',
    'ReportTemplate', 'ReportSection', 'GeneratedReport',
    'ReportBuilderManager', 'SectionType', 'SectionWidth',
    'GenerationMethod', 'PageOrientation',
    'ScenarioTemplate', 'ScenarioCategory', 'ScenarioDifficulty', 'ScenarioTemplateManager',
    'Session', 'SessionStatus', 'SessionManager',
]
