"""
MiroFish Backend - Flask应用工厂
"""

import os
import time
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, g, jsonify, request, session
from flask_cors import CORS
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect, generate_csrf

from .config import Config
from .shutdown import is_shutting_down
from .utils.logger import setup_logger, get_logger
from .middleware.error_handler import register_error_handlers

csrf = CSRFProtect()


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False

    # 设置日志
    logger = setup_logger('mirofish')

    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)

    # CORS — parse comma-separated origins from config, or allow all with "*"
    raw_origins = app.config.get('CORS_ORIGINS', '*')
    origins = [o.strip() for o in raw_origins.split(',')] if raw_origins != '*' else '*'
    CORS(app, resources={
        r"/api/*": {"origins": origins},
        r"/auth/*": {"origins": origins},
    }, supports_credentials=True)

    # 启用GZIP压缩
    Compress(app)

    # 启用CSRF保护
    csrf.init_app(app)

    # Auth middleware (loads g.user from JWT when AUTH_ENABLED=true)
    from auth.middleware import init_auth_middleware
    init_auth_middleware(app)

    # Graceful degradation middleware (service health + error handlers)
    from .utils.degradation import register_degradation_middleware
    register_degradation_middleware(app)

    # Security headers on all responses
    from .middleware import init_security_headers
    init_security_headers(app)


    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")

    # Rate limiting middleware (must be registered before request logging)
    from .middleware.rate_limit import init_rate_limiter
    init_rate_limiter(app)
    if should_log_startup:
        logger.info("Rate limiting middleware registered")

    # Health monitoring
    from .services.health_monitor import health_monitor

    # 请求日志中间件
    from .middleware import register_request_logging
    register_request_logging(app)

    # Health metrics tracking
    @app.before_request
    def track_health_metrics():
        request._health_start = time.monotonic()
        health_monitor.on_request_start()

    @app.after_request
    def record_health_metrics(response):
        duration = time.monotonic() - getattr(request, '_health_start', time.monotonic())
        health_monitor.on_request_end(duration, is_error=response.status_code >= 500)
        return response

    # Populate g.user from session for permission checking
    @app.before_request
    def load_user_context():
        g.user = session.get('user')

    @app.after_request
    def set_csrf_cookie(response):
        response.set_cookie(
            'csrf_token',
            generate_csrf(),
            samesite=app.config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            secure=app.config.get('SESSION_COOKIE_SECURE', False),
            httponly=False,
        )
        return response

    # CSRF token endpoint for SPA clients
    @app.route('/api/csrf-token', methods=['GET'])
    def csrf_token():
        return jsonify({'csrf_token': generate_csrf()})

    # Register blueprints — core blueprints are required, extension
    # blueprints are wrapped in try/except to tolerate broken modules
    # from parallel PRD execution.
    from .api import graph_bp, simulation_bp, report_bp, memory_transfer_bp
    _register = []

    def _safe_register(bp, **kwargs):
        """Register a blueprint, logging but not raising on failure."""
        try:
            app.register_blueprint(bp, **kwargs)
        except Exception as e:
            app.logger.warning("Blueprint %s skipped: %s", getattr(bp, 'name', '?'), e)

    # Core blueprints (may have duplicate-endpoint issues from PRD agents)
    _safe_register(graph_bp, url_prefix='/api/v1/graph')
    _safe_register(simulation_bp, url_prefix='/api/v1/simulation')
    _safe_register(report_bp, url_prefix='/api/v1/report')
    _safe_register(memory_transfer_bp, url_prefix='/api/v1/memory')

    # GTM scenario extensions
    from .api.gtm_scenarios import gtm_bp
    app.register_blueprint(gtm_bp)

    # All other extension blueprints — non-essential, best-effort
    _extension_blueprints = [
        ('.api.aggregation', 'aggregation_bp', {}),
        ('.api.attribution', 'attribution_bp', {}),
        ('.api.templates', 'templates_bp', {}),
        ('.api.deals', 'deals_bp', {}),
        ('.api.gtm_dashboard', 'gtm_dashboard_bp', {}),
        ('.api.pipeline', 'pipeline_bp', {}),
        ('.api.insights', 'insights_bp', {}),
        ('.api.memory', 'memory_bp', {}),
        ('.api.personas', 'personas_bp', {}),
        ('.api.team', 'team_bp', {}),
        ('.api.comparison', 'comparison_bp', {}),
        ('.api.settings', 'settings_bp', {}),
        ('.api.temporal_memory', 'temporal_memory_bp', {}),
        ('.api.cost_model', 'cost_model_bp', {}),
        ('.api.decisions', 'decisions_bp', {}),
        ('.api.metrics', 'metrics_bp', {}),
        ('.api.orders', 'orders_bp', {}),
        ('.api.personality', 'personality_bp', {}),
        ('.api.cpq', 'cpq_bp', {}),
        ('.api.debate', 'debate_bp', {}),
        ('.api.reconciliation', 'reconciliation_bp', {}),
        ('.api.branches', 'branches_bp', {}),
        ('.api.audit', 'audit_bp', {}),
        ('.api.audit_log', 'audit_log_bp', {}),
        ('.api.users', 'users_bp', {}),
        ('.api.revenue', 'revenue_bp', {}),
        ('.api.health', 'health_bp', {}),
        ('.api.services', 'services_bp', {}),
        ('.api.campaigns', 'campaigns_bp', {}),
        ('.api.agents', 'agents_bp', {}),
        ('.api.errors', 'errors_bp', {}),
        ('.api.salesforce', 'salesforce_bp', {}),
        ('.api.analytics', 'analytics_bp', {}),
        ('.api.data_pipeline', 'data_pipeline_bp', {}),
        ('.api.batch', 'batch_bp', {}),
        ('.api.auth', 'auth_bp', {}),
        ('.api.api_keys', 'api_keys_bp', {}),
        ('.api.sessions', 'sessions_bp', {}),
        ('.api.report_builder', 'report_builder_bp', {}),
        ('.api.memory', 'memory_config_bp', {}),
        ('.api.agent_prompts', 'agent_prompts_bp', {}),
        ('.api.cache', 'cache_bp', {}),
        ('.api.memory', 'agent_memory_bp', {}),
        ('.api.beliefs', 'beliefs_bp', {}),
    ]

    import importlib
    for module_path, bp_name, kwargs in _extension_blueprints:
        try:
            mod = importlib.import_module(module_path, package='app')
            bp = getattr(mod, bp_name)
            _safe_register(bp, **kwargs)
        except Exception as e:
            app.logger.debug("Extension blueprint %s.%s skipped: %s", module_path, bp_name, e)

    # OAuth flow (login, callback, logout, me)
    try:
        from auth.oauth_routes import auth_bp as oauth_bp
        app.register_blueprint(oauth_bp)
    except Exception as e:
        app.logger.debug("OAuth blueprint skipped: %s", e)

    # Error handling middleware
    register_error_handlers(app)

    # 健康检查 — returns 503 during shutdown for load balancer draining
    @app.route('/health')
    @app.route('/api/health')
    def health():
        if is_shutting_down():
            return {'status': 'shutting_down', 'service': 'MiroFish Backend'}, 503
        return {'status': 'ok', 'service': 'MiroFish Backend'}

    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")

    return app
