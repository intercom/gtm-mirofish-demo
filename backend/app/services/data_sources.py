"""
Report Data Source Service

Provides metadata and preview data for report data sources.
Real data for simulation sources; mock data for future integrations
(Revenue, Pipeline, Salesforce, CPQ, Orders, Campaigns).
"""

import json
import os

from ..utils.logger import get_logger

logger = get_logger('mirofish.data_sources')

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), '../../gtm_seed_data')

DATA_SOURCE_TYPES = [
    {
        'id': 'simulation',
        'name': 'Simulation Results',
        'description': 'OASIS agent simulation actions, timeline, and agent statistics',
        'category': 'internal',
        'icon': 'simulation',
        'connected': True,
    },
    {
        'id': 'revenue',
        'name': 'Revenue Data',
        'description': 'ARR, MRR, expansion/contraction, and cohort revenue metrics',
        'category': 'finance',
        'icon': 'revenue',
        'connected': False,
    },
    {
        'id': 'pipeline',
        'name': 'Sales Pipeline',
        'description': 'Opportunity stages, conversion rates, and deal velocity',
        'category': 'sales',
        'icon': 'pipeline',
        'connected': False,
    },
    {
        'id': 'salesforce',
        'name': 'Salesforce CRM',
        'description': 'Account, contact, and opportunity data from Salesforce',
        'category': 'crm',
        'icon': 'salesforce',
        'connected': False,
    },
    {
        'id': 'cpq',
        'name': 'CPQ',
        'description': 'Configure-Price-Quote data for deal sizing and discounting',
        'category': 'sales',
        'icon': 'cpq',
        'connected': False,
    },
    {
        'id': 'orders',
        'name': 'Orders',
        'description': 'Order management, fulfillment status, and booking history',
        'category': 'operations',
        'icon': 'orders',
        'connected': False,
    },
    {
        'id': 'campaigns',
        'name': 'Marketing Campaigns',
        'description': 'Campaign performance, attribution, and engagement metrics',
        'category': 'marketing',
        'icon': 'campaigns',
        'connected': False,
    },
]

# Mock preview data for unconnected sources
_MOCK_PREVIEWS = {
    'revenue': {
        'metrics': [
            {'label': 'Total ARR', 'value': '$12.4M', 'trend': '+18%'},
            {'label': 'Net Revenue Retention', 'value': '112%', 'trend': '+3%'},
            {'label': 'Expansion MRR', 'value': '$84K', 'trend': '+22%'},
        ],
        'sample_rows': [
            {'account': 'Acme Corp', 'arr': '$240K', 'segment': 'Enterprise', 'status': 'Expanding'},
            {'account': 'Globex Inc', 'arr': '$85K', 'segment': 'Mid-Market', 'status': 'Stable'},
            {'account': 'Initech', 'arr': '$42K', 'segment': 'SMB', 'status': 'At Risk'},
        ],
    },
    'pipeline': {
        'metrics': [
            {'label': 'Pipeline Value', 'value': '$8.2M', 'trend': '+12%'},
            {'label': 'Win Rate', 'value': '34%', 'trend': '+5%'},
            {'label': 'Avg Deal Cycle', 'value': '42 days', 'trend': '-8%'},
        ],
        'sample_rows': [
            {'opportunity': 'Acme Expansion', 'stage': 'Negotiation', 'value': '$180K', 'close_date': '2026-04-15'},
            {'opportunity': 'Globex New', 'stage': 'Discovery', 'value': '$95K', 'close_date': '2026-05-01'},
        ],
    },
    'salesforce': {
        'metrics': [
            {'label': 'Total Accounts', 'value': '2,847', 'trend': '+6%'},
            {'label': 'Active Contacts', 'value': '12,403', 'trend': '+9%'},
            {'label': 'Open Opportunities', 'value': '384', 'trend': '+14%'},
        ],
        'sample_rows': [
            {'account': 'Acme Corp', 'type': 'Enterprise', 'owner': 'Jane Smith', 'health': 'A'},
            {'account': 'Globex Inc', 'type': 'Mid-Market', 'owner': 'Bob Lee', 'health': 'B'},
        ],
    },
    'cpq': {
        'metrics': [
            {'label': 'Avg Deal Size', 'value': '$67K', 'trend': '+11%'},
            {'label': 'Avg Discount', 'value': '14%', 'trend': '-2%'},
            {'label': 'Quote-to-Close', 'value': '68%', 'trend': '+4%'},
        ],
        'sample_rows': [
            {'quote': 'Q-2026-0142', 'product': 'Enterprise Suite', 'value': '$180K', 'discount': '12%'},
            {'quote': 'Q-2026-0143', 'product': 'Growth Plan', 'value': '$45K', 'discount': '8%'},
        ],
    },
    'orders': {
        'metrics': [
            {'label': 'Orders This Month', 'value': '127', 'trend': '+15%'},
            {'label': 'Avg Order Value', 'value': '$54K', 'trend': '+7%'},
            {'label': 'Fulfillment Rate', 'value': '96%', 'trend': '+1%'},
        ],
        'sample_rows': [
            {'order': 'ORD-8821', 'customer': 'Acme Corp', 'value': '$240K', 'status': 'Fulfilled'},
            {'order': 'ORD-8822', 'customer': 'Initech', 'value': '$42K', 'status': 'Pending'},
        ],
    },
    'campaigns': {
        'metrics': [
            {'label': 'Active Campaigns', 'value': '18', 'trend': '+3'},
            {'label': 'Total Leads', 'value': '4,291', 'trend': '+24%'},
            {'label': 'Cost per Lead', 'value': '$32', 'trend': '-12%'},
        ],
        'sample_rows': [
            {'campaign': 'Q1 Webinar Series', 'channel': 'Email', 'leads': 842, 'conversion': '4.2%'},
            {'campaign': 'Product Launch', 'channel': 'Multi-touch', 'leads': 1203, 'conversion': '3.8%'},
        ],
    },
}


class DataSourceService:

    @staticmethod
    def list_sources():
        return DATA_SOURCE_TYPES

    @staticmethod
    def get_source(source_id):
        for src in DATA_SOURCE_TYPES:
            if src['id'] == source_id:
                return src
        return None

    @staticmethod
    def get_preview(source_type, simulation_id=None):
        """Return preview data for a data source type."""
        if source_type == 'simulation':
            return DataSourceService._get_simulation_preview(simulation_id)

        if source_type in _MOCK_PREVIEWS:
            return {
                'source_type': source_type,
                'is_mock': True,
                **_MOCK_PREVIEWS[source_type],
            }

        return {'source_type': source_type, 'is_mock': True, 'metrics': [], 'sample_rows': []}

    @staticmethod
    def _get_simulation_preview(simulation_id):
        """Fetch real simulation metrics, falling back to seed-data-based preview."""
        if simulation_id:
            try:
                from ..services.simulation_manager import SimulationManager
                manager = SimulationManager()
                state = manager.get_simulation(simulation_id)
                if state:
                    metrics = [
                        {'label': 'Total Actions', 'value': str(state.total_actions_count or 0), 'trend': ''},
                        {'label': 'Twitter Actions', 'value': str(state.twitter_actions_count or 0), 'trend': ''},
                        {'label': 'Reddit Actions', 'value': str(state.reddit_actions_count or 0), 'trend': ''},
                        {'label': 'Simulated Hours', 'value': str(state.simulated_hours or 0), 'trend': ''},
                    ]
                    return {
                        'source_type': 'simulation',
                        'simulation_id': simulation_id,
                        'is_mock': False,
                        'metrics': metrics,
                        'sample_rows': [],
                    }
            except Exception as e:
                logger.warning(f"Failed to load simulation {simulation_id}: {e}")

        # Fallback: seed-data-based preview
        profiles = DataSourceService._load_seed_profiles()
        metrics = [
            {'label': 'Account Profiles', 'value': str(len(profiles)), 'trend': ''},
            {'label': 'Segments', 'value': str(len({p.get('segment') for p in profiles})), 'trend': ''},
            {'label': 'Industries', 'value': str(len({p.get('industry') for p in profiles})), 'trend': ''},
        ]
        sample_rows = [
            {
                'segment': p.get('segment', ''),
                'industry': p.get('industry', ''),
                'arr_range': p.get('arr_range', ''),
                'health_score': p.get('health_score', ''),
            }
            for p in profiles[:4]
        ]
        return {
            'source_type': 'simulation',
            'simulation_id': simulation_id,
            'is_mock': simulation_id is None,
            'metrics': metrics,
            'sample_rows': sample_rows,
        }

    @staticmethod
    def _load_seed_profiles():
        filepath = os.path.join(SEED_DATA_DIR, 'account_profiles.json')
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('profiles', [])
        except Exception:
            pass
        return []
