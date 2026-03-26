"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask
from flask_cors import CORS

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
    
    # 请求日志中间件
    from .middleware import register_request_logging
    register_request_logging(app)
    
    # Register blueprints
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')

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

    # User management API
    from .api.users import users_bp
    app.register_blueprint(users_bp)

    # Health checks (basic, detailed, service degradation)
    from .api.health import health_bp
    app.register_blueprint(health_bp)

    # Root-level liveness check (for load balancers / infrastructure)
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app

