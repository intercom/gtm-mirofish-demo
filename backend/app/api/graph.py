"""
图谱相关API路由
采用项目上下文机制，服务端持久化状态
"""

import os
import traceback
import threading
from collections import defaultdict
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.cache import cached_response
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..services.community_detection import CommunityDetector
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

# 获取日志器
logger = get_logger('mirofish.api')


def is_zep_available() -> bool:
    """Check if Zep Cloud is configured and available."""
    return bool(Config.ZEP_API_KEY)


# ============== Mock data for demo mode ==============

def _mock_entities():
    """GTM-themed mock entities for when Zep is not configured."""
    return [
        {"uuid": "mock-ent-001", "name": "Intercom", "labels": ["Entity", "Company"],
         "summary": "Leading customer messaging platform for B2B SaaS companies.", "attributes": {}},
        {"uuid": "mock-ent-002", "name": "Zendesk", "labels": ["Entity", "Company"],
         "summary": "Enterprise customer service and support platform.", "attributes": {}},
        {"uuid": "mock-ent-003", "name": "Product-Led Growth", "labels": ["Entity", "Strategy"],
         "summary": "Growth strategy where product usage drives acquisition and retention.", "attributes": {}},
        {"uuid": "mock-ent-004", "name": "Enterprise Segment", "labels": ["Entity", "Segment"],
         "summary": "Companies with 500+ employees and complex support needs.", "attributes": {}},
        {"uuid": "mock-ent-005", "name": "SMB Segment", "labels": ["Entity", "Segment"],
         "summary": "Small-to-medium businesses with 10-500 employees.", "attributes": {}},
        {"uuid": "mock-ent-006", "name": "AI Chatbot", "labels": ["Entity", "Product"],
         "summary": "AI-powered conversational support reducing ticket volume by 40%.", "attributes": {}},
        {"uuid": "mock-ent-007", "name": "Customer Success Manager", "labels": ["Entity", "Role"],
         "summary": "Post-sales role focused on retention and expansion revenue.", "attributes": {}},
        {"uuid": "mock-ent-008", "name": "HubSpot", "labels": ["Entity", "Company"],
         "summary": "CRM and marketing automation platform expanding into service.", "attributes": {}},
        {"uuid": "mock-ent-009", "name": "Churn Risk Model", "labels": ["Entity", "Product"],
         "summary": "Predictive model identifying accounts likely to churn within 90 days.", "attributes": {}},
        {"uuid": "mock-ent-010", "name": "Series D Funding", "labels": ["Entity", "Event"],
         "summary": "$150M funding round to accelerate AI and international expansion.", "attributes": {}},
    ]


def _mock_edges():
    """GTM-themed mock relationships."""
    return [
        {"uuid": "mock-edge-001", "name": "COMPETES_WITH", "fact": "Intercom competes with Zendesk in the customer messaging space.",
         "source_node_uuid": "mock-ent-001", "target_node_uuid": "mock-ent-002",
         "source_node_name": "Intercom", "target_node_name": "Zendesk",
         "created_at": "2025-01-15T10:00:00Z", "valid_at": "2025-01-15T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-002", "name": "ADOPTS_STRATEGY", "fact": "Intercom adopts product-led growth as primary GTM motion.",
         "source_node_uuid": "mock-ent-001", "target_node_uuid": "mock-ent-003",
         "source_node_name": "Intercom", "target_node_name": "Product-Led Growth",
         "created_at": "2025-02-01T10:00:00Z", "valid_at": "2025-02-01T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-003", "name": "TARGETS", "fact": "Intercom targets the enterprise segment for expansion revenue.",
         "source_node_uuid": "mock-ent-001", "target_node_uuid": "mock-ent-004",
         "source_node_name": "Intercom", "target_node_name": "Enterprise Segment",
         "created_at": "2025-03-01T10:00:00Z", "valid_at": "2025-03-01T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-004", "name": "LAUNCHES", "fact": "Intercom launches AI Chatbot to reduce support ticket volume.",
         "source_node_uuid": "mock-ent-001", "target_node_uuid": "mock-ent-006",
         "source_node_name": "Intercom", "target_node_name": "AI Chatbot",
         "created_at": "2025-04-10T10:00:00Z", "valid_at": "2025-04-10T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-005", "name": "SERVES", "fact": "Customer Success Manager serves the enterprise segment accounts.",
         "source_node_uuid": "mock-ent-007", "target_node_uuid": "mock-ent-004",
         "source_node_name": "Customer Success Manager", "target_node_name": "Enterprise Segment",
         "created_at": "2025-01-20T10:00:00Z", "valid_at": "2025-01-20T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-006", "name": "COMPETES_WITH", "fact": "Intercom competes with HubSpot Service Hub in the SMB market.",
         "source_node_uuid": "mock-ent-001", "target_node_uuid": "mock-ent-008",
         "source_node_name": "Intercom", "target_node_name": "HubSpot",
         "created_at": "2025-02-15T10:00:00Z", "valid_at": "2025-02-15T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-007", "name": "TARGETS", "fact": "HubSpot targets the SMB segment with bundled CRM and service.",
         "source_node_uuid": "mock-ent-008", "target_node_uuid": "mock-ent-005",
         "source_node_name": "HubSpot", "target_node_name": "SMB Segment",
         "created_at": "2025-03-05T10:00:00Z", "valid_at": "2025-03-05T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-008", "name": "USES", "fact": "Churn Risk Model uses AI Chatbot engagement data as input signal.",
         "source_node_uuid": "mock-ent-009", "target_node_uuid": "mock-ent-006",
         "source_node_name": "Churn Risk Model", "target_node_name": "AI Chatbot",
         "created_at": "2025-05-01T10:00:00Z", "valid_at": "2025-05-01T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-009", "name": "FUNDS", "fact": "Series D Funding accelerates Intercom's AI product roadmap.",
         "source_node_uuid": "mock-ent-010", "target_node_uuid": "mock-ent-001",
         "source_node_name": "Series D Funding", "target_node_name": "Intercom",
         "created_at": "2025-06-01T10:00:00Z", "valid_at": "2025-06-01T10:00:00Z", "invalid_at": None, "expired_at": None},
        {"uuid": "mock-edge-010", "name": "REPLACED_BY", "fact": "Product-Led Growth replaced traditional enterprise sales as primary motion.",
         "source_node_uuid": "mock-ent-003", "target_node_uuid": "mock-ent-004",
         "source_node_name": "Product-Led Growth", "target_node_name": "Enterprise Segment",
         "created_at": "2024-06-01T10:00:00Z", "valid_at": "2024-06-01T10:00:00Z", "invalid_at": "2025-03-01T10:00:00Z", "expired_at": "2025-03-01T10:00:00Z"},
    ]


def allowed_file(filename: str) -> bool:
    """检查文件扩展名是否允许"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ============== 项目管理接口 ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    获取项目详情
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": f"项目不存在: {project_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
@cached_response(ttl=30)
def list_projects():
    """
    列出所有项目
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects)
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    删除项目
    """
    success = ProjectManager.delete_project(project_id)
    
    if not success:
        return jsonify({
            "success": False,
            "error": f"项目不存在或删除失败: {project_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "message": f"项目已删除: {project_id}"
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    重置项目状态（用于重新构建图谱）
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return jsonify({
            "success": False,
            "error": f"项目不存在: {project_id}"
        }), 404
    
    # 重置到本体已生成状态
    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)
    
    return jsonify({
        "success": True,
        "message": f"项目已重置: {project_id}",
        "data": project.to_dict()
    })


# ============== 接口1：上传文件并生成本体 ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    接口1：上传文件，分析生成本体定义
    
    请求方式：multipart/form-data
    
    参数：
        files: 上传的文件（PDF/MD/TXT），可多个
        simulation_requirement: 模拟需求描述（必填）
        project_name: 项目名称（可选）
        additional_context: 额外说明（可选）
        
    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("=== 开始生成本体定义 ===")
        
        # 获取参数
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        
        logger.debug(f"项目名称: {project_name}")
        logger.debug(f"模拟需求: {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "请提供模拟需求描述 (simulation_requirement)"
            }), 400
        
        # 获取上传的文件
        uploaded_files = request.files.getlist('files')
        if not uploaded_files or all(not f.filename for f in uploaded_files):
            return jsonify({
                "success": False,
                "error": "请至少上传一个文档文件"
            }), 400
        
        # 创建项目
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f"创建项目: {project.project_id}")
        
        # 保存文件并提取文本
        document_texts = []
        all_text = ""
        
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                # 保存文件到项目目录
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                # 提取文本
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return jsonify({
                "success": False,
                "error": "没有成功处理任何文档，请检查文件格式"
            }), 400
        
        # 保存提取的文本
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"文本提取完成，共 {len(all_text)} 字符")
        
        # 生成本体
        logger.info("调用 LLM 生成本体定义...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        # 保存本体到项目
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f"本体生成完成: {entity_count} 个实体类型, {edge_count} 个关系类型")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"=== 本体生成完成 === 项目ID: {project.project_id}")
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 接口2：构建图谱 ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    接口2：根据project_id构建图谱
    
    请求（JSON）：
        {
            "project_id": "proj_xxxx",  // 必填，来自接口1
            "graph_name": "图谱名称",    // 可选
            "chunk_size": 500,          // 可选，默认500
            "chunk_overlap": 50         // 可选，默认50
        }
        
    返回：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": "图谱构建任务已启动"
            }
        }
    """
    try:
        logger.info("=== 开始构建图谱 ===")
        
        # 检查配置
        errors = []
        if not Config.ZEP_API_KEY:
            errors.append("ZEP_API_KEY未配置")
        if errors:
            logger.error(f"配置错误: {errors}")
            return jsonify({
                "success": False,
                "error": "配置错误: " + "; ".join(errors)
            }), 500
        
        # 解析请求
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f"请求参数: project_id={project_id}")
        
        if not project_id:
            return jsonify({
                "success": False,
                "error": "请提供 project_id"
            }), 400
        
        # 获取项目
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"项目不存在: {project_id}"
            }), 404
        
        # 检查项目状态
        force = data.get('force', False)  # 强制重新构建
        
        if project.status == ProjectStatus.CREATED:
            return jsonify({
                "success": False,
                "error": "项目尚未生成本体，请先调用 /ontology/generate"
            }), 400
        
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return jsonify({
                "success": False,
                "error": "图谱正在构建中，请勿重复提交。如需强制重建，请添加 force: true",
                "task_id": project.graph_build_task_id
            }), 400
        
        # 如果强制重建，重置状态
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None
        
        # 获取配置
        graph_name = data.get('graph_name', project.name or 'MiroFish Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)
        
        # 更新项目配置
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        
        # 获取提取的文本
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return jsonify({
                "success": False,
                "error": "未找到提取的文本内容"
            }), 400
        
        # 获取本体
        ontology = project.ontology
        if not ontology:
            return jsonify({
                "success": False,
                "error": "未找到本体定义"
            }), 400
        
        # 创建异步任务
        task_manager = TaskManager()
        task_id = task_manager.create_task(f"构建图谱: {graph_name}")
        logger.info(f"创建图谱构建任务: task_id={task_id}, project_id={project_id}")
        
        # 更新项目状态
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)
        
        # 启动后台任务
        def build_task():
            build_logger = get_logger('mirofish.build')
            try:
                build_logger.info(f"[{task_id}] 开始构建图谱...")
                task_manager.update_task(
                    task_id, 
                    status=TaskStatus.PROCESSING,
                    message="初始化图谱构建服务..."
                )
                
                # 创建图谱构建服务
                builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
                
                # 分块
                task_manager.update_task(
                    task_id,
                    message="文本分块中...",
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text, 
                    chunk_size=chunk_size, 
                    overlap=chunk_overlap
                )
                total_chunks = len(chunks)
                
                # 创建图谱
                task_manager.update_task(
                    task_id,
                    message="创建Zep图谱...",
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)
                
                # 更新项目的graph_id
                project.graph_id = graph_id
                ProjectManager.save_project(project)
                
                # 设置本体
                task_manager.update_task(
                    task_id,
                    message="设置本体定义...",
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)
                
                # 添加文本（progress_callback 签名是 (msg, progress_ratio)）
                def add_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 40)  # 15% - 55%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                task_manager.update_task(
                    task_id,
                    message=f"开始添加 {total_chunks} 个文本块...",
                    progress=15
                )
                
                episode_uuids = builder.add_text_batches(
                    graph_id, 
                    chunks,
                    batch_size=3,
                    progress_callback=add_progress_callback
                )
                
                # 等待Zep处理完成（查询每个episode的processed状态）
                task_manager.update_task(
                    task_id,
                    message="等待Zep处理数据...",
                    progress=55
                )
                
                def wait_progress_callback(msg, progress_ratio):
                    progress = 55 + int(progress_ratio * 35)  # 55% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )
                
                builder._wait_for_episodes(episode_uuids, wait_progress_callback)
                
                # 获取图谱数据
                task_manager.update_task(
                    task_id,
                    message="获取图谱数据...",
                    progress=95
                )
                graph_data = builder.get_graph_data(graph_id)
                
                # 更新项目状态
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)
                
                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(f"[{task_id}] 图谱构建完成: graph_id={graph_id}, 节点={node_count}, 边={edge_count}")
                
                # 完成
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message="图谱构建完成",
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks
                    }
                )
                
            except Exception as e:
                # 更新项目状态为失败
                build_logger.error(f"[{task_id}] 图谱构建失败: {str(e)}")
                build_logger.debug(traceback.format_exc())
                
                project.status = ProjectStatus.FAILED
                project.error = str(e)
                ProjectManager.save_project(project)
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=f"构建失败: {str(e)}",
                    error=traceback.format_exc()
                )
        
        # 启动后台线程
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": "图谱构建任务已启动，请通过 /task/{task_id} 查询进度"
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 任务查询接口 ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    查询任务状态
    """
    task = TaskManager().get_task(task_id)
    
    if not task:
        return jsonify({
            "success": False,
            "error": f"任务不存在: {task_id}"
        }), 404
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    列出所有任务
    """
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks)
    })


# ============== 图谱数据接口 ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
@cached_response(ttl=900)
def get_graph_data(graph_id: str):
    """
    获取图谱数据（节点和边）
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY未配置"
            }), 500
        
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@graph_bp.route('/search', methods=['POST'])
def search_graph():
    """
    Graph semantic search endpoint

    Request (JSON):
        {
            "graph_id": "mirofish_xxxx",
            "query": "search query",
            "limit": 10,
            "scope": "edges"
        }

    Returns:
        {
            "success": true,
            "data": {
                "facts": [...],
                "edges": [...],
                "nodes": [...],
                "query": "...",
                "total_count": N
            }
        }
    """
    try:
        data = request.get_json() or {}

        graph_id = data.get('graph_id')
        query = data.get('query', '').strip()
        limit = data.get('limit', 10)
        scope = data.get('scope', 'edges')

        if not query:
            return jsonify({
                "success": False,
                "error": "Please provide a search query"
            }), 400

        if not graph_id:
            return jsonify({
                "success": False,
                "error": "Please provide graph_id"
            }), 400

        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": True,
                "data": {
                    "facts": [],
                    "edges": [],
                    "nodes": [],
                    "query": query,
                    "total_count": 0,
                    "demo": True
                }
            })

        from ..services.zep_tools import ZepToolsService

        tools = ZepToolsService()
        result = tools.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit,
            scope=scope
        )

        return jsonify({
            "success": True,
            "data": result.to_dict()
        })

    except Exception as e:
        logger.error(f"Graph search failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============== Community Detection ==============

@graph_bp.route('/communities/<graph_id>', methods=['GET'])
def get_communities(graph_id: str):
    """
    Detect communities in a knowledge graph.
    Returns community clusters with labels, members, topics, and cohesion scores.
    Falls back to demo data when ZEP_API_KEY is not configured.
    """
    try:
        detector = CommunityDetector()

        if not Config.ZEP_API_KEY:
            logger.info("ZEP_API_KEY not configured, returning demo communities")
            demo_data = _get_demo_graph_data()
            result = detector.detect(demo_data['nodes'], demo_data['edges'])
            result['metadata']['demo'] = True
            return jsonify({'success': True, 'data': result})

        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)

        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        result = detector.detect(nodes, edges)

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


def _get_demo_graph_data():
    """Return demo graph data for community detection when no Zep key is available."""
    nodes = [
        {'uuid': 'p1', 'name': 'Enterprise Buyer', 'labels': ['Entity', 'Persona'], 'summary': 'Decision-maker evaluating platform purchases for growth.'},
        {'uuid': 'p2', 'name': 'SMB Founder', 'labels': ['Entity', 'Persona'], 'summary': 'Small business owner seeking affordable support tools.'},
        {'uuid': 'p3', 'name': 'Developer Advocate', 'labels': ['Entity', 'Persona'], 'summary': 'Technical influencer evaluating APIs and integrations.'},
        {'uuid': 'p4', 'name': 'VP of Support', 'labels': ['Entity', 'Persona'], 'summary': 'Senior leader responsible for support team performance.'},
        {'uuid': 'p5', 'name': 'CX Director', 'labels': ['Entity', 'Persona'], 'summary': 'Owns customer experience strategy and CSAT metrics.'},
        {'uuid': 'p6', 'name': 'CFO', 'labels': ['Entity', 'Persona'], 'summary': 'Financial decision-maker focused on ROI and cost reduction.'},
        {'uuid': 't1', 'name': 'Customer Support', 'labels': ['Entity', 'Topic'], 'summary': 'Core product area for ticket management and live chat.'},
        {'uuid': 't2', 'name': 'AI Automation', 'labels': ['Entity', 'Topic'], 'summary': 'ML-powered features that drive efficiency and enable growth.'},
        {'uuid': 't3', 'name': 'Pricing Strategy', 'labels': ['Entity', 'Topic'], 'summary': 'Seat-based vs usage-based pricing models and packaging.'},
        {'uuid': 't4', 'name': 'Fin AI Agent', 'labels': ['Entity', 'Topic'], 'summary': 'AI resolution engine handling frontline support queries.'},
        {'uuid': 't5', 'name': 'Resolution Rate', 'labels': ['Entity', 'Topic'], 'summary': 'Key metric for support queries resolved without escalation.'},
        {'uuid': 't6', 'name': 'Cost Reduction', 'labels': ['Entity', 'Topic'], 'summary': 'Strategies to lower support cost via automation.'},
        {'uuid': 'e1', 'name': 'Product-Led Growth', 'labels': ['Entity', 'Process'], 'summary': 'GTM motion focusing on self-serve onboarding.'},
        {'uuid': 'e2', 'name': 'Sales-Led Motion', 'labels': ['Entity', 'Process'], 'summary': 'Enterprise sales cycle with demos and procurement.'},
        {'uuid': 'e3', 'name': 'ROI Analysis', 'labels': ['Entity', 'Process'], 'summary': 'Quantitative assessment of cost savings and gains.'},
        {'uuid': 'e4', 'name': 'Contract Renewal', 'labels': ['Entity', 'Event'], 'summary': 'Renewal negotiation risk and close opportunity.'},
    ]
    edges = [
        {'source_node_uuid': 'p1', 'target_node_uuid': 't1', 'name': 'evaluates'},
        {'source_node_uuid': 'p1', 'target_node_uuid': 'e2', 'name': 'engages_via'},
        {'source_node_uuid': 'p2', 'target_node_uuid': 'e1', 'name': 'converts_through'},
        {'source_node_uuid': 'p2', 'target_node_uuid': 't3', 'name': 'influenced_by'},
        {'source_node_uuid': 'p3', 'target_node_uuid': 't2', 'name': 'integrates'},
        {'source_node_uuid': 'p3', 'target_node_uuid': 'e1', 'name': 'tests'},
        {'source_node_uuid': 'p4', 'target_node_uuid': 't1', 'name': 'owns'},
        {'source_node_uuid': 'p4', 'target_node_uuid': 't5', 'name': 'monitors'},
        {'source_node_uuid': 'p4', 'target_node_uuid': 't4', 'name': 'depends_on'},
        {'source_node_uuid': 'p5', 'target_node_uuid': 't1', 'name': 'drives'},
        {'source_node_uuid': 'p5', 'target_node_uuid': 't5', 'name': 'monitors'},
        {'source_node_uuid': 'p6', 'target_node_uuid': 't6', 'name': 'requires'},
        {'source_node_uuid': 'p6', 'target_node_uuid': 'e3', 'name': 'requires'},
        {'source_node_uuid': 'p6', 'target_node_uuid': 't3', 'name': 'evaluates'},
        {'source_node_uuid': 't1', 'target_node_uuid': 't2', 'name': 'enhanced_by'},
        {'source_node_uuid': 't2', 'target_node_uuid': 't4', 'name': 'enables'},
        {'source_node_uuid': 't4', 'target_node_uuid': 't5', 'name': 'produces'},
        {'source_node_uuid': 't6', 'target_node_uuid': 't2', 'name': 'depends_on'},
        {'source_node_uuid': 'e2', 'target_node_uuid': 'e4', 'name': 'leads_to'},
        {'source_node_uuid': 'e3', 'target_node_uuid': 't6', 'name': 'validates'},
    ]
    return {'nodes': nodes, 'edges': edges}



@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    删除Zep图谱
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY未配置"
            }), 500

        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        builder.delete_graph(graph_id)

        return jsonify({
            "success": True,
            "message": f"图谱已删除: {graph_id}"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Knowledge Graph API Endpoints ==============


@graph_bp.route('/entities', methods=['GET'])
def list_entities():
    """
    List entities from knowledge graph with optional type filter.

    Query params:
        graph_id: required — the Zep graph to query
        type: optional — filter by entity type label (e.g. "Company", "Product")
    """
    graph_id = request.args.get('graph_id')
    entity_type = request.args.get('type')

    if not is_zep_available() or not graph_id:
        entities = _mock_entities()
        if entity_type:
            entities = [e for e in entities if entity_type in e["labels"]]
        return jsonify({
            "success": True,
            "source": "mock",
            "data": {
                "entities": entities,
                "count": len(entities),
                "entity_types": list({l for e in entities for l in e["labels"] if l not in ("Entity", "Node")}),
            }
        })

    try:
        from ..services.zep_entity_reader import ZepEntityReader
        reader = ZepEntityReader(api_key=Config.ZEP_API_KEY)
        type_filter = [entity_type] if entity_type else None
        result = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=type_filter,
            enrich_with_edges=False,
        )
        entities = [e.to_dict() for e in result.entities]
        return jsonify({
            "success": True,
            "source": "zep",
            "data": {
                "entities": entities,
                "count": result.filtered_count,
                "entity_types": list(result.entity_types),
            }
        })
    except Exception as e:
        logger.error(f"list_entities failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@graph_bp.route('/entities/<name>/relationships', methods=['GET'])
def entity_relationships(name: str):
    """
    Get an entity's relationships by entity name.

    Query params:
        graph_id: required — the Zep graph to query
    """
    graph_id = request.args.get('graph_id')

    if not is_zep_available() or not graph_id:
        edges = _mock_edges()
        related = [e for e in edges if e["source_node_name"] == name or e["target_node_name"] == name]
        return jsonify({
            "success": True,
            "source": "mock",
            "data": {
                "entity_name": name,
                "relationships": related,
                "count": len(related),
            }
        })

    try:
        from ..services.zep_entity_reader import ZepEntityReader
        reader = ZepEntityReader(api_key=Config.ZEP_API_KEY)

        all_nodes = reader.get_all_nodes(graph_id)
        target_node = next((n for n in all_nodes if n["name"] == name), None)
        if not target_node:
            return jsonify({"success": False, "error": f"Entity not found: {name}"}), 404

        all_edges = reader.get_all_edges(graph_id)
        node_map = {n["uuid"]: n["name"] for n in all_nodes}
        relationships = []
        for edge in all_edges:
            if edge["source_node_uuid"] == target_node["uuid"] or edge["target_node_uuid"] == target_node["uuid"]:
                relationships.append({
                    **edge,
                    "source_node_name": node_map.get(edge["source_node_uuid"], ""),
                    "target_node_name": node_map.get(edge["target_node_uuid"], ""),
                })

        return jsonify({
            "success": True,
            "source": "zep",
            "data": {
                "entity_name": name,
                "entity": target_node,
                "relationships": relationships,
                "count": len(relationships),
            }
        })
    except Exception as e:
        logger.error(f"entity_relationships failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@graph_bp.route('/search', methods=['GET'])
def search_knowledge_graph():
    """
    Natural language search over the knowledge graph.

    Query params:
        graph_id: required — the Zep graph to query
        q: required — the search query
        limit: optional — max results (default 10)
    """
    graph_id = request.args.get('graph_id')
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({"success": False, "error": "Query parameter 'q' is required"}), 400

    if not is_zep_available() or not graph_id:
        query_lower = query.lower()
        all_edges = _mock_edges()
        all_entities = _mock_entities()
        matched_edges = [e for e in all_edges if query_lower in e["fact"].lower()][:limit]
        matched_entities = [e for e in all_entities if query_lower in e["name"].lower() or query_lower in e["summary"].lower()][:limit]
        facts = [e["fact"] for e in matched_edges]
        if not facts and not matched_entities:
            facts = [e["fact"] for e in all_edges[:limit]]
            matched_entities = all_entities[:limit]
        return jsonify({
            "success": True,
            "source": "mock",
            "data": {
                "query": query,
                "facts": facts,
                "edges": matched_edges,
                "nodes": matched_entities,
                "total_count": len(facts) + len(matched_entities),
            }
        })

    try:
        from ..services.zep_tools import ZepToolsService
        service = ZepToolsService(api_key=Config.ZEP_API_KEY)
        result = service.search_graph(graph_id=graph_id, query=query, limit=limit)
        return jsonify({
            "success": True,
            "source": "zep",
            "data": result.to_dict(),
        })
    except Exception as e:
        logger.error(f"search_knowledge_graph failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@graph_bp.route('/communities', methods=['GET'])
def get_communities():
    """
    Detect communities/clusters in the knowledge graph.
    Groups entities by type label and detects connected components.

    Query params:
        graph_id: required — the Zep graph to query
    """
    graph_id = request.args.get('graph_id')

    if not is_zep_available() or not graph_id:
        entities = _mock_entities()
        edges = _mock_edges()
        communities = _detect_communities(entities, edges)
        return jsonify({
            "success": True,
            "source": "mock",
            "data": {
                "communities": communities,
                "count": len(communities),
            }
        })

    try:
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        communities = _detect_communities(graph_data["nodes"], graph_data["edges"])
        return jsonify({
            "success": True,
            "source": "zep",
            "data": {
                "communities": communities,
                "count": len(communities),
            }
        })
    except Exception as e:
        logger.error(f"get_communities failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _detect_communities(nodes, edges):
    """
    Build communities from graph data using connected-component analysis.
    Each component becomes a community, labelled by the most common entity type.
    """
    uuid_to_node = {n["uuid"]: n for n in nodes}

    # Build adjacency list
    adj = defaultdict(set)
    for edge in edges:
        src, tgt = edge.get("source_node_uuid"), edge.get("target_node_uuid")
        if src in uuid_to_node and tgt in uuid_to_node:
            adj[src].add(tgt)
            adj[tgt].add(src)

    # BFS to find connected components
    visited = set()
    components = []
    for node in nodes:
        uid = node["uuid"]
        if uid in visited:
            continue
        component = []
        queue = [uid]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(component)

    # Build community objects
    communities = []
    for i, member_uuids in enumerate(components):
        members = [uuid_to_node[u] for u in member_uuids if u in uuid_to_node]
        type_counts = defaultdict(int)
        for m in members:
            for label in m.get("labels", []):
                if label not in ("Entity", "Node"):
                    type_counts[label] += 1
        dominant_type = max(type_counts, key=type_counts.get) if type_counts else "Unknown"
        communities.append({
            "id": i,
            "label": dominant_type,
            "member_count": len(members),
            "members": [{"uuid": m["uuid"], "name": m["name"], "labels": m.get("labels", [])} for m in members],
            "entity_types": dict(type_counts),
        })

    communities.sort(key=lambda c: c["member_count"], reverse=True)
    return communities


@graph_bp.route('/temporal', methods=['GET'])
def get_temporal_facts():
    """
    Temporal facts with optional time range filter.

    Query params:
        graph_id: required — the Zep graph to query
        start: optional — ISO 8601 start date filter
        end: optional — ISO 8601 end date filter
    """
    graph_id = request.args.get('graph_id')
    start_filter = request.args.get('start', '')
    end_filter = request.args.get('end', '')

    if not is_zep_available() or not graph_id:
        edges = _mock_edges()
        filtered = _filter_temporal(edges, start_filter, end_filter)
        return jsonify({
            "success": True,
            "source": "mock",
            "data": {
                "facts": filtered,
                "count": len(filtered),
                "filters": {"start": start_filter or None, "end": end_filter or None},
            }
        })

    try:
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        node_map = {n["uuid"]: n["name"] for n in graph_data["nodes"]}

        temporal_edges = []
        for edge in graph_data["edges"]:
            temporal_edges.append({
                "uuid": edge["uuid"],
                "name": edge.get("name", ""),
                "fact": edge.get("fact", ""),
                "source_node_name": node_map.get(edge["source_node_uuid"], ""),
                "target_node_name": node_map.get(edge["target_node_uuid"], ""),
                "created_at": edge.get("created_at"),
                "valid_at": edge.get("valid_at"),
                "invalid_at": edge.get("invalid_at"),
                "expired_at": edge.get("expired_at"),
            })

        filtered = _filter_temporal(temporal_edges, start_filter, end_filter)
        return jsonify({
            "success": True,
            "source": "zep",
            "data": {
                "facts": filtered,
                "count": len(filtered),
                "filters": {"start": start_filter or None, "end": end_filter or None},
            }
        })
    except Exception as e:
        logger.error(f"get_temporal_facts failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def _filter_temporal(edges, start_filter, end_filter):
    """Filter edges by time range using valid_at / created_at fields."""
    if not start_filter and not end_filter:
        return edges

    filtered = []
    for edge in edges:
        ts = edge.get("valid_at") or edge.get("created_at") or ""
        ts_str = str(ts) if ts else ""
        if not ts_str:
            continue
        if start_filter and ts_str < start_filter:
            continue
        if end_filter and ts_str > end_filter:
            continue
        filtered.append(edge)
    return filtered


@graph_bp.route('/stats', methods=['GET'])
def get_graph_stats():
    """
    Graph statistics: entity count, relationship count, community count, type breakdown.

    Query params:
        graph_id: required — the Zep graph to query
    """
    graph_id = request.args.get('graph_id')

    if not is_zep_available() or not graph_id:
        entities = _mock_entities()
        edges = _mock_edges()
        communities = _detect_communities(entities, edges)
        type_counts = defaultdict(int)
        for e in entities:
            for label in e.get("labels", []):
                if label not in ("Entity", "Node"):
                    type_counts[label] += 1
        relationship_types = defaultdict(int)
        for edge in edges:
            relationship_types[edge["name"]] += 1
        return jsonify({
            "success": True,
            "source": "mock",
            "data": {
                "entity_count": len(entities),
                "relationship_count": len(edges),
                "community_count": len(communities),
                "entity_types": dict(type_counts),
                "relationship_types": dict(relationship_types),
            }
        })

    try:
        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        communities = _detect_communities(nodes, edges)

        type_counts = defaultdict(int)
        for n in nodes:
            for label in n.get("labels", []):
                if label not in ("Entity", "Node"):
                    type_counts[label] += 1
        relationship_types = defaultdict(int)
        for edge in edges:
            relationship_types[edge.get("name", "unknown")] += 1

        return jsonify({
            "success": True,
            "source": "zep",
            "data": {
                "entity_count": graph_data["node_count"],
                "relationship_count": graph_data["edge_count"],
                "community_count": len(communities),
                "entity_types": dict(type_counts),
                "relationship_types": dict(relationship_types),
            }
        })
    except Exception as e:
        logger.error(f"get_graph_stats failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== Topic Distribution (Treemap) ==============

TOPIC_DISTRIBUTION_DEMO = {
    "name": "Topics",
    "children": [
        {
            "name": "Product",
            "children": [
                {"name": "AI Agent Capabilities", "value": 28},
                {"name": "Pricing & Packaging", "value": 19},
                {"name": "Platform Integration", "value": 14},
                {"name": "Self-Serve Onboarding", "value": 8},
            ],
        },
        {
            "name": "Market",
            "children": [
                {"name": "Competitive Displacement", "value": 22},
                {"name": "Enterprise Expansion", "value": 16},
                {"name": "SMB Acquisition", "value": 11},
            ],
        },
        {
            "name": "Customer",
            "children": [
                {"name": "Support Automation ROI", "value": 25},
                {"name": "Churn Risk Signals", "value": 13},
                {"name": "NPS & Satisfaction", "value": 9},
            ],
        },
        {
            "name": "Operations",
            "children": [
                {"name": "Sales Cycle Length", "value": 17},
                {"name": "Pipeline Velocity", "value": 12},
                {"name": "Rep Enablement", "value": 6},
            ],
        },
    ],
}

GENERIC_LABELS = {"Entity", "Node"}


def _compute_topic_distribution(graph_data):
    """Build treemap hierarchy from graph nodes grouped by label with degree-based weights."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Compute degree centrality per node
    degree = {}
    for n in nodes:
        degree[n["uuid"]] = 0
    for e in edges:
        src = e.get("source_node_uuid")
        tgt = e.get("target_node_uuid")
        if src in degree:
            degree[src] += 1
        if tgt in degree:
            degree[tgt] += 1

    # Group nodes by their primary label
    groups = {}
    for n in nodes:
        meaningful = [l for l in (n.get("labels") or []) if l not in GENERIC_LABELS]
        label = meaningful[0] if meaningful else "Other"
        if label not in groups:
            groups[label] = []
        weight = 1 + degree.get(n["uuid"], 0)
        groups[label].append({
            "name": n.get("name") or n["uuid"][:8],
            "value": weight,
        })

    # Sort children within each group by value descending
    children = []
    for label, items in sorted(groups.items(), key=lambda x: -sum(i["value"] for i in x[1])):
        items.sort(key=lambda x: -x["value"])
        children.append({"name": label, "children": items})

    return {"name": "Topics", "children": children}


@graph_bp.route('/topic-distribution/<graph_id>', methods=['GET'])
def get_topic_distribution(graph_id: str):
    """
    Get topic distribution data for treemap visualization.
    Falls back to demo data when ZEP_API_KEY is not configured.
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": True,
                "data": TOPIC_DISTRIBUTION_DEMO,
                "demo": True,
            })

        builder = GraphBuilderService(api_key=Config.ZEP_API_KEY)
        graph_data = builder.get_graph_data(graph_id)
        distribution = _compute_topic_distribution(graph_data)

        return jsonify({
            "success": True,
            "data": distribution,
            "demo": False,
        })

    except Exception as e:
        logger.warning(f"Failed to compute topic distribution, falling back to demo: {e}")
        return jsonify({
            "success": True,
            "data": TOPIC_DISTRIBUTION_DEMO,
            "demo": True,
        })
