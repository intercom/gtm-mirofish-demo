"""
MiroFish Backend - Flask应用工厂
"""

import os
import time
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, g, request, session
from flask_cors import CORS
from flask_compress import Compress

from .config import Config
from .utils.logger import setup_logger


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
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 启用GZIP压缩
    Compress(app)

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


    # Register blueprints
    from .api import graph_bp, simulation_bp, report_bp, memory_transfer_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(memory_transfer_bp, url_prefix='/api/memory')

    # GTM scenario extensions
    from .api.gtm_scenarios import gtm_bp
    app.register_blueprint(gtm_bp)

    # Scenario aggregation API
    from .api.aggregation import aggregation_bp
    app.register_blueprint(aggregation_bp)

    # Attribution analysis API
    from .api.attribution import attribution_bp
    app.register_blueprint(attribution_bp)

    # Scenario template CRUD API
    from .api.templates import templates_bp
    app.register_blueprint(templates_bp)

    # Deals API (dashboard ticker)
    from .api.deals import deals_bp
    app.register_blueprint(deals_bp)

    # GTM dashboard API
    from .api.gtm_dashboard import gtm_dashboard_bp
    app.register_blueprint(gtm_dashboard_bp)

    # Pipeline funnel API (dashboard widgets)
    from .api.pipeline import pipeline_bp
    app.register_blueprint(pipeline_bp)

    # Insights API (LLM-powered GTM insights)
    from .api.insights import insights_bp
    app.register_blueprint(insights_bp)

    # Memory search API
    from .api.memory import memory_bp
    app.register_blueprint(memory_bp)

    # Persona generation API
    from .api.personas import personas_bp
    app.register_blueprint(personas_bp)

    # Team composition API
    from .api.team import team_bp
    app.register_blueprint(team_bp)

    # Settings API (test connections, auth status)
    from .api.settings import settings_bp
    app.register_blueprint(settings_bp)

    # Temporal memory API (Zep-backed time-travel memory)
    from .api.temporal_memory import temporal_memory_bp
    app.register_blueprint(temporal_memory_bp)

    # Cost model API (campaign cost modeling calculator)
    from .api.cost_model import cost_model_bp
    app.register_blueprint(cost_model_bp)

    # Decision explanation API
    from .api.decisions import decisions_bp
    app.register_blueprint(decisions_bp)

    # OASIS Metrics API
    from .api.metrics import metrics_bp
    app.register_blueprint(metrics_bp)

    # Order-to-Cash API
    from .api.orders import orders_bp
    app.register_blueprint(orders_bp)

    # Personality dynamics API
    from .api.personality import personality_bp
    app.register_blueprint(personality_bp)

    # CPQ (Configure Price Quote) API
    from .api.cpq import cpq_bp
    app.register_blueprint(cpq_bp)

    # Debate orchestration API
    from .api.debate import debate_bp
    app.register_blueprint(debate_bp)

    # Reconciliation API (three-way MRR reconciliation)
    from .api.reconciliation import reconciliation_bp
    app.register_blueprint(reconciliation_bp)

    # Branch comparison & insights API
    from .api.branches import branches_bp
    app.register_blueprint(branches_bp)

    # Audit log API
    from .api.audit import audit_bp
    app.register_blueprint(audit_bp)

    # Audit log viewer API
    from .api.audit_log import audit_log_bp
    app.register_blueprint(audit_log_bp)

    # User management API
    from .api.users import users_bp
    app.register_blueprint(users_bp)

    # Revenue analytics API
    from .api.revenue import revenue_bp
    app.register_blueprint(revenue_bp)

    # Health checks (basic, detailed, service degradation, monitoring metrics)
    from .api.health import health_bp
    app.register_blueprint(health_bp)

    # Unified service availability checker
    from .api.services import services_bp
    app.register_blueprint(services_bp)

    # Campaigns API (ROI comparison, efficiency metrics)
    from .api.campaigns import campaigns_bp
    app.register_blueprint(campaigns_bp)

    # Agents API (wizard creation, preview, OASIS agent factory)
    from .api.agents import agents_bp
    app.register_blueprint(agents_bp)

    # Frontend error tracking
    from .api.errors import errors_bp
    app.register_blueprint(errors_bp)

    # Salesforce CRM demo data API
    from .api.salesforce import salesforce_bp
    app.register_blueprint(salesforce_bp)

    # Analytics API (cohort analysis, segment performance)
    from .api.analytics import analytics_bp
    app.register_blueprint(analytics_bp)

    # Data Pipeline API (connector health, sync status)
    from .api.data_pipeline import data_pipeline_bp
    app.register_blueprint(data_pipeline_bp)

    # Batch API (multi-request batching)
    from .api.batch import batch_bp
    app.register_blueprint(batch_bp)

    # Auth API (login, logout, token validation)
    from .api.auth import auth_bp
    app.register_blueprint(auth_bp)

    # API Key management
    from .api.api_keys import api_keys_bp
    app.register_blueprint(api_keys_bp)

    # Sessions API
    from .api.sessions import sessions_bp
    app.register_blueprint(sessions_bp)

    # Report Builder API (templates + generated reports)
    from .api.report_builder import report_builder_bp
    app.register_blueprint(report_builder_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app

