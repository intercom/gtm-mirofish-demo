"""
OASIS Metrics Collector

Aggregates and computes derived metrics from simulation run data —
action rates, platform distributions, agent engagement, and per-round trends.
"""

import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.logger import get_logger
from .simulation_runner import SimulationRunner, RunnerStatus

logger = get_logger('mirofish.metrics_collector')


class MetricsCollector:
    """Collects and computes aggregate metrics for an OASIS simulation."""

    # Action types that indicate content creation (vs. passive engagement)
    CONTENT_ACTIONS = {'CREATE_POST', 'REPLY', 'COMMENT', 'CREATE_THREAD'}
    ENGAGEMENT_ACTIONS = {'LIKE', 'LIKE_POST', 'UPVOTE', 'SHARE', 'REPOST'}

    @classmethod
    def collect(cls, simulation_id: str) -> Dict[str, Any]:
        """
        Collect a unified metrics snapshot for a simulation.

        Returns a dict with:
          - summary: high-level counts and rates
          - platform_breakdown: per-platform stats
          - action_distribution: action type counts and percentages
          - agent_leaderboard: top agents by activity
          - round_series: per-round time-series data
          - status: current runner status
        """
        run_state = SimulationRunner.get_run_status(simulation_id)
        if not run_state:
            logger.warning(f"No run state for simulation {simulation_id}")
            return cls._empty_metrics(simulation_id)

        state_dict = run_state.to_dict()
        status = state_dict.get('runner_status', 'idle')
        total_actions = state_dict.get('total_actions_count', 0)
        twitter_count = state_dict.get('twitter_actions_count', 0)
        reddit_count = state_dict.get('reddit_actions_count', 0)
        current_round = state_dict.get('current_round', 0)
        total_rounds = state_dict.get('total_rounds', 0)

        timeline = SimulationRunner.get_timeline(simulation_id)
        agent_stats = SimulationRunner.get_agent_stats(simulation_id)

        action_dist = cls._compute_action_distribution(agent_stats)
        round_series = cls._build_round_series(timeline)
        agent_leaderboard = cls._build_agent_leaderboard(agent_stats)
        rates = cls._compute_rates(timeline, total_actions, current_round)

        return {
            'simulation_id': simulation_id,
            'status': status,
            'collected_at': datetime.now().isoformat(),
            'summary': {
                'total_actions': total_actions,
                'total_rounds': total_rounds,
                'current_round': current_round,
                'progress_percent': state_dict.get('progress_percent', 0),
                'simulated_hours': state_dict.get('simulated_hours', 0),
                'total_simulation_hours': state_dict.get('total_simulation_hours', 0),
                'unique_agents': len(agent_stats),
                'content_actions': rates['content_actions'],
                'engagement_actions': rates['engagement_actions'],
                'actions_per_round': rates['actions_per_round'],
                'started_at': state_dict.get('started_at'),
                'completed_at': state_dict.get('completed_at'),
            },
            'platform_breakdown': {
                'twitter': {
                    'actions': twitter_count,
                    'share': round(twitter_count / max(total_actions, 1) * 100, 1),
                    'current_round': state_dict.get('twitter_current_round', 0),
                    'simulated_hours': state_dict.get('twitter_simulated_hours', 0),
                    'running': state_dict.get('twitter_running', False),
                    'completed': state_dict.get('twitter_completed', False),
                },
                'reddit': {
                    'actions': reddit_count,
                    'share': round(reddit_count / max(total_actions, 1) * 100, 1),
                    'current_round': state_dict.get('reddit_current_round', 0),
                    'simulated_hours': state_dict.get('reddit_simulated_hours', 0),
                    'running': state_dict.get('reddit_running', False),
                    'completed': state_dict.get('reddit_completed', False),
                },
            },
            'action_distribution': action_dist,
            'agent_leaderboard': agent_leaderboard,
            'round_series': round_series,
        }

    @classmethod
    def _compute_action_distribution(cls, agent_stats: List[Dict]) -> List[Dict[str, Any]]:
        """Aggregate action types across all agents into a distribution list."""
        totals: Dict[str, int] = {}
        for agent in agent_stats:
            for action_type, count in agent.get('action_types', {}).items():
                totals[action_type] = totals.get(action_type, 0) + count

        grand_total = sum(totals.values()) or 1
        return sorted(
            [
                {
                    'action_type': atype,
                    'count': count,
                    'percent': round(count / grand_total * 100, 1),
                    'category': 'content' if atype in cls.CONTENT_ACTIONS else 'engagement',
                }
                for atype, count in totals.items()
            ],
            key=lambda x: x['count'],
            reverse=True,
        )

    @classmethod
    def _build_round_series(cls, timeline: List[Dict]) -> List[Dict[str, Any]]:
        """Transform timeline into a chart-friendly series."""
        return [
            {
                'round': entry['round_num'],
                'twitter': entry.get('twitter_actions', 0),
                'reddit': entry.get('reddit_actions', 0),
                'total': entry.get('total_actions', 0),
                'active_agents': entry.get('active_agents_count', 0),
            }
            for entry in timeline
        ]

    @classmethod
    def _build_agent_leaderboard(cls, agent_stats: List[Dict], limit: int = 10) -> List[Dict[str, Any]]:
        """Return top agents ranked by total actions."""
        return [
            {
                'agent_id': a['agent_id'],
                'agent_name': a['agent_name'],
                'total_actions': a['total_actions'],
                'twitter_actions': a.get('twitter_actions', 0),
                'reddit_actions': a.get('reddit_actions', 0),
                'top_action': max(a.get('action_types', {}), key=a['action_types'].get, default=None) if a.get('action_types') else None,
            }
            for a in agent_stats[:limit]
        ]

    @classmethod
    def _compute_rates(
        cls,
        timeline: List[Dict],
        total_actions: int,
        current_round: int,
    ) -> Dict[str, Any]:
        """Compute derived rate metrics."""
        content_count = 0
        engagement_count = 0
        for entry in timeline:
            for atype, count in entry.get('action_types', {}).items():
                if atype in cls.CONTENT_ACTIONS:
                    content_count += count
                elif atype in cls.ENGAGEMENT_ACTIONS:
                    engagement_count += count

        return {
            'content_actions': content_count,
            'engagement_actions': engagement_count,
            'actions_per_round': round(total_actions / max(current_round, 1), 1),
        }

    @classmethod
    def _empty_metrics(cls, simulation_id: str) -> Dict[str, Any]:
        """Return an empty metrics shell when no data is available."""
        return {
            'simulation_id': simulation_id,
            'status': 'idle',
            'collected_at': datetime.now().isoformat(),
            'summary': {
                'total_actions': 0,
                'total_rounds': 0,
                'current_round': 0,
                'progress_percent': 0,
                'simulated_hours': 0,
                'total_simulation_hours': 0,
                'unique_agents': 0,
                'content_actions': 0,
                'engagement_actions': 0,
                'actions_per_round': 0,
                'started_at': None,
                'completed_at': None,
            },
            'platform_breakdown': {
                'twitter': {'actions': 0, 'share': 0, 'current_round': 0, 'simulated_hours': 0, 'running': False, 'completed': False},
                'reddit': {'actions': 0, 'share': 0, 'current_round': 0, 'simulated_hours': 0, 'running': False, 'completed': False},
            },
            'action_distribution': [],
            'agent_leaderboard': [],
            'round_series': [],
        }

    @classmethod
    def generate_demo_metrics(cls, simulation_id: str = 'demo') -> Dict[str, Any]:
        """Generate realistic mock metrics for demo mode."""
        num_rounds = random.randint(6, 12)
        num_agents = random.randint(8, 15)

        agent_names = [
            'Sarah Chen, VP Support @ Acme SaaS',
            'James Wright, CX Director @ Retail Plus',
            'Robert Williams, IT Director @ EduSpark',
            'Michael Chang, Head of Ops @ FinEdge',
            'Anika Sharma, Head of Support Eng @ DevStack',
            'Sofia Martinez, Support Manager @ QuickShip',
            'Rachel Torres, VP Support @ CloudOps Inc',
            'David Park, CX Lead @ HealthFirst',
            'Emily Watson, IT Manager @ DataPulse',
            'Carlos Rivera, Director of Ops @ NovaPay',
            'Lisa Kim, CTO @ StartupHQ',
            'Tom Bradley, VP Engineering @ ScaleUp',
            'Nina Patel, Product Lead @ GrowthCo',
            'Alex Johansson, Support Eng @ Nordic SaaS',
            'Maria Garcia, CS Director @ LatAm Pay',
        ]

        action_types = ['CREATE_POST', 'REPLY', 'LIKE', 'REPOST', 'COMMENT', 'UPVOTE', 'SHARE', 'CREATE_THREAD']

        round_series = []
        total_twitter = 0
        total_reddit = 0
        for r in range(1, num_rounds + 1):
            tw = random.randint(5, 25)
            rd = random.randint(3, 20)
            total_twitter += tw
            total_reddit += rd
            round_series.append({
                'round': r,
                'twitter': tw,
                'reddit': rd,
                'total': tw + rd,
                'active_agents': random.randint(4, num_agents),
            })

        total_actions = total_twitter + total_reddit

        leaderboard = []
        for i in range(min(num_agents, 10)):
            t_act = random.randint(5, 30)
            r_act = random.randint(3, 20)
            leaderboard.append({
                'agent_id': i,
                'agent_name': agent_names[i % len(agent_names)],
                'total_actions': t_act + r_act,
                'twitter_actions': t_act,
                'reddit_actions': r_act,
                'top_action': random.choice(action_types),
            })
        leaderboard.sort(key=lambda x: x['total_actions'], reverse=True)

        dist_data = {}
        for at in action_types:
            dist_data[at] = random.randint(5, 60)
        dist_total = sum(dist_data.values()) or 1
        action_distribution = sorted(
            [
                {
                    'action_type': at,
                    'count': c,
                    'percent': round(c / dist_total * 100, 1),
                    'category': 'content' if at in cls.CONTENT_ACTIONS else 'engagement',
                }
                for at, c in dist_data.items()
            ],
            key=lambda x: x['count'],
            reverse=True,
        )

        content_sum = sum(d['count'] for d in action_distribution if d['category'] == 'content')
        engage_sum = sum(d['count'] for d in action_distribution if d['category'] == 'engagement')

        return {
            'simulation_id': simulation_id,
            'status': 'completed',
            'collected_at': datetime.now().isoformat(),
            'summary': {
                'total_actions': total_actions,
                'total_rounds': num_rounds,
                'current_round': num_rounds,
                'progress_percent': 100,
                'simulated_hours': num_rounds * 2,
                'total_simulation_hours': num_rounds * 2,
                'unique_agents': num_agents,
                'content_actions': content_sum,
                'engagement_actions': engage_sum,
                'actions_per_round': round(total_actions / num_rounds, 1),
                'started_at': datetime.now().isoformat(),
                'completed_at': datetime.now().isoformat(),
            },
            'platform_breakdown': {
                'twitter': {
                    'actions': total_twitter,
                    'share': round(total_twitter / max(total_actions, 1) * 100, 1),
                    'current_round': num_rounds,
                    'simulated_hours': num_rounds * 2,
                    'running': False,
                    'completed': True,
                },
                'reddit': {
                    'actions': total_reddit,
                    'share': round(total_reddit / max(total_actions, 1) * 100, 1),
                    'current_round': num_rounds,
                    'simulated_hours': num_rounds * 2,
                    'running': False,
                    'completed': True,
                },
            },
            'action_distribution': action_distribution,
            'agent_leaderboard': leaderboard,
            'round_series': round_series,
        }
