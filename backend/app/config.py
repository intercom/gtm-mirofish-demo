"""
Configuration management
Class-based config hierarchy: BaseConfig → DevelopmentConfig / ProductionConfig
Loads from project root .env file, selects config class via FLASK_ENV.
"""

import os
import logging
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


class BaseConfig:
    """Shared configuration across all environments."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'mirofish-gtm-demo-secret')
    DEBUG = False
    JSON_AS_ASCII = False

    # CSRF Protection (Flask-WTF)
    WTF_CSRF_TIME_LIMIT = 3600
    WTF_CSRF_HEADERS = ['X-CSRFToken']

    # CORS origins (comma-separated for multiple origins)
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')

    # Session cookie configuration for CSRF token storage
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None' if os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true' else 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

    # LLM Configuration (resolved from provider)
    _llm = get_llm_config()
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER', '').lower()
    LLM_API_KEY = _llm['api_key']
    LLM_BASE_URL = _llm['base_url']
    LLM_MODEL_NAME = _llm['model_name']

    # Zep Configuration
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')

    # Server
    PORT = int(os.environ.get('BACKEND_PORT', os.environ.get('FLASK_PORT', '5001')))

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

    # Rate Limiting
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_DEFAULT = int(os.environ.get('RATE_LIMIT_DEFAULT', '60'))
    RATE_LIMIT_LLM = int(os.environ.get('RATE_LIMIT_LLM', '10'))
    RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '60'))

    # Demo
    DEMO_SPEED = float(os.environ.get('DEMO_SPEED', '1.0'))

    # Logging
    LOG_FILE = os.environ.get('LOG_FILE', '')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Auth Configuration
    AUTH_ENABLED = os.environ.get('AUTH_ENABLED', 'false').lower() == 'true'
    AUTH_PROVIDER = os.environ.get('AUTH_PROVIDER', 'google')
    AUTH_ALLOWED_DOMAIN = os.environ.get('AUTH_ALLOWED_DOMAIN', 'intercom.io')
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

    # RBAC — role assigned to authenticated users with no explicit role
    RBAC_DEFAULT_ROLE = os.environ.get('RBAC_DEFAULT_ROLE', 'viewer')

    @classmethod
    def validate(cls):
        """Validate configuration. Returns errors list; logs warnings for missing optional vars."""
        logger = logging.getLogger('mirofish.config')
        errors = []

        # Warn about missing optional vars
        if not cls.LLM_API_KEY:
            logger.warning("LLM_API_KEY not set — LLM features will use demo/mock mode")
        if not cls.ZEP_API_KEY:
            logger.warning("ZEP_API_KEY not set — knowledge graph features unavailable")
        if cls.SECRET_KEY == 'mirofish-gtm-demo-secret':
            logger.warning("SECRET_KEY using default value — set a unique key for production")

        # Error on invalid combinations
        if cls.LLM_PROVIDER and cls.LLM_PROVIDER not in LLM_PROVIDERS:
            errors.append(
                f"LLM_PROVIDER '{cls.LLM_PROVIDER}' is not supported. "
                f"Choose from: {', '.join(LLM_PROVIDERS.keys())}"
            )
        if cls.LLM_PROVIDER and not cls.LLM_API_KEY:
            errors.append(
                f"LLM_PROVIDER is set to '{cls.LLM_PROVIDER}' but LLM_API_KEY is missing"
            )
        if cls.AUTH_ENABLED and cls.AUTH_PROVIDER == 'google' and not cls.GOOGLE_CLIENT_ID:
            errors.append("AUTH_ENABLED with Google provider requires GOOGLE_CLIENT_ID")

        return errors

    @classmethod
    def warnings(cls):
        """Return non-fatal configuration warnings."""
        warns = []
        if not cls.ZEP_API_KEY:
            warns.append("ZEP_API_KEY not configured — Zep features disabled (demo mode)")
        return warns


class DevelopmentConfig(BaseConfig):
    """Development: debug mode enabled, verbose logging."""

    DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')


class ProductionConfig(BaseConfig):
    """Production: no debug, strict CORS, stricter validation."""

    DEBUG = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')

    @classmethod
    def validate(cls):
        """Production adds stricter validation on top of base checks."""
        errors = super().validate()
        if cls.SECRET_KEY == 'mirofish-gtm-demo-secret':
            errors.append("SECRET_KEY must be changed from default in production")
        if cls.CORS_ORIGINS == '*':
            errors.append("CORS_ORIGINS must not be wildcard '*' in production")
        return errors


# Select configuration based on FLASK_ENV
_env = os.environ.get('FLASK_ENV', 'development').lower()
_config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': DevelopmentConfig,
}
Config = _config_map.get(_env, DevelopmentConfig)
