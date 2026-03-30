"""
业务服务模块
"""

from .ontology_generator import OntologyGenerator
from .graph_builder import GraphBuilderService
from .text_processor import TextProcessor
from .zep_entity_reader import ZepEntityReader, EntityNode, FilteredEntities
from .oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from .simulation_manager import SimulationManager, SimulationState, SimulationStatus
from .simulation_config_generator import (
    SimulationConfigGenerator,
    SimulationParameters,
    AgentActivityConfig,
    TimeSimulationConfig,
    EventConfig,
    PlatformConfig
)
from .simulation_runner import (
    SimulationRunner,
    SimulationRunState,
    RunnerStatus,
    AgentAction,
    RoundSummary
)
from .zep_client import get_zep_client, is_zep_available, require_zep_client, reset_client
from .zep_graph_memory_updater import (
    ZepGraphMemoryUpdater,
    ZepGraphMemoryManager,
    AgentActivity
)
from .zep_entity_extractor import EntityExtractor, ExtractedEntity, EntityMap
from .zep_graph_memory import (
    GraphMemoryService,
    GraphQueryResult,
    EntityRelationship,
    CommunitySummary,
    TemporalFact,
)
from .simulation_ipc import (
    SimulationIPCClient,
    SimulationIPCServer,
    IPCCommand,
    IPCResponse,
    CommandType,
    CommandStatus
)
from .oasis_environment import (
    EnvironmentManager,
    EnvironmentState,
    EnvironmentType,
    EnvironmentStatus,
)
from .memory_consolidation import (
    MemoryConsolidator,
    Memory,
    MemoryType,
)
from .reasoning_parser import (
    ReasoningParser,
    ParsedReasoning,
    ReasoningStep,
    LogicLink,
    StepType
)
from .scenario_templates import (
    ScenarioTemplateService,
    ScenarioTemplate,
    AgentConfig as ScenarioAgentConfig,
)
from .whatif_engine import (
    WhatIfEngine,
    ScenarioConfig,
    SimulationResults,
    ComparisonResult,
    SensitivityResult,
    Modification,
    ModificationType,
    ScenarioStatus,
)

# Non-essential service imports — wrapped in try/except to tolerate
# broken modules from parallel PRD execution without blocking app startup.
import logging as _logging

_log = _logging.getLogger(__name__)

_optional_imports = {
    'coalition_labeler': lambda: __import__('app.services.coalition_labeler', fromlist=['CoalitionLabeler', 'Coalition']),
    'debate_scorer': lambda: __import__('app.services.debate_scorer', fromlist=['DebateScorer']),
    'agent_prompts': lambda: __import__('app.services.agent_prompts', fromlist=['AgentPromptModifier']),
    'cpq_data_generator': lambda: __import__('app.services.cpq_data_generator', fromlist=['CpqDataGenerator']),
    'otc_data_generator': lambda: __import__('app.services.otc_data_generator', fromlist=['OTCDataGenerator']),
    'campaign_generator': lambda: __import__('app.services.campaign_generator', fromlist=['generate_campaigns']),
    'revenue_data_generator': lambda: __import__('app.services.revenue_data_generator', fromlist=['RevenueDataGenerator']),
    'agent_intelligence': lambda: __import__('app.services.agent_intelligence', fromlist=['AgentIntelligence']),
    'coalition_detector': lambda: __import__('app.services.coalition_detector', fromlist=['CoalitionDetector']),
    'sensitivity_analyzer': lambda: __import__('app.services.sensitivity_analyzer', fromlist=['SensitivityAnalyzer']),
    'activity_feed': lambda: __import__('app.services.activity_feed', fromlist=['ActivityFeedService']),
    'interaction_graph': lambda: __import__('app.services.interaction_graph', fromlist=['InteractionGraphBuilder']),
    'sentiment_dynamics': lambda: __import__('app.services.sentiment_dynamics', fromlist=['SentimentDynamics']),
    'agent_memory': lambda: __import__('app.services.agent_memory', fromlist=['AgentMemory']),
}

for _name, _loader in _optional_imports.items():
    try:
        _loader()
    except Exception as _e:
        _log.debug("Optional service %s not available: %s", _name, _e)

# Re-export what successfully imported
try:
    from .coalition_labeler import CoalitionLabeler, Coalition
except Exception:
    pass
try:
    from .debate_scorer import (
        DebateScorer, DebateScorecard, AgentPerformance, ArgumentScore, DebateFormat,
    )
except Exception:
    pass
try:
    from .agent_prompts import (
        AgentPromptModifier, AgentPromptContext, PersonalityVector, AgentContext,
        Memory as AgentMemory, build_augmented_prompt, build_memory_section,
        build_demo_prompt, rank_memories,
    )
except Exception:
    pass
try:
    from .cpq_data_generator import CpqDataGenerator
except Exception:
    pass
try:
    from .otc_data_generator import OTCDataGenerator
except Exception:
    pass
try:
    from .campaign_generator import (
        generate_campaigns, get_campaign_stats, get_roi_comparison, get_budget_efficiency,
    )
except Exception:
    pass
try:
    from .revenue_data_generator import RevenueDataGenerator
except Exception:
    pass
try:
    from .agent_intelligence import AgentIntelligence
except Exception:
    pass
try:
    from .coalition_detector import CoalitionDetector
except Exception:
    pass
try:
    from .sensitivity_analyzer import SensitivityAnalyzer
except Exception:
    pass
try:
    from .activity_feed import ActivityFeedService, ACTIVITY_TYPES
except Exception:
    pass
try:
    from .interaction_graph import InteractionGraphBuilder
except Exception:
    pass
try:
    from .sentiment_dynamics import SentimentDynamics, AgentSentimentState
except Exception:
    pass
try:
    from .agent_memory import AgentMemory as AgentMemoryService, MemoryMessage, MemorySearchResult
except Exception:
    pass
