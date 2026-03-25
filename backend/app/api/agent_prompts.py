"""
Agent Prompts API
Build memory-augmented prompts for simulation agents.
"""

from flask import Blueprint, jsonify, request

from ..utils.logger import get_logger
from ..services.agent_prompts import (
    AgentContext,
    Memory,
    build_augmented_prompt,
    build_demo_prompt,
    build_memory_section,
    rank_memories,
    DEFAULT_TOP_K,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_MEMORY_BUDGET_RATIO,
)

logger = get_logger('mirofish.api.agent_prompts')

agent_prompts_bp = Blueprint('agent_prompts', __name__, url_prefix='/api/v1/agent-prompts')


@agent_prompts_bp.route('/build', methods=['POST'])
def build_prompt():
    """
    Build a memory-augmented agent prompt.

    Accepts agent context (persona, memories, beliefs, relationships)
    and returns a composed prompt with memory injection within token budget.

    Body (JSON):
        agent_id:           str, required
        agent_name:         str, required
        persona:            str, optional — agent persona description
        base_system_prompt: str, optional — base instructions to prepend
        discussion_context: str, optional — current discussion for relevance ranking
        current_round:      int, optional (default 0)
        top_k:              int, optional (default 10)
        context_window:     int, optional (default 8192)
        budget_ratio:       float, optional (default 0.30)
        memories:           list of {content, round_created, importance, category, source}
        beliefs:            dict of {topic: stance}
        facts:              list of str
        relationships:      dict of {agent_name: description}
    """
    data = request.get_json(silent=True) or {}

    agent_id = data.get('agent_id')
    agent_name = data.get('agent_name')
    if not agent_id or not agent_name:
        return jsonify({'error': 'agent_id and agent_name are required'}), 400

    # Parse memories
    raw_memories = data.get('memories', [])
    memories = []
    for m in raw_memories:
        if not isinstance(m, dict) or 'content' not in m:
            continue
        memories.append(Memory(
            content=m['content'],
            round_created=m.get('round_created', 0),
            importance=m.get('importance', 5.0),
            category=m.get('category', 'observation'),
            source=m.get('source'),
        ))

    current_round = data.get('current_round', 0)
    top_k = data.get('top_k', DEFAULT_TOP_K)
    context_window = data.get('context_window', DEFAULT_CONTEXT_WINDOW)
    budget_ratio = data.get('budget_ratio', DEFAULT_MEMORY_BUDGET_RATIO)
    discussion_context = data.get('discussion_context', '')

    context = AgentContext(
        agent_id=agent_id,
        agent_name=agent_name,
        persona=data.get('persona', ''),
        beliefs=data.get('beliefs', {}),
        facts=data.get('facts', []),
        relationships=data.get('relationships', {}),
        memories=memories,
        current_round=current_round,
    )

    ranked = rank_memories(memories, current_round, discussion_context, top_k)
    prompt = build_augmented_prompt(
        context,
        base_system_prompt=data.get('base_system_prompt', ''),
        discussion_context=discussion_context,
        top_k=top_k,
        context_window=context_window,
        budget_ratio=budget_ratio,
    )

    from ..services.agent_prompts import _estimate_tokens

    return jsonify({
        'prompt': prompt,
        'metadata': {
            'agent_id': agent_id,
            'agent_name': agent_name,
            'memories_injected': len(ranked),
            'beliefs_count': len(context.beliefs),
            'facts_count': len(context.facts),
            'relationships_count': len(context.relationships),
            'current_round': current_round,
            'token_budget': int(context_window * budget_ratio),
            'estimated_tokens': _estimate_tokens(prompt),
        },
    })


@agent_prompts_bp.route('/build/demo', methods=['POST'])
def build_demo():
    """
    Build a memory-augmented prompt using demo data.

    Useful when no real simulation/Zep data is available.

    Body (JSON):
        agent_id:           str, required
        agent_name:         str, required
        persona:            str, optional
        discussion_context: str, optional
        current_round:      int, optional (default 5)
        top_k:              int, optional (default 10)
        context_window:     int, optional (default 8192)
        budget_ratio:       float, optional (default 0.30)
    """
    data = request.get_json(silent=True) or {}

    agent_id = data.get('agent_id')
    agent_name = data.get('agent_name')
    if not agent_id or not agent_name:
        return jsonify({'error': 'agent_id and agent_name are required'}), 400

    result = build_demo_prompt(
        agent_id=agent_id,
        agent_name=agent_name,
        persona=data.get('persona', ''),
        discussion_context=data.get('discussion_context', ''),
        current_round=data.get('current_round', 5),
        top_k=data.get('top_k', DEFAULT_TOP_K),
        context_window=data.get('context_window', DEFAULT_CONTEXT_WINDOW),
        budget_ratio=data.get('budget_ratio', DEFAULT_MEMORY_BUDGET_RATIO),
    )

    return jsonify(result)


@agent_prompts_bp.route('/rank-memories', methods=['POST'])
def rank_memories_endpoint():
    """
    Rank a set of memories by relevance to a discussion context.

    Body (JSON):
        memories:           list of {content, round_created, importance, category}
        current_round:      int, required
        discussion_context: str, optional
        top_k:              int, optional (default 10)
    """
    data = request.get_json(silent=True) or {}

    current_round = data.get('current_round', 0)
    discussion_context = data.get('discussion_context', '')
    top_k = data.get('top_k', DEFAULT_TOP_K)

    raw_memories = data.get('memories', [])
    if not raw_memories:
        return jsonify({'error': 'memories list is required'}), 400

    memories = []
    for m in raw_memories:
        if not isinstance(m, dict) or 'content' not in m:
            continue
        memories.append(Memory(
            content=m['content'],
            round_created=m.get('round_created', 0),
            importance=m.get('importance', 5.0),
            category=m.get('category', 'observation'),
            source=m.get('source'),
        ))

    ranked = rank_memories(memories, current_round, discussion_context, top_k)

    return jsonify({
        'ranked_memories': [
            {
                'content': m.content,
                'round_created': m.round_created,
                'category': m.category,
                'importance': m.importance,
                'effective_importance': round(m.effective_importance(current_round), 2),
            }
            for m in ranked
        ],
        'total_input': len(memories),
        'returned': len(ranked),
    })
