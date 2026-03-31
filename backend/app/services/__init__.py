"""
业务服务模块

Uses resilient imports to handle modules that may have incomplete code
from batch generation runs.
"""

import importlib
import logging

logger = logging.getLogger(__name__)

# Track successfully imported names for __all__
_exported = []


def _try_import(module_name, names):
    """Try importing names from a submodule, skip silently on failure."""
    global _exported
    try:
        mod = importlib.import_module(f'.{module_name}', __package__)
        result = {}
        for name in names:
            obj = getattr(mod, name, None)
            if obj is not None:
                result[name] = obj
                _exported.append(name)
            else:
                logger.debug(f"Name {name!r} not found in services.{module_name}")
        return result
    except Exception as e:
        logger.debug(f"Could not import services.{module_name}: {e}")
        return {}


# Core services — import directly (these must work)
from .ontology_generator import OntologyGenerator
from .graph_builder import GraphBuilderService
from .text_processor import TextProcessor
from .simulation_manager import SimulationManager, SimulationState, SimulationStatus

_exported.extend([
    'OntologyGenerator', 'GraphBuilderService', 'TextProcessor',
    'SimulationManager', 'SimulationState', 'SimulationStatus',
])

# Services that may have incomplete code from batch generation
_optional_imports = [
    ('zep_entity_reader', ['ZepEntityReader', 'EntityNode', 'FilteredEntities']),
    ('oasis_profile_generator', ['OasisProfileGenerator', 'OasisAgentProfile']),
    ('simulation_config_generator', [
        'SimulationConfigGenerator', 'SimulationParameters',
        'AgentActivityConfig', 'TimeSimulationConfig', 'EventConfig', 'PlatformConfig',
    ]),
    ('simulation_runner', [
        'SimulationRunner', 'SimulationRunState', 'RunnerStatus',
        'AgentAction', 'RoundSummary',
    ]),
    ('zep_client', ['get_zep_client', 'is_zep_available', 'require_zep_client', 'reset_client']),
    ('zep_graph_memory_updater', ['ZepGraphMemoryUpdater', 'ZepGraphMemoryManager', 'AgentActivity']),
    ('zep_entity_extractor', ['EntityExtractor', 'ExtractedEntity', 'EntityMap']),
    ('zep_graph_memory', [
        'GraphMemoryService', 'GraphQueryResult', 'EntityRelationship',
        'CommunitySummary', 'TemporalFact',
    ]),
    ('simulation_ipc', [
        'SimulationIPCClient', 'SimulationIPCServer',
        'IPCCommand', 'IPCResponse', 'CommandType', 'CommandStatus',
    ]),
    ('oasis_environment', [
        'EnvironmentManager', 'EnvironmentState', 'EnvironmentType', 'EnvironmentStatus',
    ]),
    ('memory_consolidation', ['MemoryConsolidator', 'Memory', 'MemoryType']),
    ('reasoning_parser', [
        'ReasoningParser', 'ParsedReasoning', 'ReasoningStep', 'LogicLink', 'StepType',
    ]),
    ('coalition_labeler', ['CoalitionLabeler', 'Coalition']),
    ('debate_scorer', [
        'DebateScorer', 'DebateScorecard', 'AgentPerformance', 'ArgumentScore', 'DebateFormat',
    ]),
    ('agent_prompts', [
        'AgentPromptModifier', 'AgentPromptContext', 'PersonalityVector', 'AgentContext',
        'build_augmented_prompt', 'build_memory_section', 'build_demo_prompt', 'rank_memories',
    ]),
    ('scenario_templates', ['ScenarioTemplateService', 'ScenarioTemplate']),
    ('whatif_engine', [
        'WhatIfEngine', 'ScenarioConfig', 'SimulationResults', 'ComparisonResult',
        'SensitivityResult', 'Modification', 'ModificationType', 'ScenarioStatus',
    ]),
    ('cpq_data_generator', ['CpqDataGenerator']),
    ('otc_data_generator', ['OTCDataGenerator']),
    ('campaign_generator', ['get_campaigns']),
    ('revenue_data_generator', ['RevenueDataGenerator']),
    ('agent_intelligence', ['AgentIntelligence']),
    ('coalition_detector', ['CoalitionDetector']),
    ('sensitivity_analyzer', ['SensitivityAnalyzer']),
    ('activity_feed', ['ActivityFeedService', 'ACTIVITY_TYPES']),
    ('interaction_graph', ['InteractionGraphBuilder']),
    ('sentiment_dynamics', ['SentimentDynamics', 'AgentSentimentState']),
    ('agent_memory', ['AgentMemory', 'MemoryMessage', 'MemorySearchResult']),
]

# Perform imports, injecting into module namespace
for _mod_name, _names in _optional_imports:
    _imported = _try_import(_mod_name, _names)
    globals().update(_imported)

__all__ = list(_exported)
