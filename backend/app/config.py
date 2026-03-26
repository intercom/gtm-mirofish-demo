"""
Configuration management
Loads from project root .env file
"""

import os
from dotenv import load_dotenv

project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    load_dotenv(override=True)

# Multi-LLM Provider Configuration
LLM_PROVIDERS = {
    "anthropic": {
        "base_url": "https://api.anthropic.com/v1/",
        "default_model": "claude-sonnet-4-20250514",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1/",
        "default_model": "gpt-4o",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",
    },
}

def get_llm_config():
    """Resolve LLM configuration from provider or explicit env vars."""
    provider = os.environ.get('LLM_PROVIDER', '').lower()

    if provider in LLM_PROVIDERS:
        provider_config = LLM_PROVIDERS[provider]
        return {
            "api_key": os.environ.get('LLM_API_KEY'),
            "base_url": os.environ.get('LLM_BASE_URL', provider_config['base_url']),
            "model_name": os.environ.get('LLM_MODEL_NAME', provider_config['default_model']),
        }
    else:
        # Fallback to explicit env vars (original MiroFish behavior)
        return {
            "api_key": os.environ.get('LLM_API_KEY'),
            "base_url": os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1'),
            "model_name": os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini'),
        }


class Config:
    """Flask configuration"""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-gtm-demo-secret')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    JSON_AS_ASCII = False

    # LLM Configuration (resolved from provider)
    _llm = get_llm_config()
    LLM_API_KEY = _llm['api_key']
    LLM_BASE_URL = _llm['base_url']
    LLM_MODEL_NAME = _llm['model_name']

    # Zep Configuration
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')

    # File upload
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}

    # Text processing
    DEFAULT_CHUNK_SIZE = 500
    DEFAULT_CHUNK_OVERLAP = 50

    # OASIS simulation
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '10'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '5'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    # Auth Configuration
    AUTH_ENABLED = os.environ.get('AUTH_ENABLED', 'false').lower() == 'true'
    AUTH_PROVIDER = os.environ.get('AUTH_PROVIDER', 'google')
    AUTH_ALLOWED_DOMAIN = os.environ.get('AUTH_ALLOWED_DOMAIN', 'intercom.io')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    @classmethod
    def validate(cls):
        """Validate required configuration.

        Returns a list of hard errors. Missing ZEP_API_KEY is only a
        warning (the app runs in demo mode without it).
        """
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY not configured")
        return errors

    @classmethod
    def warnings(cls):
        """Return non-fatal configuration warnings."""
        warns = []
        if not cls.ZEP_API_KEY:
            warns.append("ZEP_API_KEY not configured — Zep features disabled (demo mode)")
        return warns
