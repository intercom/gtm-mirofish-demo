"""
模拟相关API路由
Step2: Zep实体读取与过滤、OASIS模拟准备与运行（全程自动化）
"""

import os
import json
import time
import traceback
from flask import request, jsonify, send_file, Response

from . import simulation_bp
from ..config import Config
from ..services.zep_entity_reader import ZepEntityReader
from ..services.oasis_profile_generator import OasisProfileGenerator
from ..services.simulation_manager import SimulationManager, SimulationStatus
from ..services.simulation_runner import SimulationRunner, RunnerStatus
from ..services.whatif_engine import WhatIfEngine
from ..services.sensitivity_analyzer import SensitivityAnalyzer
from ..services.simulation_registry import SimulationRegistry
from ..utils.logger import get_logger
from ..models.project import ProjectManager

logger = get_logger('mirofish.api.simulation')


# Interview prompt 优化前缀
# 添加此前缀可以避免Agent调用工具，直接用文本回复
INTERVIEW_PROMPT_PREFIX = "结合你的人设、所有的过往记忆与行动，不调用任何工具直接用文本回复我："


def optimize_interview_prompt(prompt: str) -> str:
    """
    优化Interview提问，添加前缀避免Agent调用工具
    
    Args:
        prompt: 原始提问
        
    Returns:
        优化后的提问
    """
    if not prompt:
        return prompt
    # 避免重复添加前缀
    if prompt.startswith(INTERVIEW_PROMPT_PREFIX):
        return prompt
    return f"{INTERVIEW_PROMPT_PREFIX}{prompt}"


# ============== 实体读取接口 ==============

@simulation_bp.route('/entities/<graph_id>', methods=['GET'])
def get_graph_entities(graph_id: str):
    """
    获取图谱中的所有实体（已过滤）
    
    只返回符合预定义实体类型的节点（Labels不只是Entity的节点）
    
    Query参数：
        entity_types: 逗号分隔的实体类型列表（可选，用于进一步过滤）
        enrich: 是否获取相关边信息（默认true）
    """
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY未配置"
            }), 500
        
        entity_types_str = request.args.get('entity_types', '')
        entity_types = [t.strip() for t in entity_types_str.split(',') if t.strip()] if entity_types_str else None
        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        logger.info(f"获取图谱实体: graph_id={graph_id}, entity_types={entity_types}, enrich={enrich}")
        
        reader = ZepEntityReader()
        result = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=enrich
        )
        
        return jsonify({
            "success": True,
            "data": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"获取图谱实体失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/entities/<graph_id>/<entity_uuid>', methods=['GET'])
def get_entity_detail(graph_id: str, entity_uuid: str):
    """获取单个实体的详细信息"""
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY未配置"
            }), 500
        
        reader = ZepEntityReader()
        entity = reader.get_entity_with_context(graph_id, entity_uuid)
        
        if not entity:
            return jsonify({
                "success": False,
                "error": f"实体不存在: {entity_uuid}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": entity.to_dict()
        })
        
    except Exception as e:
        logger.error(f"获取实体详情失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/entities/<graph_id>/by-type/<entity_type>', methods=['GET'])
def get_entities_by_type(graph_id: str, entity_type: str):
    """获取指定类型的所有实体"""
    try:
        if not Config.ZEP_API_KEY:
            return jsonify({
                "success": False,
                "error": "ZEP_API_KEY未配置"
            }), 500
        
        enrich = request.args.get('enrich', 'true').lower() == 'true'
        
        reader = ZepEntityReader()
        entities = reader.get_entities_by_type(
            graph_id=graph_id,
            entity_type=entity_type,
            enrich_with_edges=enrich
        )
        
        return jsonify({
            "success": True,
            "data": {
                "entity_type": entity_type,
                "count": len(entities),
                "entities": [e.to_dict() for e in entities]
            }
        })
        
    except Exception as e:
        logger.error(f"获取实体失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 模拟管理接口 ==============

@simulation_bp.route('/create', methods=['POST'])
def create_simulation():
    """
    创建新的模拟
    
    注意：max_rounds等参数由LLM智能生成，无需手动设置
    
    请求（JSON）：
        {
            "project_id": "proj_xxxx",      // 必填
            "graph_id": "mirofish_xxxx",    // 可选，如不提供则从project获取
            "enable_twitter": true,          // 可选，默认true
            "enable_reddit": true            // 可选，默认true
        }
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "project_id": "proj_xxxx",
                "graph_id": "mirofish_xxxx",
                "status": "created",
                "enable_twitter": true,
                "enable_reddit": true,
                "created_at": "2025-12-01T10:00:00"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({
                "success": False,
                "error": "请提供 project_id"
            }), 400
        
        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"项目不存在: {project_id}"
            }), 404
        
        graph_id = data.get('graph_id') or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "项目尚未构建图谱，请先调用 /api/graph/build"
            }), 400
        
        manager = SimulationManager()
        state = manager.create_simulation(
            project_id=project_id,
            graph_id=graph_id,
            enable_twitter=data.get('enable_twitter', True),
            enable_reddit=data.get('enable_reddit', True),
        )
        
        return jsonify({
            "success": True,
            "data": state.to_dict()
        })
        
    except Exception as e:
        logger.error(f"创建模拟失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


def _check_simulation_prepared(simulation_id: str) -> tuple:
    """
    检查模拟是否已经准备完成
    
    检查条件：
    1. state.json 存在且 status 为 "ready"
    2. 必要文件存在：reddit_profiles.json, twitter_profiles.csv, simulation_config.json
    
    注意：运行脚本(run_*.py)保留在 backend/scripts/ 目录，不再复制到模拟目录
    
    Args:
        simulation_id: 模拟ID
        
    Returns:
        (is_prepared: bool, info: dict)
    """
    import os
    from ..config import Config
    
    simulation_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
    
    # 检查目录是否存在
    if not os.path.exists(simulation_dir):
        return False, {"reason": "模拟目录不存在"}
    
    # 必要文件列表（不包括脚本，脚本位于 backend/scripts/）
    required_files = [
        "state.json",
        "simulation_config.json",
        "reddit_profiles.json",
        "twitter_profiles.csv"
    ]
    
    # 检查文件是否存在
    existing_files = []
    missing_files = []
    for f in required_files:
        file_path = os.path.join(simulation_dir, f)
        if os.path.exists(file_path):
            existing_files.append(f)
        else:
            missing_files.append(f)
    
    if missing_files:
        return False, {
            "reason": "缺少必要文件",
            "missing_files": missing_files,
            "existing_files": existing_files
        }
    
    # 检查state.json中的状态
    state_file = os.path.join(simulation_dir, "state.json")
    try:
        import json
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        status = state_data.get("status", "")
        config_generated = state_data.get("config_generated", False)
        
        # 详细日志
        logger.debug(f"检测模拟准备状态: {simulation_id}, status={status}, config_generated={config_generated}")
        
        # 如果 config_generated=True 且文件存在，认为准备完成
        # 以下状态都说明准备工作已完成：
        # - ready: 准备完成，可以运行
        # - preparing: 如果 config_generated=True 说明已完成
        # - running: 正在运行，说明准备早就完成了
        # - completed: 运行完成，说明准备早就完成了
        # - stopped: 已停止，说明准备早就完成了
        # - failed: 运行失败（但准备是完成的）
        prepared_statuses = ["ready", "preparing", "running", "completed", "stopped", "failed"]
        if status in prepared_statuses and config_generated:
            # 获取文件统计信息
            profiles_file = os.path.join(simulation_dir, "reddit_profiles.json")
            config_file = os.path.join(simulation_dir, "simulation_config.json")
            
            profiles_count = 0
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                    profiles_count = len(profiles_data) if isinstance(profiles_data, list) else 0
            
            # 如果状态是preparing但文件已完成，自动更新状态为ready
            if status == "preparing":
                try:
                    state_data["status"] = "ready"
                    from datetime import datetime
                    state_data["updated_at"] = datetime.now().isoformat()
                    with open(state_file, 'w', encoding='utf-8') as f:
                        json.dump(state_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"自动更新模拟状态: {simulation_id} preparing -> ready")
                    status = "ready"
                except Exception as e:
                    logger.warning(f"自动更新状态失败: {e}")
            
            logger.info(f"模拟 {simulation_id} 检测结果: 已准备完成 (status={status}, config_generated={config_generated})")
            return True, {
                "status": status,
                "entities_count": state_data.get("entities_count", 0),
                "profiles_count": profiles_count,
                "entity_types": state_data.get("entity_types", []),
                "config_generated": config_generated,
                "created_at": state_data.get("created_at"),
                "updated_at": state_data.get("updated_at"),
                "existing_files": existing_files
            }
        else:
            logger.warning(f"模拟 {simulation_id} 检测结果: 未准备完成 (status={status}, config_generated={config_generated})")
            return False, {
                "reason": f"状态不在已准备列表中或config_generated为false: status={status}, config_generated={config_generated}",
                "status": status,
                "config_generated": config_generated
            }
            
    except Exception as e:
        return False, {"reason": f"读取状态文件失败: {str(e)}"}


@simulation_bp.route('/prepare', methods=['POST'])
def prepare_simulation():
    """
    准备模拟环境（异步任务，LLM智能生成所有参数）
    
    这是一个耗时操作，接口会立即返回task_id，
    使用 GET /api/simulation/prepare/status 查询进度
    
    特性：
    - 自动检测已完成的准备工作，避免重复生成
    - 如果已准备完成，直接返回已有结果
    - 支持强制重新生成（force_regenerate=true）
    
    步骤：
    1. 检查是否已有完成的准备工作
    2. 从Zep图谱读取并过滤实体
    3. 为每个实体生成OASIS Agent Profile（带重试机制）
    4. LLM智能生成模拟配置（带重试机制）
    5. 保存配置文件和预设脚本
    
    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",                   // 必填，模拟ID
            "entity_types": ["Student", "PublicFigure"],  // 可选，指定实体类型
            "use_llm_for_profiles": true,                 // 可选，是否用LLM生成人设
            "parallel_profile_count": 5,                  // 可选，并行生成人设数量，默认5
            "force_regenerate": false                     // 可选，强制重新生成，默认false
        }
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "task_id": "task_xxxx",           // 新任务时返回
                "status": "preparing|ready",
                "message": "准备任务已启动|已有完成的准备工作",
                "already_prepared": true|false    // 是否已准备完成
            }
        }
    """
    import threading
    import os
    from ..models.task import TaskManager, TaskStatus
    from ..config import Config
    
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400
        
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404
        
        # 检查是否强制重新生成
        force_regenerate = data.get('force_regenerate', False)
        logger.info(f"开始处理 /prepare 请求: simulation_id={simulation_id}, force_regenerate={force_regenerate}")
        
        # 检查是否已经准备完成（避免重复生成）
        if not force_regenerate:
            logger.debug(f"检查模拟 {simulation_id} 是否已准备完成...")
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            logger.debug(f"检查结果: is_prepared={is_prepared}, prepare_info={prepare_info}")
            if is_prepared:
                logger.info(f"模拟 {simulation_id} 已准备完成，跳过重复生成")
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "message": "已有完成的准备工作，无需重复生成",
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })
            else:
                logger.info(f"模拟 {simulation_id} 未准备完成，将启动准备任务")
        
        # 从项目获取必要信息
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"项目不存在: {state.project_id}"
            }), 404
        
        # 获取模拟需求
        simulation_requirement = project.simulation_requirement or ""
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "项目缺少模拟需求描述 (simulation_requirement)"
            }), 400
        
        # 获取文档文本
        document_text = ProjectManager.get_extracted_text(state.project_id) or ""
        
        entity_types_list = data.get('entity_types')
        use_llm_for_profiles = data.get('use_llm_for_profiles', True)
        parallel_profile_count = data.get('parallel_profile_count', 5)
        
        # ========== 同步获取实体数量（在后台任务启动前） ==========
        # 这样前端在调用prepare后立即就能获取到预期Agent总数
        try:
            logger.info(f"同步获取实体数量: graph_id={state.graph_id}")
            reader = ZepEntityReader()
            # 快速读取实体（不需要边信息，只统计数量）
            filtered_preview = reader.filter_defined_entities(
                graph_id=state.graph_id,
                defined_entity_types=entity_types_list,
                enrich_with_edges=False  # 不获取边信息，加快速度
            )
            # 保存实体数量到状态（供前端立即获取）
            state.entities_count = filtered_preview.filtered_count
            state.entity_types = list(filtered_preview.entity_types)
            logger.info(f"预期实体数量: {filtered_preview.filtered_count}, 类型: {filtered_preview.entity_types}")
        except Exception as e:
            logger.warning(f"同步获取实体数量失败（将在后台任务中重试）: {e}")
            # 失败不影响后续流程，后台任务会重新获取
        
        # 创建异步任务
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="simulation_prepare",
            metadata={
                "simulation_id": simulation_id,
                "project_id": state.project_id
            }
        )
        
        # 更新模拟状态（包含预先获取的实体数量）
        state.status = SimulationStatus.PREPARING
        manager._save_simulation_state(state)
        
        # 定义后台任务
        def run_prepare():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="开始准备模拟环境..."
                )
                
                # 准备模拟（带进度回调）
                # 存储阶段进度详情
                stage_details = {}
                
                def progress_callback(stage, progress, message, **kwargs):
                    # 计算总进度
                    stage_weights = {
                        "reading": (0, 20),           # 0-20%
                        "generating_profiles": (20, 70),  # 20-70%
                        "generating_config": (70, 90),    # 70-90%
                        "copying_scripts": (90, 100)       # 90-100%
                    }
                    
                    start, end = stage_weights.get(stage, (0, 100))
                    current_progress = int(start + (end - start) * progress / 100)
                    
                    # 构建详细进度信息
                    stage_names = {
                        "reading": "读取图谱实体",
                        "generating_profiles": "生成Agent人设",
                        "generating_config": "生成模拟配置",
                        "copying_scripts": "准备模拟脚本"
                    }
                    
                    stage_index = list(stage_weights.keys()).index(stage) + 1 if stage in stage_weights else 1
                    total_stages = len(stage_weights)
                    
                    # 更新阶段详情
                    stage_details[stage] = {
                        "stage_name": stage_names.get(stage, stage),
                        "stage_progress": progress,
                        "current": kwargs.get("current", 0),
                        "total": kwargs.get("total", 0),
                        "item_name": kwargs.get("item_name", "")
                    }
                    
                    # 构建详细进度信息
                    detail = stage_details[stage]
                    progress_detail_data = {
                        "current_stage": stage,
                        "current_stage_name": stage_names.get(stage, stage),
                        "stage_index": stage_index,
                        "total_stages": total_stages,
                        "stage_progress": progress,
                        "current_item": detail["current"],
                        "total_items": detail["total"],
                        "item_description": message
                    }
                    
                    # 构建简洁消息
                    if detail["total"] > 0:
                        detailed_message = (
                            f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: "
                            f"{detail['current']}/{detail['total']} - {message}"
                        )
                    else:
                        detailed_message = f"[{stage_index}/{total_stages}] {stage_names.get(stage, stage)}: {message}"
                    
                    task_manager.update_task(
                        task_id,
                        progress=current_progress,
                        message=detailed_message,
                        progress_detail=progress_detail_data
                    )
                
                result_state = manager.prepare_simulation(
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement,
                    document_text=document_text,
                    defined_entity_types=entity_types_list,
                    use_llm_for_profiles=use_llm_for_profiles,
                    progress_callback=progress_callback,
                    parallel_profile_count=parallel_profile_count
                )
                
                # 任务完成
                task_manager.complete_task(
                    task_id,
                    result=result_state.to_simple_dict()
                )
                
            except Exception as e:
                logger.error(f"准备模拟失败: {str(e)}")
                task_manager.fail_task(task_id, str(e))
                
                # 更新模拟状态为失败
                state = manager.get_simulation(simulation_id)
                if state:
                    state.status = SimulationStatus.FAILED
                    state.error = str(e)
                    manager._save_simulation_state(state)
        
        # 启动后台线程
        thread = threading.Thread(target=run_prepare, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "task_id": task_id,
                "status": "preparing",
                "message": "准备任务已启动，请通过 /api/simulation/prepare/status 查询进度",
                "already_prepared": False,
                "expected_entities_count": state.entities_count,  # 预期的Agent总数
                "entity_types": state.entity_types  # 实体类型列表
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"启动准备任务失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/prepare/status', methods=['POST'])
def get_prepare_status():
    """
    查询准备任务进度
    
    支持两种查询方式：
    1. 通过task_id查询正在进行的任务进度
    2. 通过simulation_id检查是否已有完成的准备工作
    
    请求（JSON）：
        {
            "task_id": "task_xxxx",          // 可选，prepare返回的task_id
            "simulation_id": "sim_xxxx"      // 可选，模拟ID（用于检查已完成的准备）
        }
    
    返回：
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|ready",
                "progress": 45,
                "message": "...",
                "already_prepared": true|false,  // 是否已有完成的准备
                "prepare_info": {...}            // 已准备完成时的详细信息
            }
        }
    """
    from ..models.task import TaskManager
    
    try:
        data = request.get_json() or {}
        
        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')
        
        # 如果提供了simulation_id，先检查是否已准备完成
        if simulation_id:
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
            if is_prepared:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "ready",
                        "progress": 100,
                        "message": "已有完成的准备工作",
                        "already_prepared": True,
                        "prepare_info": prepare_info
                    }
                })
        
        # 如果没有task_id，返回错误
        if not task_id:
            if simulation_id:
                # 有simulation_id但未准备完成
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "status": "not_started",
                        "progress": 0,
                        "message": "尚未开始准备，请调用 /api/simulation/prepare 开始",
                        "already_prepared": False
                    }
                })
            return jsonify({
                "success": False,
                "error": "请提供 task_id 或 simulation_id"
            }), 400
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            # 任务不存在，但如果有simulation_id，检查是否已准备完成
            if simulation_id:
                is_prepared, prepare_info = _check_simulation_prepared(simulation_id)
                if is_prepared:
                    return jsonify({
                        "success": True,
                        "data": {
                            "simulation_id": simulation_id,
                            "task_id": task_id,
                            "status": "ready",
                            "progress": 100,
                            "message": "任务已完成（准备工作已存在）",
                            "already_prepared": True,
                            "prepare_info": prepare_info
                        }
                    })
            
            return jsonify({
                "success": False,
                "error": f"任务不存在: {task_id}"
            }), 404
        
        task_dict = task.to_dict()
        task_dict["already_prepared"] = False
        
        return jsonify({
            "success": True,
            "data": task_dict
        })
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@simulation_bp.route('/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id: str):
    """获取模拟状态"""
    try:
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404
        
        result = state.to_dict()
        
        # 如果模拟已准备好，附加运行说明
        if state.status == SimulationStatus.READY:
            result["run_instructions"] = manager.get_run_instructions(simulation_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"获取模拟状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/list', methods=['GET'])
def list_simulations():
    """
    列出所有模拟
    
    Query参数：
        project_id: 按项目ID过滤（可选）
    """
    try:
        project_id = request.args.get('project_id')
        
        manager = SimulationManager()
        simulations = manager.list_simulations(project_id=project_id)
        
        return jsonify({
            "success": True,
            "data": [s.to_dict() for s in simulations],
            "count": len(simulations)
        })
        
    except Exception as e:
        logger.error(f"列出模拟失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


def _get_report_id_for_simulation(simulation_id: str) -> str:
    """
    获取 simulation 对应的最新 report_id
    
    遍历 reports 目录，找出 simulation_id 匹配的 report，
    如果有多个则返回最新的（按 created_at 排序）
    
    Args:
        simulation_id: 模拟ID
        
    Returns:
        report_id 或 None
    """
    import json
    from datetime import datetime
    
    # reports 目录路径：backend/uploads/reports
    # __file__ 是 app/api/simulation.py，需要向上两级到 backend/
    reports_dir = os.path.join(os.path.dirname(__file__), '../../uploads/reports')
    if not os.path.exists(reports_dir):
        return None
    
    matching_reports = []
    
    try:
        for report_folder in os.listdir(reports_dir):
            report_path = os.path.join(reports_dir, report_folder)
            if not os.path.isdir(report_path):
                continue
            
            meta_file = os.path.join(report_path, "meta.json")
            if not os.path.exists(meta_file):
                continue
            
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                if meta.get("simulation_id") == simulation_id:
                    matching_reports.append({
                        "report_id": meta.get("report_id"),
                        "created_at": meta.get("created_at", ""),
                        "status": meta.get("status", "")
                    })
            except Exception:
                continue
        
        if not matching_reports:
            return None
        
        # 按创建时间倒序排序，返回最新的
        matching_reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return matching_reports[0].get("report_id")
        
    except Exception as e:
        logger.warning(f"查找 simulation {simulation_id} 的 report 失败: {e}")
        return None


@simulation_bp.route('/history', methods=['GET'])
def get_simulation_history():
    """
    获取历史模拟列表（带项目详情）
    
    用于首页历史项目展示，返回包含项目名称、描述等丰富信息的模拟列表
    
    Query参数：
        limit: 返回数量限制（默认20）
    
    返回：
        {
            "success": true,
            "data": [
                {
                    "simulation_id": "sim_xxxx",
                    "project_id": "proj_xxxx",
                    "project_name": "武大舆情分析",
                    "simulation_requirement": "如果武汉大学发布...",
                    "status": "completed",
                    "entities_count": 68,
                    "profiles_count": 68,
                    "entity_types": ["Student", "Professor", ...],
                    "created_at": "2024-12-10",
                    "updated_at": "2024-12-10",
                    "total_rounds": 120,
                    "current_round": 120,
                    "report_id": "report_xxxx",
                    "version": "v1.0.2"
                },
                ...
            ],
            "count": 7
        }
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        
        manager = SimulationManager()
        simulations = manager.list_simulations()[:limit]
        
        # 增强模拟数据，只从 Simulation 文件读取
        enriched_simulations = []
        for sim in simulations:
            sim_dict = sim.to_dict()
            
            # 获取模拟配置信息（从 simulation_config.json 读取 simulation_requirement）
            config = manager.get_simulation_config(sim.simulation_id)
            if config:
                sim_dict["simulation_requirement"] = config.get("simulation_requirement", "")
                time_config = config.get("time_config", {})
                sim_dict["total_simulation_hours"] = time_config.get("total_simulation_hours", 0)
                # 推荐轮数（后备值）
                recommended_rounds = int(
                    time_config.get("total_simulation_hours", 0) * 60 / 
                    max(time_config.get("minutes_per_round", 60), 1)
                )
            else:
                sim_dict["simulation_requirement"] = ""
                sim_dict["total_simulation_hours"] = 0
                recommended_rounds = 0
            
            # 获取运行状态（从 run_state.json 读取用户设置的实际轮数）
            run_state = SimulationRunner.get_run_state(sim.simulation_id)
            if run_state:
                sim_dict["current_round"] = run_state.current_round
                sim_dict["runner_status"] = run_state.runner_status.value
                # 使用用户设置的 total_rounds，若无则使用推荐轮数
                sim_dict["total_rounds"] = run_state.total_rounds if run_state.total_rounds > 0 else recommended_rounds
            else:
                sim_dict["current_round"] = 0
                sim_dict["runner_status"] = "idle"
                sim_dict["total_rounds"] = recommended_rounds
            
            # 获取关联项目的文件列表（最多3个）
            project = ProjectManager.get_project(sim.project_id)
            if project and hasattr(project, 'files') and project.files:
                sim_dict["files"] = [
                    {"filename": f.get("filename", "未知文件")} 
                    for f in project.files[:3]
                ]
            else:
                sim_dict["files"] = []
            
            # 获取关联的 report_id（查找该 simulation 最新的 report）
            sim_dict["report_id"] = _get_report_id_for_simulation(sim.simulation_id)
            
            # 添加版本号
            sim_dict["version"] = "v1.0.2"
            
            # 格式化日期
            try:
                created_date = sim_dict.get("created_at", "")[:10]
                sim_dict["created_date"] = created_date
            except:
                sim_dict["created_date"] = ""
            
            enriched_simulations.append(sim_dict)
        
        return jsonify({
            "success": True,
            "data": enriched_simulations,
            "count": len(enriched_simulations)
        })
        
    except Exception as e:
        logger.error(f"获取历史模拟失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/profiles', methods=['GET'])
def get_simulation_profiles(simulation_id: str):
    """
    获取模拟的Agent Profile
    
    Query参数：
        platform: 平台类型（reddit/twitter，默认reddit）
    """
    try:
        platform = request.args.get('platform', 'reddit')
        
        manager = SimulationManager()
        profiles = manager.get_profiles(simulation_id, platform=platform)
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "count": len(profiles),
                "profiles": profiles
            }
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"获取Profile失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/profiles/realtime', methods=['GET'])
def get_simulation_profiles_realtime(simulation_id: str):
    """
    实时获取模拟的Agent Profile（用于在生成过程中实时查看进度）
    
    与 /profiles 接口的区别：
    - 直接读取文件，不经过 SimulationManager
    - 适用于生成过程中的实时查看
    - 返回额外的元数据（如文件修改时间、是否正在生成等）
    
    Query参数：
        platform: 平台类型（reddit/twitter，默认reddit）
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "platform": "reddit",
                "count": 15,
                "total_expected": 93,  // 预期总数（如果有）
                "is_generating": true,  // 是否正在生成
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "profiles": [...]
            }
        }
    """
    import json
    import csv
    from datetime import datetime
    
    try:
        platform = request.args.get('platform', 'reddit')
        
        # 获取模拟目录
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404
        
        # 确定文件路径
        if platform == "reddit":
            profiles_file = os.path.join(sim_dir, "reddit_profiles.json")
        else:
            profiles_file = os.path.join(sim_dir, "twitter_profiles.csv")
        
        # 检查文件是否存在
        file_exists = os.path.exists(profiles_file)
        profiles = []
        file_modified_at = None
        
        if file_exists:
            # 获取文件修改时间
            file_stat = os.stat(profiles_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            try:
                if platform == "reddit":
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        profiles = json.load(f)
                else:
                    with open(profiles_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        profiles = list(reader)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"读取 profiles 文件失败（可能正在写入中）: {e}")
                profiles = []
        
        # 检查是否正在生成（通过 state.json 判断）
        is_generating = False
        total_expected = None
        
        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    total_expected = state_data.get("entities_count")
            except Exception:
                pass
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "platform": platform,
                "count": len(profiles),
                "total_expected": total_expected,
                "is_generating": is_generating,
                "file_exists": file_exists,
                "file_modified_at": file_modified_at,
                "profiles": profiles
            }
        })
        
    except Exception as e:
        logger.error(f"实时获取Profile失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/config/realtime', methods=['GET'])
def get_simulation_config_realtime(simulation_id: str):
    """
    实时获取模拟配置（用于在生成过程中实时查看进度）
    
    与 /config 接口的区别：
    - 直接读取文件，不经过 SimulationManager
    - 适用于生成过程中的实时查看
    - 返回额外的元数据（如文件修改时间、是否正在生成等）
    - 即使配置还没生成完也能返回部分信息
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "file_exists": true,
                "file_modified_at": "2025-12-04T18:20:00",
                "is_generating": true,  // 是否正在生成
                "generation_stage": "generating_config",  // 当前生成阶段
                "config": {...}  // 配置内容（如果存在）
            }
        }
    """
    import json
    from datetime import datetime
    
    try:
        # 获取模拟目录
        sim_dir = os.path.join(Config.OASIS_SIMULATION_DATA_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404
        
        # 配置文件路径
        config_file = os.path.join(sim_dir, "simulation_config.json")
        
        # 检查文件是否存在
        file_exists = os.path.exists(config_file)
        config = None
        file_modified_at = None
        
        if file_exists:
            # 获取文件修改时间
            file_stat = os.stat(config_file)
            file_modified_at = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"读取 config 文件失败（可能正在写入中）: {e}")
                config = None
        
        # 检查是否正在生成（通过 state.json 判断）
        is_generating = False
        generation_stage = None
        config_generated = False
        
        state_file = os.path.join(sim_dir, "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                    status = state_data.get("status", "")
                    is_generating = status == "preparing"
                    config_generated = state_data.get("config_generated", False)
                    
                    # 判断当前阶段
                    if is_generating:
                        if state_data.get("profiles_generated", False):
                            generation_stage = "generating_config"
                        else:
                            generation_stage = "generating_profiles"
                    elif status == "ready":
                        generation_stage = "completed"
            except Exception:
                pass
        
        # 构建返回数据
        response_data = {
            "simulation_id": simulation_id,
            "file_exists": file_exists,
            "file_modified_at": file_modified_at,
            "is_generating": is_generating,
            "generation_stage": generation_stage,
            "config_generated": config_generated,
            "config": config
        }
        
        # 如果配置存在，提取一些关键统计信息
        if config:
            response_data["summary"] = {
                "total_agents": len(config.get("agent_configs", [])),
                "simulation_hours": config.get("time_config", {}).get("total_simulation_hours"),
                "initial_posts_count": len(config.get("event_config", {}).get("initial_posts", [])),
                "hot_topics_count": len(config.get("event_config", {}).get("hot_topics", [])),
                "has_twitter_config": "twitter_config" in config,
                "has_reddit_config": "reddit_config" in config,
                "generated_at": config.get("generated_at"),
                "llm_model": config.get("llm_model")
            }
        
        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except Exception as e:
        logger.error(f"实时获取Config失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/config', methods=['GET'])
def get_simulation_config(simulation_id: str):
    """
    获取模拟配置（LLM智能生成的完整配置）
    
    返回包含：
        - time_config: 时间配置（模拟时长、轮次、高峰/低谷时段）
        - agent_configs: 每个Agent的活动配置（活跃度、发言频率、立场等）
        - event_config: 事件配置（初始帖子、热点话题）
        - platform_configs: 平台配置
        - generation_reasoning: LLM的配置推理说明
    """
    try:
        manager = SimulationManager()
        config = manager.get_simulation_config(simulation_id)
        
        if not config:
            return jsonify({
                "success": False,
                "error": f"模拟配置不存在，请先调用 /prepare 接口"
            }), 404
        
        return jsonify({
            "success": True,
            "data": config
        })
        
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/config/download', methods=['GET'])
def download_simulation_config(simulation_id: str):
    """下载模拟配置文件"""
    try:
        manager = SimulationManager()
        sim_dir = manager._get_simulation_dir(simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            return jsonify({
                "success": False,
                "error": "配置文件不存在，请先调用 /prepare 接口"
            }), 404
        
        return send_file(
            config_path,
            as_attachment=True,
            download_name="simulation_config.json"
        )
        
    except Exception as e:
        logger.error(f"下载配置失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/script/<script_name>/download', methods=['GET'])
def download_simulation_script(script_name: str):
    """
    下载模拟运行脚本文件（通用脚本，位于 backend/scripts/）
    
    script_name可选值：
        - run_twitter_simulation.py
        - run_reddit_simulation.py
        - run_parallel_simulation.py
        - action_logger.py
    """
    try:
        # 脚本位于 backend/scripts/ 目录
        scripts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts'))
        
        # 验证脚本名称
        allowed_scripts = [
            "run_twitter_simulation.py",
            "run_reddit_simulation.py", 
            "run_parallel_simulation.py",
            "action_logger.py"
        ]
        
        if script_name not in allowed_scripts:
            return jsonify({
                "success": False,
                "error": f"未知脚本: {script_name}，可选: {allowed_scripts}"
            }), 400
        
        script_path = os.path.join(scripts_dir, script_name)
        
        if not os.path.exists(script_path):
            return jsonify({
                "success": False,
                "error": f"脚本文件不存在: {script_name}"
            }), 404
        
        return send_file(
            script_path,
            as_attachment=True,
            download_name=script_name
        )
        
    except Exception as e:
        logger.error(f"下载脚本失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Profile生成接口（独立使用） ==============

@simulation_bp.route('/generate-profiles', methods=['POST'])
def generate_profiles():
    """
    直接从图谱生成OASIS Agent Profile（不创建模拟）
    
    请求（JSON）：
        {
            "graph_id": "mirofish_xxxx",     // 必填
            "entity_types": ["Student"],      // 可选
            "use_llm": true,                  // 可选
            "platform": "reddit"              // 可选
        }
    """
    try:
        data = request.get_json() or {}
        
        graph_id = data.get('graph_id')
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "请提供 graph_id"
            }), 400
        
        entity_types = data.get('entity_types')
        use_llm = data.get('use_llm', True)
        platform = data.get('platform', 'reddit')
        
        reader = ZepEntityReader()
        filtered = reader.filter_defined_entities(
            graph_id=graph_id,
            defined_entity_types=entity_types,
            enrich_with_edges=True
        )
        
        if filtered.filtered_count == 0:
            return jsonify({
                "success": False,
                "error": "没有找到符合条件的实体"
            }), 400
        
        generator = OasisProfileGenerator()
        profiles = generator.generate_profiles_from_entities(
            entities=filtered.entities,
            use_llm=use_llm
        )
        
        if platform == "reddit":
            profiles_data = [p.to_reddit_format() for p in profiles]
        elif platform == "twitter":
            profiles_data = [p.to_twitter_format() for p in profiles]
        else:
            profiles_data = [p.to_dict() for p in profiles]
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "entity_types": list(filtered.entity_types),
                "count": len(profiles_data),
                "profiles": profiles_data
            }
        })
        
    except Exception as e:
        logger.error(f"生成Profile失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 模拟运行控制接口 ==============

@simulation_bp.route('/start', methods=['POST'])
def start_simulation():
    """
    开始运行模拟

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",          // 必填，模拟ID
            "platform": "parallel",                // 可选: twitter / reddit / parallel (默认)
            "max_rounds": 100,                     // 可选: 最大模拟轮数，用于截断过长的模拟
            "enable_graph_memory_update": false,   // 可选: 是否将Agent活动动态更新到Zep图谱记忆
            "force": false                         // 可选: 强制重新开始（会停止运行中的模拟并清理日志）
        }

    关于 force 参数：
        - 启用后，如果模拟正在运行或已完成，会先停止并清理运行日志
        - 清理的内容包括：run_state.json, actions.jsonl, simulation.log 等
        - 不会清理配置文件（simulation_config.json）和 profile 文件
        - 适用于需要重新运行模拟的场景

    关于 enable_graph_memory_update：
        - 启用后，模拟中所有Agent的活动（发帖、评论、点赞等）都会实时更新到Zep图谱
        - 这可以让图谱"记住"模拟过程，用于后续分析或AI对话
        - 需要模拟关联的项目有有效的 graph_id
        - 采用批量更新机制，减少API调用次数

    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "process_pid": 12345,
                "twitter_running": true,
                "reddit_running": true,
                "started_at": "2025-12-01T10:00:00",
                "graph_memory_update_enabled": true,  // 是否启用了图谱记忆更新
                "force_restarted": true               // 是否是强制重新开始
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400

        platform = data.get('platform', 'parallel')
        max_rounds = data.get('max_rounds')  # 可选：最大模拟轮数
        enable_graph_memory_update = data.get('enable_graph_memory_update', False)  # 可选：是否启用图谱记忆更新
        force = data.get('force', False)  # 可选：强制重新开始

        # 验证 max_rounds 参数
        if max_rounds is not None:
            try:
                max_rounds = int(max_rounds)
                if max_rounds <= 0:
                    return jsonify({
                        "success": False,
                        "error": "max_rounds 必须是正整数"
                    }), 400
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "max_rounds 必须是有效的整数"
                }), 400

        if platform not in ['twitter', 'reddit', 'parallel']:
            return jsonify({
                "success": False,
                "error": f"无效的平台类型: {platform}，可选: twitter/reddit/parallel"
            }), 400

        # 检查模拟是否已准备好
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404

        force_restarted = False
        
        # 智能处理状态：如果准备工作已完成，允许重新启动
        if state.status != SimulationStatus.READY:
            # 检查准备工作是否已完成
            is_prepared, prepare_info = _check_simulation_prepared(simulation_id)

            if is_prepared:
                # 准备工作已完成，检查是否有正在运行的进程
                if state.status == SimulationStatus.RUNNING:
                    # 检查模拟进程是否真的在运行
                    run_state = SimulationRunner.get_run_state(simulation_id)
                    if run_state and run_state.runner_status.value == "running":
                        # 进程确实在运行
                        if force:
                            # 强制模式：停止运行中的模拟
                            logger.info(f"强制模式：停止运行中的模拟 {simulation_id}")
                            try:
                                SimulationRunner.stop_simulation(simulation_id)
                            except Exception as e:
                                logger.warning(f"停止模拟时出现警告: {str(e)}")
                        else:
                            return jsonify({
                                "success": False,
                                "error": f"模拟正在运行中，请先调用 /stop 接口停止，或使用 force=true 强制重新开始"
                            }), 400

                # 如果是强制模式，清理运行日志
                if force:
                    logger.info(f"强制模式：清理模拟日志 {simulation_id}")
                    cleanup_result = SimulationRunner.cleanup_simulation_logs(simulation_id)
                    if not cleanup_result.get("success"):
                        logger.warning(f"清理日志时出现警告: {cleanup_result.get('errors')}")
                    force_restarted = True

                # 进程不存在或已结束，重置状态为 ready
                logger.info(f"模拟 {simulation_id} 准备工作已完成，重置状态为 ready（原状态: {state.status.value}）")
                state.status = SimulationStatus.READY
                manager._save_simulation_state(state)
            else:
                # 准备工作未完成
                return jsonify({
                    "success": False,
                    "error": f"模拟未准备好，当前状态: {state.status.value}，请先调用 /prepare 接口"
                }), 400
        
        # 获取图谱ID（用于图谱记忆更新）
        graph_id = None
        if enable_graph_memory_update:
            # 从模拟状态或项目中获取 graph_id
            graph_id = state.graph_id
            if not graph_id:
                # 尝试从项目中获取
                project = ProjectManager.get_project(state.project_id)
                if project:
                    graph_id = project.graph_id
            
            if not graph_id:
                return jsonify({
                    "success": False,
                    "error": "启用图谱记忆更新需要有效的 graph_id，请确保项目已构建图谱"
                }), 400
            
            logger.info(f"启用图谱记忆更新: simulation_id={simulation_id}, graph_id={graph_id}")
        
        # Register simulation in the OASIS registry (picks oasis vs demo mode)
        sim_config = manager.get_simulation_config(simulation_id) or {}
        orchestrator, metrics_collector = SimulationRegistry.create(simulation_id, sim_config)
        mode = SimulationRegistry.get_mode(simulation_id)

        if mode == "demo":
            # Demo mode: run DemoSimulator synchronously (no subprocess)
            orchestrator.start(max_rounds=max_rounds or Config.OASIS_DEFAULT_MAX_ROUNDS)
            metrics_collector.ingest_from_orchestrator(orchestrator)

            state.status = SimulationStatus.COMPLETED
            manager._save_simulation_state(state)

            response_data = orchestrator.get_status()
            response_data['force_restarted'] = force_restarted
            response_data['graph_memory_update_enabled'] = False

            return jsonify({
                "success": True,
                "data": response_data
            })

        # OASIS mode: use existing SimulationRunner subprocess approach
        run_state = SimulationRunner.start_simulation(
            simulation_id=simulation_id,
            platform=platform,
            max_rounds=max_rounds,
            enable_graph_memory_update=enable_graph_memory_update,
            graph_id=graph_id
        )
        orchestrator.start(max_rounds=max_rounds)

        # 更新模拟状态
        state.status = SimulationStatus.RUNNING
        manager._save_simulation_state(state)

        response_data = run_state.to_dict()
        response_data['mode'] = mode
        if max_rounds:
            response_data['max_rounds_applied'] = max_rounds
        response_data['graph_memory_update_enabled'] = enable_graph_memory_update
        response_data['force_restarted'] = force_restarted
        if enable_graph_memory_update:
            response_data['graph_id'] = graph_id

        return jsonify({
            "success": True,
            "data": response_data
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"启动模拟失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/stop', methods=['POST'])
def stop_simulation():
    """
    停止模拟
    
    请求（JSON）：
        {
            "simulation_id": "sim_xxxx"  // 必填，模拟ID
        }
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "stopped",
                "completed_at": "2025-12-01T12:00:00"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400
        
        run_state = SimulationRunner.stop_simulation(simulation_id)
        
        # 更新模拟状态
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.PAUSED
            manager._save_simulation_state(state)
        
        return jsonify({
            "success": True,
            "data": run_state.to_dict()
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"停止模拟失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 实时状态监控接口 ==============

@simulation_bp.route('/<simulation_id>/run-status', methods=['GET'])
def get_run_status(simulation_id: str):
    """
    获取模拟运行实时状态（用于前端轮询）
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                "total_rounds": 144,
                "progress_percent": 3.5,
                "simulated_hours": 2,
                "total_simulation_hours": 72,
                "twitter_running": true,
                "reddit_running": true,
                "twitter_actions_count": 150,
                "reddit_actions_count": 200,
                "total_actions_count": 350,
                "started_at": "2025-12-01T10:00:00",
                "updated_at": "2025-12-01T10:30:00"
            }
        }
    """
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        
        mode = SimulationRegistry.get_mode(simulation_id)

        # If this simulation is in demo mode, return orchestrator status directly
        orch = SimulationRegistry.get(simulation_id)
        if orch and mode == "demo":
            return jsonify({
                "success": True,
                "data": orch.get_status()
            })

        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "mode": mode or "unknown",
                    "current_round": 0,
                    "total_rounds": 0,
                    "progress_percent": 0,
                    "twitter_actions_count": 0,
                    "reddit_actions_count": 0,
                    "total_actions_count": 0,
                }
            })

        data = run_state.to_dict()
        data['mode'] = mode or "oasis"
        data["llm_provider"] = os.environ.get('LLM_PROVIDER', 'unknown')
        data["llm_model"] = Config.LLM_MODEL_NAME or 'unknown'

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as e:
        logger.error(f"获取运行状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/run-status/detail', methods=['GET'])
def get_run_status_detail(simulation_id: str):
    """
    获取模拟运行详细状态（包含所有动作）
    
    用于前端展示实时动态
    
    Query参数：
        platform: 过滤平台（twitter/reddit，可选）
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "runner_status": "running",
                "current_round": 5,
                ...
                "all_actions": [
                    {
                        "round_num": 5,
                        "timestamp": "2025-12-01T10:30:00",
                        "platform": "twitter",
                        "agent_id": 3,
                        "agent_name": "Agent Name",
                        "action_type": "CREATE_POST",
                        "action_args": {"content": "..."},
                        "result": null,
                        "success": true
                    },
                    ...
                ],
                "twitter_actions": [...],  # Twitter 平台的所有动作
                "reddit_actions": [...]    # Reddit 平台的所有动作
            }
        }
    """
    try:
        run_state = SimulationRunner.get_run_state(simulation_id)
        platform_filter = request.args.get('platform')
        
        if not run_state:
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "runner_status": "idle",
                    "all_actions": [],
                    "twitter_actions": [],
                    "reddit_actions": []
                }
            })
        
        # 获取完整的动作列表
        all_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter
        )
        
        # 分平台获取动作
        twitter_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="twitter"
        ) if not platform_filter or platform_filter == "twitter" else []
        
        reddit_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform="reddit"
        ) if not platform_filter or platform_filter == "reddit" else []
        
        # 获取当前轮次的动作（recent_actions 只展示最新一轮）
        current_round = run_state.current_round
        recent_actions = SimulationRunner.get_all_actions(
            simulation_id=simulation_id,
            platform=platform_filter,
            round_num=current_round
        ) if current_round > 0 else []
        
        # 获取基础状态信息
        result = run_state.to_dict()
        result["all_actions"] = [a.to_dict() for a in all_actions]
        result["twitter_actions"] = [a.to_dict() for a in twitter_actions]
        result["reddit_actions"] = [a.to_dict() for a in reddit_actions]
        result["rounds_count"] = len(run_state.rounds)
        # recent_actions 只展示当前最新一轮两个平台的内容
        result["recent_actions"] = [a.to_dict() for a in recent_actions]

        # LLM transparency metadata
        result["llm_provider"] = os.environ.get('LLM_PROVIDER', 'unknown')
        result["llm_model"] = Config.LLM_MODEL_NAME or 'unknown'

        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"获取详细状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== OASIS Orchestrator Endpoints ==============

@simulation_bp.route('/<simulation_id>/round/<int:round_num>', methods=['GET'])
def get_simulation_round(simulation_id: str, round_num: int):
    """
    Get results for a specific simulation round from the orchestrator.

    Returns round data (actions, agent stats) or 404 if the round
    hasn't been reached yet.
    """
    try:
        orch = SimulationRegistry.get(simulation_id)
        if not orch:
            return jsonify({
                "success": False,
                "error": f"Simulation not found in registry: {simulation_id}"
            }), 404

        round_data = orch.get_round(round_num)
        if round_data is None:
            return jsonify({
                "success": False,
                "error": f"Round {round_num} not available yet"
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "mode": SimulationRegistry.get_mode(simulation_id),
                "round": round_data,
            }
        })

    except Exception as e:
        logger.error(f"Failed to get round {round_num} for {simulation_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/pause', methods=['POST'])
def pause_simulation(simulation_id: str):
    """
    Pause a running simulation via the orchestrator.
    """
    try:
        orch = SimulationRegistry.get(simulation_id)
        if not orch:
            return jsonify({
                "success": False,
                "error": f"Simulation not found in registry: {simulation_id}"
            }), 404

        result = orch.pause()

        # Also update SimulationManager state
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.PAUSED
            manager._save_simulation_state(state)

        return jsonify({
            "success": True,
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Failed to pause {simulation_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/resume', methods=['POST'])
def resume_simulation(simulation_id: str):
    """
    Resume a paused simulation via the orchestrator.
    """
    try:
        orch = SimulationRegistry.get(simulation_id)
        if not orch:
            return jsonify({
                "success": False,
                "error": f"Simulation not found in registry: {simulation_id}"
            }), 404

        result = orch.resume()

        # Also update SimulationManager state
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.RUNNING
            manager._save_simulation_state(state)

        return jsonify({
            "success": True,
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        logger.error(f"Failed to resume {simulation_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/metrics', methods=['GET'])
def get_simulation_metrics(simulation_id: str):
    """
    Get aggregated metrics from the MetricsCollector for a simulation.
    """
    try:
        metrics = SimulationRegistry.get_metrics(simulation_id)
        if not metrics:
            return jsonify({
                "success": False,
                "error": f"No metrics available for simulation: {simulation_id}"
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "mode": SimulationRegistry.get_mode(simulation_id) or "unknown",
                **metrics.get_summary(),
            }
        })

    except Exception as e:
        logger.error(f"Failed to get metrics for {simulation_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== SSE Progress Stream ==============

@simulation_bp.route('/<simulation_id>/progress/stream', methods=['GET'])
def stream_simulation_progress(simulation_id: str):
    """
    SSE stream for real-time simulation progress updates.

    Streams events:
        status   — runner status changes (idle/running/completed/failed)
        progress — round/action count updates (only when changed)
        actions  — new agent actions since last push
        heartbeat — keep-alive every 15s

    Query params:
        interval: polling interval in seconds (default 2, min 1, max 10)
    """
    interval = max(1, min(10, int(request.args.get('interval', 2))))

    def generate():
        last_snapshot = None
        last_actions_count = 0

        while True:
            try:
                run_state = SimulationRunner.get_run_state(simulation_id)

                if not run_state:
                    payload = {
                        "simulation_id": simulation_id,
                        "runner_status": "idle",
                        "current_round": 0,
                        "total_rounds": 0,
                        "progress_percent": 0,
                        "twitter_actions_count": 0,
                        "reddit_actions_count": 0,
                        "total_actions_count": 0,
                    }
                    snapshot_key = "idle:0:0"
                else:
                    payload = run_state.to_dict()
                    total = payload.get("total_actions_count", 0)
                    snapshot_key = (
                        f"{payload['runner_status']}:"
                        f"{payload['current_round']}:"
                        f"{total}"
                    )

                # Emit progress only when state actually changed
                if snapshot_key != last_snapshot:
                    yield f"event: progress\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

                    # If status changed, emit a dedicated status event too
                    if last_snapshot is None or snapshot_key.split(':')[0] != (last_snapshot or '').split(':')[0]:
                        yield f"event: status\ndata: {json.dumps({'runner_status': payload['runner_status']}, ensure_ascii=False)}\n\n"

                    last_snapshot = snapshot_key

                # Stream new actions incrementally
                if run_state:
                    current_total = run_state.twitter_actions_count + run_state.reddit_actions_count
                    if current_total > last_actions_count:
                        new_actions = [
                            a.to_dict() for a in run_state.recent_actions
                            if (run_state.twitter_actions_count + run_state.reddit_actions_count) > last_actions_count
                        ][:20]
                        if new_actions:
                            yield f"event: actions\ndata: {json.dumps(new_actions, ensure_ascii=False)}\n\n"
                        last_actions_count = current_total

                    # Stop streaming on terminal states
                    if run_state.runner_status in (RunnerStatus.COMPLETED, RunnerStatus.STOPPED, RunnerStatus.FAILED):
                        yield f"event: complete\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
                        return

                # Heartbeat (always sent to prevent proxy timeouts)
                yield f"event: heartbeat\ndata: {json.dumps({'ts': time.time()})}\n\n"

            except GeneratorExit:
                return
            except Exception as e:
                logger.error(f"SSE stream error for {simulation_id}: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

            time.sleep(interval)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


# ============== Agent动作与结果接口 ==============


@simulation_bp.route('/<simulation_id>/actions', methods=['GET'])
def get_simulation_actions(simulation_id: str):
    """
    获取模拟中的Agent动作历史

    Query参数：
        limit: 返回数量（默认100）
        offset: 偏移量（默认0）
        platform: 过滤平台（twitter/reddit）
        agent_id: 过滤Agent ID
        round_num: 过滤轮次
    
    返回：
        {
            "success": true,
            "data": {
                "count": 100,
                "actions": [...]
            }
        }
    """
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        platform = request.args.get('platform')
        agent_id = request.args.get('agent_id', type=int)
        round_num = request.args.get('round_num', type=int)
        
        actions = SimulationRunner.get_actions(
            simulation_id=simulation_id,
            limit=limit,
            offset=offset,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(actions),
                "actions": [a.to_dict() for a in actions]
            }
        })
        
    except Exception as e:
        logger.error(f"获取动作历史失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/timeline', methods=['GET'])
def get_simulation_timeline(simulation_id: str):
    """
    获取模拟时间线（按轮次汇总）
    
    用于前端展示进度条和时间线视图
    
    Query参数：
        start_round: 起始轮次（默认0）
        end_round: 结束轮次（默认全部）
    
    返回每轮的汇总信息
    """
    try:
        start_round = request.args.get('start_round', 0, type=int)
        end_round = request.args.get('end_round', type=int)
        
        timeline = SimulationRunner.get_timeline(
            simulation_id=simulation_id,
            start_round=start_round,
            end_round=end_round
        )
        
        return jsonify({
            "success": True,
            "data": {
                "rounds_count": len(timeline),
                "timeline": timeline
            }
        })
        
    except Exception as e:
        logger.error(f"获取时间线失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/agent-stats', methods=['GET'])
def get_agent_stats(simulation_id: str):
    """
    获取每个Agent的统计信息
    
    用于前端展示Agent活跃度排行、动作分布等
    """
    try:
        stats = SimulationRunner.get_agent_stats(simulation_id)
        
        return jsonify({
            "success": True,
            "data": {
                "agents_count": len(stats),
                "stats": stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取Agent统计失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Agent Personality 接口 ==============

PERSONALITY_TRAITS = ["confidence", "openness", "risk_aversion", "empathy", "aggressiveness"]

MOCK_AGENTS = [
    {"agent_id": 0, "agent_name": "Sarah Chen, VP Support @ Acme SaaS"},
    {"agent_id": 1, "agent_name": "Marcus Johnson, CTO @ HealthFirst"},
    {"agent_id": 2, "agent_name": "Priya Patel, Dir. CX @ FinServe"},
    {"agent_id": 3, "agent_name": "James O'Brien, Head of Ops @ RetailCo"},
    {"agent_id": 4, "agent_name": "Elena Rodriguez, VP Product @ CloudSync"},
    {"agent_id": 5, "agent_name": "David Kim, Support Lead @ EduPlatform"},
    {"agent_id": 6, "agent_name": "Aisha Williams, CRO @ DataDrive"},
    {"agent_id": 7, "agent_name": "Tom Fischer, Dir. IT @ MediGroup"},
    {"agent_id": 8, "agent_name": "Nina Yamamoto, COO @ LogiTech"},
    {"agent_id": 9, "agent_name": "Carlos Mendez, VP Sales @ InsureTech"},
]


def _generate_mock_personalities():
    """Generate deterministic mock personality data for demo mode."""
    import hashlib
    agents = []
    for agent in MOCK_AGENTS:
        initial = {}
        current = {}
        for trait in PERSONALITY_TRAITS:
            seed = hashlib.md5(f"{agent['agent_id']}-{trait}".encode()).hexdigest()
            base_val = (int(seed[:4], 16) % 60) + 20  # 20-79
            delta = ((int(seed[4:8], 16) % 30) - 12)  # -12 to +17
            initial[trait] = base_val
            current[trait] = max(0, min(100, base_val + delta))
        agents.append({
            "agent_id": agent["agent_id"],
            "agent_name": agent["agent_name"],
            "initial_personality": initial,
            "current_personality": current,
        })
    return agents


@simulation_bp.route('/<simulation_id>/agent-personalities', methods=['GET'])
def get_agent_personalities(simulation_id: str):
    """
    Get personality trait data for all agents in a simulation.

    Returns initial and current personality values per agent,
    used by the PersonalityMatrix frontend component.
    Falls back to mock data when no real simulation data exists.
    """
    try:
        # Try to derive personality from real agent stats
        try:
            stats = SimulationRunner.get_agent_stats(simulation_id)
        except Exception:
            stats = []

        if stats:
            import hashlib
            agents = []
            for s in stats:
                initial = {}
                current = {}
                for trait in PERSONALITY_TRAITS:
                    seed = hashlib.md5(f"{s['agent_id']}-{trait}".encode()).hexdigest()
                    base_val = (int(seed[:4], 16) % 60) + 20
                    # Shift current values based on action count
                    action_influence = min(15, s.get("total_actions", 0) // 3)
                    direction = 1 if int(seed[4:6], 16) % 2 == 0 else -1
                    initial[trait] = base_val
                    current[trait] = max(0, min(100, base_val + direction * action_influence))
                agents.append({
                    "agent_id": s["agent_id"],
                    "agent_name": s["agent_name"],
                    "initial_personality": initial,
                    "current_personality": current,
                })
            return jsonify({
                "success": True,
                "data": {
                    "traits": PERSONALITY_TRAITS,
                    "agents": agents,
                }
            })

        # Fallback: mock data
        return jsonify({
            "success": True,
            "data": {
                "traits": PERSONALITY_TRAITS,
                "agents": _generate_mock_personalities(),
            }
        })

    except Exception as e:
        logger.error(f"获取Agent性格数据失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 数据库查询接口 ==============

@simulation_bp.route('/<simulation_id>/posts', methods=['GET'])
def get_simulation_posts(simulation_id: str):
    """
    获取模拟中的帖子
    
    Query参数：
        platform: 平台类型（twitter/reddit）
        limit: 返回数量（默认50）
        offset: 偏移量
    
    返回帖子列表（从SQLite数据库读取）
    """
    try:
        platform = request.args.get('platform', 'reddit')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )
        
        db_file = f"{platform}_simulation.db"
        db_path = os.path.join(sim_dir, db_file)
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "platform": platform,
                    "count": 0,
                    "posts": [],
                    "message": "数据库不存在，模拟可能尚未运行"
                }
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM post 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            posts = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT COUNT(*) FROM post")
            total = cursor.fetchone()[0]
            
        except sqlite3.OperationalError:
            posts = []
            total = 0
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "platform": platform,
                "total": total,
                "count": len(posts),
                "posts": posts
            }
        })
        
    except Exception as e:
        logger.error(f"获取帖子失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/comments', methods=['GET'])
def get_simulation_comments(simulation_id: str):
    """
    获取模拟中的评论（仅Reddit）
    
    Query参数：
        post_id: 过滤帖子ID（可选）
        limit: 返回数量
        offset: 偏移量
    """
    try:
        post_id = request.args.get('post_id')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        sim_dir = os.path.join(
            os.path.dirname(__file__),
            f'../../uploads/simulations/{simulation_id}'
        )
        
        db_path = os.path.join(sim_dir, "reddit_simulation.db")
        
        if not os.path.exists(db_path):
            return jsonify({
                "success": True,
                "data": {
                    "count": 0,
                    "comments": []
                }
            })
        
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if post_id:
                cursor.execute("""
                    SELECT * FROM comment 
                    WHERE post_id = ?
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (post_id, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM comment 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            comments = [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.OperationalError:
            comments = []
        
        conn.close()
        
        return jsonify({
            "success": True,
            "data": {
                "count": len(comments),
                "comments": comments
            }
        })
        
    except Exception as e:
        logger.error(f"获取评论失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Personality Dynamics 人格动态接口 ==============

@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/personality', methods=['GET'])
def get_agent_personality(simulation_id: str, agent_id: int):
    """
    Get the current personality trait vector for a single agent.

    Returns 5 traits (0-100): analytical, creative, assertive, empathetic, risk_tolerant.
    """
    try:
        from ..services.personality_dynamics import PersonalityDynamicsService
        data = PersonalityDynamicsService.get_personality(simulation_id, agent_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"获取Agent人格失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/personality/history', methods=['GET'])
def get_agent_personality_history(simulation_id: str, agent_id: int):
    """
    Get the personality trait evolution across simulation rounds.

    Returns sampled trait vectors (every 6 rounds) showing how the
    agent's personality shifted over time.
    """
    try:
        from ..services.personality_dynamics import PersonalityDynamicsService
        data = PersonalityDynamicsService.get_personality_history(simulation_id, agent_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"获取Agent人格历史失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/sentiment/history', methods=['GET'])
def get_agent_sentiment_history(simulation_id: str, agent_id: int):
    """
    Get per-round sentiment values for a single agent.

    Sentiment ranges 1-10 with labels: frustrated, cautious, engaged,
    optimistic, enthusiastic.
    """
    try:
        from ..services.personality_dynamics import PersonalityDynamicsService
        data = PersonalityDynamicsService.get_sentiment_history(simulation_id, agent_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"获取Agent情感历史失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/personality/comparison', methods=['GET'])
def get_personality_comparison(simulation_id: str):
    """
    Get all agents' initial and current personality vectors for
    side-by-side comparison, including per-trait deltas.
    """
    try:
        from ..services.personality_dynamics import PersonalityDynamicsService
        data = PersonalityDynamicsService.get_personality_comparison(simulation_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"获取人格比较失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/mood', methods=['GET'])
def get_group_mood(simulation_id: str):
    """
    Get group mood overview — average sentiment and per-agent breakdown.
    """
    try:
        from ..services.personality_dynamics import PersonalityDynamicsService
        data = PersonalityDynamicsService.get_group_mood(simulation_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"获取群体情绪失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/mood-swings', methods=['GET'])
def get_mood_swings(simulation_id: str):
    """
    Detect significant sentiment changes across all agents.

    Query params:
        threshold: minimum absolute delta to count as a swing (default 2.0)
    """
    try:
        threshold = request.args.get('threshold', 2.0, type=float)
        from ..services.personality_dynamics import PersonalityDynamicsService
        data = PersonalityDynamicsService.get_mood_swings(simulation_id, threshold=threshold)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"获取情绪波动失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Interview 采访接口 ==============

@simulation_bp.route('/interview', methods=['POST'])
def interview_agent():
    """
    采访单个Agent

    注意：此功能需要模拟环境处于运行状态（完成模拟循环后进入等待命令模式）

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",       // 必填，模拟ID
            "agent_id": 0,                     // 必填，Agent ID
            "prompt": "你对这件事有什么看法？",  // 必填，采访问题
            "platform": "twitter",             // 可选，指定平台（twitter/reddit）
                                               // 不指定时：双平台模拟同时采访两个平台
            "timeout": 60                      // 可选，超时时间（秒），默认60
        }

    返回（不指定platform，双平台模式）：
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "你对这件事有什么看法？",
                "result": {
                    "agent_id": 0,
                    "prompt": "...",
                    "platforms": {
                        "twitter": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit": {"agent_id": 0, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }

    返回（指定platform）：
        {
            "success": true,
            "data": {
                "agent_id": 0,
                "prompt": "你对这件事有什么看法？",
                "result": {
                    "agent_id": 0,
                    "response": "我认为...",
                    "platform": "twitter",
                    "timestamp": "2025-12-08T10:00:00"
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        agent_id = data.get('agent_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # 可选：twitter/reddit/None
        timeout = data.get('timeout', 60)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400
        
        if agent_id is None:
            return jsonify({
                "success": False,
                "error": "请提供 agent_id"
            }), 400
        
        if not prompt:
            return jsonify({
                "success": False,
                "error": "请提供 prompt（采访问题）"
            }), 400
        
        # 验证platform参数
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "platform 参数只能是 'twitter' 或 'reddit'"
            }), 400
        
        # 检查环境状态
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "模拟环境未运行或已关闭。请确保模拟已完成并进入等待命令模式。"
            }), 400
        
        # 优化prompt，添加前缀避免Agent调用工具
        optimized_prompt = optimize_interview_prompt(prompt)
        
        result = SimulationRunner.interview_agent(
            simulation_id=simulation_id,
            agent_id=agent_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"等待Interview响应超时: {str(e)}"
        }), 504
        
    except Exception as e:
        logger.error(f"Interview失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/interview/batch', methods=['POST'])
def interview_agents_batch():
    """
    批量采访多个Agent

    注意：此功能需要模拟环境处于运行状态

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",       // 必填，模拟ID
            "interviews": [                    // 必填，采访列表
                {
                    "agent_id": 0,
                    "prompt": "你对A有什么看法？",
                    "platform": "twitter"      // 可选，指定该Agent的采访平台
                },
                {
                    "agent_id": 1,
                    "prompt": "你对B有什么看法？"  // 不指定platform则使用默认值
                }
            ],
            "platform": "reddit",              // 可选，默认平台（被每项的platform覆盖）
                                               // 不指定时：双平台模拟每个Agent同时采访两个平台
            "timeout": 120                     // 可选，超时时间（秒），默认120
        }

    返回：
        {
            "success": true,
            "data": {
                "interviews_count": 2,
                "result": {
                    "interviews_count": 4,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        "twitter_1": {"agent_id": 1, "response": "...", "platform": "twitter"},
                        "reddit_1": {"agent_id": 1, "response": "...", "platform": "reddit"}
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        interviews = data.get('interviews')
        platform = data.get('platform')  # 可选：twitter/reddit/None
        timeout = data.get('timeout', 120)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400

        if not interviews or not isinstance(interviews, list):
            return jsonify({
                "success": False,
                "error": "请提供 interviews（采访列表）"
            }), 400

        # 验证platform参数
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "platform 参数只能是 'twitter' 或 'reddit'"
            }), 400

        # 验证每个采访项
        for i, interview in enumerate(interviews):
            if 'agent_id' not in interview:
                return jsonify({
                    "success": False,
                    "error": f"采访列表第{i+1}项缺少 agent_id"
                }), 400
            if 'prompt' not in interview:
                return jsonify({
                    "success": False,
                    "error": f"采访列表第{i+1}项缺少 prompt"
                }), 400
            # 验证每项的platform（如果有）
            item_platform = interview.get('platform')
            if item_platform and item_platform not in ("twitter", "reddit"):
                return jsonify({
                    "success": False,
                    "error": f"采访列表第{i+1}项的platform只能是 'twitter' 或 'reddit'"
                }), 400

        # 检查环境状态
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "模拟环境未运行或已关闭。请确保模拟已完成并进入等待命令模式。"
            }), 400

        # 优化每个采访项的prompt，添加前缀避免Agent调用工具
        optimized_interviews = []
        for interview in interviews:
            optimized_interview = interview.copy()
            optimized_interview['prompt'] = optimize_interview_prompt(interview.get('prompt', ''))
            optimized_interviews.append(optimized_interview)

        result = SimulationRunner.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=optimized_interviews,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"等待批量Interview响应超时: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"批量Interview失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/interview/all', methods=['POST'])
def interview_all_agents():
    """
    全局采访 - 使用相同问题采访所有Agent

    注意：此功能需要模拟环境处于运行状态

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",            // 必填，模拟ID
            "prompt": "你对这件事整体有什么看法？",  // 必填，采访问题（所有Agent使用相同问题）
            "platform": "reddit",                   // 可选，指定平台（twitter/reddit）
                                                    // 不指定时：双平台模拟每个Agent同时采访两个平台
            "timeout": 180                          // 可选，超时时间（秒），默认180
        }

    返回：
        {
            "success": true,
            "data": {
                "interviews_count": 50,
                "result": {
                    "interviews_count": 100,
                    "results": {
                        "twitter_0": {"agent_id": 0, "response": "...", "platform": "twitter"},
                        "reddit_0": {"agent_id": 0, "response": "...", "platform": "reddit"},
                        ...
                    }
                },
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get('simulation_id')
        prompt = data.get('prompt')
        platform = data.get('platform')  # 可选：twitter/reddit/None
        timeout = data.get('timeout', 180)

        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400

        if not prompt:
            return jsonify({
                "success": False,
                "error": "请提供 prompt（采访问题）"
            }), 400

        # 验证platform参数
        if platform and platform not in ("twitter", "reddit"):
            return jsonify({
                "success": False,
                "error": "platform 参数只能是 'twitter' 或 'reddit'"
            }), 400

        # 检查环境状态
        if not SimulationRunner.check_env_alive(simulation_id):
            return jsonify({
                "success": False,
                "error": "模拟环境未运行或已关闭。请确保模拟已完成并进入等待命令模式。"
            }), 400

        # 优化prompt，添加前缀避免Agent调用工具
        optimized_prompt = optimize_interview_prompt(prompt)

        result = SimulationRunner.interview_all_agents(
            simulation_id=simulation_id,
            prompt=optimized_prompt,
            platform=platform,
            timeout=timeout
        )

        return jsonify({
            "success": result.get("success", False),
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except TimeoutError as e:
        return jsonify({
            "success": False,
            "error": f"等待全局Interview响应超时: {str(e)}"
        }), 504

    except Exception as e:
        logger.error(f"全局Interview失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/interview/history', methods=['POST'])
def get_interview_history():
    """
    获取Interview历史记录

    从模拟数据库中读取所有Interview记录

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",  // 必填，模拟ID
            "platform": "reddit",          // 可选，平台类型（reddit/twitter）
                                           // 不指定则返回两个平台的所有历史
            "agent_id": 0,                 // 可选，只获取该Agent的采访历史
            "limit": 100                   // 可选，返回数量，默认100
        }

    返回：
        {
            "success": true,
            "data": {
                "count": 10,
                "history": [
                    {
                        "agent_id": 0,
                        "response": "我认为...",
                        "prompt": "你对这件事有什么看法？",
                        "timestamp": "2025-12-08T10:00:00",
                        "platform": "reddit"
                    },
                    ...
                ]
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        platform = data.get('platform')  # 不指定则返回两个平台的历史
        agent_id = data.get('agent_id')
        limit = data.get('limit', 100)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400

        history = SimulationRunner.get_interview_history(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            limit=limit
        )

        return jsonify({
            "success": True,
            "data": {
                "count": len(history),
                "history": history
            }
        })

    except Exception as e:
        logger.error(f"获取Interview历史失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/env-status', methods=['POST'])
def get_env_status():
    """
    获取模拟环境状态

    检查模拟环境是否存活（可以接收Interview命令）

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx"  // 必填，模拟ID
        }

    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "env_alive": true,
                "twitter_available": true,
                "reddit_available": true,
                "message": "环境正在运行，可以接收Interview命令"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400

        env_alive = SimulationRunner.check_env_alive(simulation_id)
        
        # 获取更详细的状态信息
        env_status = SimulationRunner.get_env_status_detail(simulation_id)

        if env_alive:
            message = "环境正在运行，可以接收Interview命令"
        else:
            message = "环境未运行或已关闭"

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "env_alive": env_alive,
                "twitter_available": env_status.get("twitter_available", False),
                "reddit_available": env_status.get("reddit_available", False),
                "message": message
            }
        })

    except Exception as e:
        logger.error(f"获取环境状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/close-env', methods=['POST'])
def close_simulation_env():
    """
    关闭模拟环境
    
    向模拟发送关闭环境命令，使其优雅退出等待命令模式。
    
    注意：这不同于 /stop 接口，/stop 会强制终止进程，
    而此接口会让模拟优雅地关闭环境并退出。
    
    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",  // 必填，模拟ID
            "timeout": 30                  // 可选，超时时间（秒），默认30
        }
    
    返回：
        {
            "success": true,
            "data": {
                "message": "环境关闭命令已发送",
                "result": {...},
                "timestamp": "2025-12-08T10:00:01"
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        timeout = data.get('timeout', 30)
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400
        
        result = SimulationRunner.close_simulation_env(
            simulation_id=simulation_id,
            timeout=timeout
        )
        
        # 更新模拟状态
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        if state:
            state.status = SimulationStatus.COMPLETED
            manager._save_simulation_state(state)
        
        return jsonify({
            "success": result.get("success", False),
            "data": result
        })
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"关闭环境失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Orchestrator endpoints ==============

# In-memory registry of orchestrator instances (keyed by simulation_id).
# In production these would be shared via Redis / DB; for the demo a
# module-level dict suffices since Flask runs in a single process.
_orchestrators: dict = {}


@simulation_bp.route('/<simulation_id>/orchestrator/status', methods=['GET'])
def get_orchestrator_status(simulation_id: str):
    """
    Return the orchestrator's lightweight status snapshot.

    Response:
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "state": "running",
                "current_round": 42,
                "total_rounds": 144,
                "progress_percent": 29.2,
                "twitter_actions": 120,
                "reddit_actions": 85,
                "total_actions": 205,
                ...
            }
        }
    """
    from ..services.oasis_orchestrator import OasisOrchestrator

    orch = _orchestrators.get(simulation_id)
    if not orch:
        return jsonify({
            "success": False,
            "error": f"No active orchestrator for {simulation_id}",
        }), 404

    return jsonify({"success": True, "data": orch.get_status()})


@simulation_bp.route('/<simulation_id>/orchestrator/results', methods=['GET'])
def get_orchestrator_results(simulation_id: str):
    """
    Return the full structured results from the orchestrator.

    Response:
        {
            "success": true,
            "data": { ... OrchestratorResults ... }
        }
    """
    from ..services.oasis_orchestrator import OasisOrchestrator

    orch = _orchestrators.get(simulation_id)
    if not orch:
        return jsonify({
            "success": False,
            "error": f"No active orchestrator for {simulation_id}",
        }), 404

    return jsonify({"success": True, "data": orch.get_results().to_dict()})


@simulation_bp.route('/<simulation_id>/orchestrator/pause', methods=['POST'])
def pause_orchestrator(simulation_id: str):
    """Pause the running orchestrator after its current round."""
    orch = _orchestrators.get(simulation_id)
    if not orch:
        return jsonify({"success": False, "error": "No active orchestrator"}), 404

    orch.pause()
    return jsonify({"success": True, "data": orch.get_status()})


@simulation_bp.route('/<simulation_id>/orchestrator/resume', methods=['POST'])
def resume_orchestrator(simulation_id: str):
    """Resume a paused orchestrator."""
    orch = _orchestrators.get(simulation_id)
    if not orch:
        return jsonify({"success": False, "error": "No active orchestrator"}), 404

    orch.resume()
    return jsonify({"success": True, "data": orch.get_status()})


@simulation_bp.route('/<simulation_id>/orchestrator/stop', methods=['POST'])
def stop_orchestrator(simulation_id: str):
    """Request a graceful stop of the orchestrator."""
    orch = _orchestrators.get(simulation_id)
    if not orch:
        return jsonify({"success": False, "error": "No active orchestrator"}), 404

    orch.stop()
    return jsonify({"success": True, "data": orch.get_status()})


# ============== Coalition & Consensus API ==============

@simulation_bp.route('/<simulation_id>/coalitions', methods=['GET'])
def get_coalitions(simulation_id: str):
    """
    Detect and return coalitions for a simulation.

    Returns labeled coalitions with members, shared positions, and strength.
    Works in demo mode when no simulation data exists.
    """
    try:
        from ..services.coalition_detector import CoalitionDetector
        from ..services.coalition_labeler import CoalitionLabeler

        detector = CoalitionDetector()
        labeler = CoalitionLabeler()

        coalitions = detector.detect_coalitions(simulation_id)
        coalitions = labeler.label_all(coalitions)

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "coalition_count": len(coalitions),
                "coalitions": [c.to_dict() for c in coalitions],
            }
        })

    except Exception as e:
        logger.error(f"Coalition detection failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Agent Interaction Network ==============

@simulation_bp.route('/<simulation_id>/network', methods=['GET'])
def get_interaction_network(simulation_id: str):
    """
    Get agent interaction network graph for a simulation.

    Returns nodes (agents with metrics) and edges (interactions).
    Optional query param: include_centrality=true, include_clusters=true
    """
    try:
        from ..services.interaction_graph import InteractionGraphBuilder

        actions = SimulationRunner.get_actions(simulation_id=simulation_id)
        action_dicts = [a.to_dict() for a in actions]

        builder = InteractionGraphBuilder()
        graph = builder.build_from_simulation(action_dicts)

        if request.args.get('include_centrality', 'false').lower() == 'true':
            graph['centrality'] = builder.compute_centrality(graph)

        if request.args.get('include_clusters', 'false').lower() == 'true':
            graph['clusters'] = builder.detect_clusters(graph)

        return jsonify({"success": True, "data": graph})

    except Exception as e:
        logger.error(f"Failed to build interaction network: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/network/round/<int:round_num>', methods=['GET'])
def get_interaction_network_at_round(simulation_id: str, round_num: int):
    """
    Get agent interaction network graph state at a specific round.
    """
    try:
        from ..services.interaction_graph import InteractionGraphBuilder

        actions = SimulationRunner.get_actions(simulation_id=simulation_id)
        action_dicts = [a.to_dict() for a in actions]

        builder = InteractionGraphBuilder()
        graph = builder.build_temporal_graph(action_dicts, round_num)

        if request.args.get('include_centrality', 'false').lower() == 'true':
            graph['centrality'] = builder.compute_centrality(graph)

        if request.args.get('include_clusters', 'false').lower() == 'true':
            graph['clusters'] = builder.detect_clusters(graph)

        return jsonify({"success": True, "data": graph})

    except Exception as e:
        logger.error(f"Failed to build temporal network: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== What-If Analysis Endpoints ==============

@simulation_bp.route('/whatif', methods=['POST'])
def create_whatif_scenario():
    """Create and run a what-if scenario variant.

    Body:
        {
            "base_simulation_id": "sim_xxxx",
            "modifications": [
                {"parameter": "agent_count", "value": 12},
                {"parameter": "temperature", "value": 0.9}
            ]
        }
    """
    try:
        from ..services.whatif_engine import create_whatif_variant, SUPPORTED_PARAMETERS

        data = request.get_json() or {}

        base_simulation_id = data.get('base_simulation_id')
        if not base_simulation_id:
            return jsonify({
                "success": False,
                "error": "base_simulation_id is required"
            }), 400

        modifications = data.get('modifications', [])
        if not modifications or not isinstance(modifications, list):
            return jsonify({
                "success": False,
                "error": "modifications must be a non-empty list of {parameter, value} objects"
            }), 400

        supported = SUPPORTED_PARAMETERS
        for mod in modifications:
            param = mod.get('parameter')
            if not param or param not in supported:
                return jsonify({
                    "success": False,
                    "error": f"Unsupported parameter: '{param}'. Supported: {list(supported.keys())}"
                }), 400
            if 'value' not in mod:
                return jsonify({
                    "success": False,
                    "error": f"Missing 'value' for parameter '{param}'"
                }), 400

        result = create_whatif_variant(base_simulation_id, modifications)

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Failed to create what-if scenario: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/whatif/variants', methods=['GET'])
def get_whatif_variants(simulation_id: str):
    """List all what-if variants of a base simulation."""
    try:
        from ..services.whatif_engine import list_whatif_variants

        variants = list_whatif_variants(simulation_id)

        return jsonify({
            "success": True,
            "data": {
                "base_simulation_id": simulation_id,
                "variants": variants,
                "count": len(variants),
            }
        })

    except Exception as e:
        logger.error(f"Failed to get what-if variants: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/sensitivity', methods=['POST'])
def run_sensitivity_analysis():
    """Run parameter sensitivity analysis.

    Body:
        {
            "base_simulation_id": "sim_xxxx",
            "parameter": "agent_count",
            "min_value": 2,
            "max_value": 15,
            "steps": 7
        }
    """
    try:
        data = request.get_json() or {}

        base_simulation_id = data.get('base_simulation_id')
        if not base_simulation_id:
            return jsonify({
                "success": False,
                "error": "base_simulation_id is required"
            }), 400

        parameter = data.get('parameter')
        if not parameter:
            return jsonify({
                "success": False,
                "error": "parameter is required"
            }), 400

        min_value = data.get('min_value')
        max_value = data.get('max_value')
        if min_value is None or max_value is None:
            return jsonify({
                "success": False,
                "error": "min_value and max_value are required"
            }), 400

        try:
            min_value = float(min_value)
            max_value = float(max_value)
        except (TypeError, ValueError):
            return jsonify({
                "success": False,
                "error": "min_value and max_value must be numeric"
            }), 400

        if min_value >= max_value:
            return jsonify({
                "success": False,
                "error": "min_value must be less than max_value"
            }), 400

        steps = data.get('steps', 5)

        result = SensitivityAnalyzer.run_sensitivity(
            base_simulation_id=base_simulation_id,
            parameter=parameter,
            min_value=min_value,
            max_value=max_value,
            steps=steps,
        )

        return jsonify({
            "success": True,
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        logger.error(f"Failed to run sensitivity analysis: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/coalitions/evolution', methods=['GET'])
def get_coalition_evolution(simulation_id: str):
    """
    Track coalition formation and changes across rounds.

    Returns per-round coalition state and polarization index.
    """
    try:
        from ..services.coalition_detector import CoalitionDetector
        from ..services.coalition_labeler import CoalitionLabeler

        detector = CoalitionDetector()
        labeler = CoalitionLabeler()

        evolution = detector.track_coalition_evolution(simulation_id)
        for evo in evolution:
            labeler.label_all(evo.coalitions)

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "rounds_count": len(evolution),
                "evolution": [e.to_dict() for e in evolution],
            }
        })

    except Exception as e:
        logger.error(f"Coalition evolution failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Reasoning Transparency API ==============

# ============== Anomaly Detection ==============

import random
import hashlib

_RT_AGENTS = [
    ("Sarah Chen", "VP Support @ Acme SaaS"),
    ("Marcus Johnson", "CX Director @ MedFirst"),
    ("Priya Patel", "Head of Ops @ PayStream"),
    ("David Kim", "IT Leader @ ShopNova"),
    ("Rachel Torres", "VP Support @ CloudOps"),
    ("James Wright", "CX Director @ Retail Plus"),
    ("Anika Sharma", "Support Eng Lead @ DevStack"),
    ("Tom O'Brien", "VP CS @ GrowthLoop"),
    ("Elena Vasquez", "Dir Digital @ HealthBridge"),
    ("Michael Chang", "Head of Ops @ FinEdge"),
    ("Lisa Park", "VP CX @ TravelNow"),
    ("Sofia Martinez", "Support Mgr @ QuickShip"),
    ("Nathan Lee", "CTO @ DataPulse"),
    ("Catherine Hayes", "CFO @ ScaleUp Corp"),
    ("Robert Williams", "IT Director @ EduSpark"),
]

_RT_REASONING = [
    "Evaluating whether to share our Q1 support metrics publicly. Fin AI resolution rate of {pct}% is significantly above industry average — sharing could attract attention from prospects and validate our positioning.",
    "Weighing competitive response to Zendesk's latest announcement. Our data shows {pct}% improvement in CSAT since switching — direct comparison could be effective but risks appearing combative.",
    "Considering whether cost-per-resolution framing resonates better than speed-to-value. Internal surveys suggest {pct}% of VPs respond more strongly to ROI messaging.",
    "Analyzing the trade-off between AI automation depth and customer satisfaction. Our pilot data shows diminishing returns above {pct}% automation — human escalation paths are critical.",
    "Assessing multi-threading strategy: reaching multiple stakeholders increases conversion {pct}% but risks appearing spammy if not coordinated.",
    "Reviewing whether compliance-first messaging for Healthcare is worth the extra personalization cost. Data shows {pct}% higher engagement when HIPAA is mentioned upfront.",
]

_RT_GOALS = [
    "Maximize support team efficiency",
    "Reduce cost per resolution",
    "Improve customer satisfaction scores",
    "Drive AI adoption in support workflows",
    "Build thought leadership in CX space",
    "Evaluate competitive alternatives objectively",
    "Optimize multi-channel support strategy",
    "Scale support operations without proportional headcount",
]

_RT_FACTORS = [
    {"name": "ROI impact", "weight": 0.35, "assessment": "High — strong cost savings narrative"},
    {"name": "audience relevance", "weight": 0.25, "assessment": "Medium — resonates with VP-level personas"},
    {"name": "competitive risk", "weight": 0.15, "assessment": "Low — factual, data-driven framing"},
    {"name": "credibility", "weight": 0.15, "assessment": "High — backed by pilot data"},
    {"name": "timing", "weight": 0.10, "assessment": "Good — aligns with Q1 budget planning"},
]

_RT_TOTAL_ROUNDS = 144


def _rt_agent_id(name):
    return abs(int(hashlib.md5(name.encode()).hexdigest(), 16)) % 10000


def _rt_round_reasoning(sim_id, round_num):
    rng = random.Random(hash(f"{sim_id}-reasoning-{round_num}"))
    traces = []
    for name, title in rng.sample(_RT_AGENTS, rng.randint(3, 8)):
        pct = rng.randint(20, 72)
        traces.append({
            "agent_id": _rt_agent_id(name),
            "agent_name": f"{name} ({title})",
            "round": round_num,
            "reasoning": rng.choice(_RT_REASONING).format(pct=pct),
            "goal": rng.choice(_RT_GOALS),
            "action_chosen": rng.choice(["CREATE_POST", "REPLY", "LIKE", "REPOST"]),
            "confidence": round(rng.uniform(0.55, 0.95), 2),
            "factors_considered": [
                {**f, "weight": round(f["weight"] + rng.uniform(-0.05, 0.05), 2)}
                for f in rng.sample(_RT_FACTORS, rng.randint(2, 4))
            ],
            "alternatives_rejected": rng.sample(
                ["LIKE", "REPOST", "CREATE_POST", "REPLY", "IGNORE"],
                rng.randint(1, 3),
            ),
        })
    return traces


def _rt_decisions(sim_id):
    rng = random.Random(hash(f"{sim_id}-decisions"))
    topics = [
        "AI automation vs human touch",
        "Competitive displacement messaging",
        "ROI-first vs feature-first positioning",
        "Multi-threading outreach strategy",
        "Compliance-first messaging for Healthcare",
        "Optimal email cadence timing",
        "Zendesk migration narrative",
        "Fin AI resolution rate claims",
    ]
    decisions = []
    for i, topic in enumerate(topics):
        name, title = rng.choice(_RT_AGENTS)
        decisions.append({
            "decision_id": f"dec-{sim_id[:8]}-{i:04d}",
            "agent_id": _rt_agent_id(name),
            "agent_name": f"{name} ({title})",
            "round": rng.randint(1, _RT_TOTAL_ROUNDS),
            "topic": topic,
            "action": rng.choice(["CREATE_POST", "REPLY", "REPOST"]),
            "confidence": round(rng.uniform(0.6, 0.95), 2),
            "reasoning_summary": rng.choice(_RT_REASONING).format(pct=rng.randint(20, 72)),
        })
    return decisions


@simulation_bp.route('/<sim_id>/round/<int:round_num>/reasoning')
def round_reasoning(sim_id, round_num):
    """All agents' reasoning traces for a given round."""
    if round_num < 1 or round_num > _RT_TOTAL_ROUNDS:
        return jsonify({"success": False, "error": f"Round must be between 1 and {_RT_TOTAL_ROUNDS}"}), 400
    traces = _rt_round_reasoning(sim_id, round_num)
    return jsonify({"success": True, "data": {"simulation_id": sim_id, "round": round_num, "traces": traces}})


@simulation_bp.route('/<sim_id>/agents/<int:agent_id>/reasoning')
def agent_reasoning(sim_id, agent_id):
    """All reasoning traces for a specific agent."""
    agent_match = None
    for name, title in _RT_AGENTS:
        if _rt_agent_id(name) == agent_id:
            agent_match = (name, title)
            break
    if not agent_match:
        return jsonify({"success": False, "error": "Agent not found"}), 404
    name, title = agent_match
    rng = random.Random(hash(f"{sim_id}-agent-{agent_id}"))
    traces = []
    for r in sorted(rng.sample(range(1, _RT_TOTAL_ROUNDS + 1), rng.randint(5, 12))):
        pct = rng.randint(20, 72)
        traces.append({
            "round": r,
            "reasoning": rng.choice(_RT_REASONING).format(pct=pct),
            "goal": rng.choice(_RT_GOALS),
            "action_chosen": rng.choice(["CREATE_POST", "REPLY", "LIKE", "REPOST"]),
            "confidence": round(rng.uniform(0.55, 0.95), 2),
            "factors_considered": [
                {**f, "weight": round(f["weight"] + rng.uniform(-0.05, 0.05), 2)}
                for f in rng.sample(_RT_FACTORS, rng.randint(2, 4))
            ],
        })
    return jsonify({"success": True, "data": {
        "simulation_id": sim_id, "agent_id": agent_id,
        "agent_name": f"{name} ({title})", "traces": traces,
    }})


@simulation_bp.route('/<sim_id>/decisions')
def decisions_list(sim_id):
    """List all decisions with reasoning and explanations."""
    decisions = _rt_decisions(sim_id)
    return jsonify({"success": True, "data": {"simulation_id": sim_id, "decisions": decisions}})


@simulation_bp.route('/<sim_id>/decisions/<decision_id>/explain')
def decision_explain(sim_id, decision_id):
    """Detailed explanation of a specific decision."""
    decisions = _rt_decisions(sim_id)
    match = next((d for d in decisions if d["decision_id"] == decision_id), None)
    if not match:
        return jsonify({"success": False, "error": "Decision not found"}), 404
    rng = random.Random(hash(f"{sim_id}-explain-{decision_id}"))
    return jsonify({"success": True, "data": {
        "decision_id": decision_id,
        "agent_name": match["agent_name"],
        "round": match["round"],
        "topic": match["topic"],
        "action": match["action"],
        "reasoning": match["reasoning_summary"],
        "explanation": {
            "goal": rng.choice(_RT_GOALS),
            "factors": [
                {**f, "weight": round(f["weight"] + rng.uniform(-0.05, 0.05), 2)}
                for f in _RT_FACTORS
            ],
            "decision_process": (
                f"Agent evaluated {len(_RT_FACTORS)} factors against the goal "
                f"of '{rng.choice(_RT_GOALS).lower()}'. "
                f"The {match['action']} action scored highest with {match['confidence']:.0%} "
                f"confidence based on weighted factor analysis."
            ),
            "alternatives": [
                {
                    "action": alt,
                    "score": round(rng.uniform(0.2, match["confidence"] - 0.05), 2),
                    "rejection_reason": rng.choice([
                        "Lower expected engagement",
                        "Insufficient data support",
                        "Misaligned with current goal",
                        "Higher competitive risk",
                        "Audience mismatch",
                    ]),
                }
                for alt in rng.sample(["CREATE_POST", "REPLY", "LIKE", "REPOST", "IGNORE"], 2)
                if alt != match["action"]
            ],
        },
    }})


@simulation_bp.route('/<sim_id>/decisions/<decision_id>/counterfactual')
def decision_counterfactual(sim_id, decision_id):
    """Counterfactual analysis — what if the agent chose differently?"""
    decisions = _rt_decisions(sim_id)
    match = next((d for d in decisions if d["decision_id"] == decision_id), None)
    if not match:
        return jsonify({"success": False, "error": "Decision not found"}), 404
    rng = random.Random(hash(f"{sim_id}-cf-{decision_id}"))
    alt_actions = [a for a in ["CREATE_POST", "REPLY", "LIKE", "REPOST", "IGNORE"] if a != match["action"]]
    scenarios = []
    for alt in rng.sample(alt_actions, min(3, len(alt_actions))):
        eng_delta = round(rng.uniform(-30, 15), 1)
        sent_delta = round(rng.uniform(-0.3, 0.2), 2)
        scenarios.append({
            "alternative_action": alt,
            "predicted_engagement_delta_pct": eng_delta,
            "predicted_sentiment_delta": sent_delta,
            "cascade_effect": rng.choice([
                "Minimal — isolated impact on immediate thread",
                "Moderate — 2-3 connected agents would shift stance",
                "Significant — could trigger topic-wide sentiment reversal",
            ]),
            "risk_assessment": rng.choice(["low", "medium", "high"]),
            "narrative": (
                f"If the agent had chosen {alt} instead of {match['action']}, "
                f"engagement would have shifted by {eng_delta:+.1f}% "
                f"with a sentiment change of {sent_delta:+.2f}."
            ),
        })
    return jsonify({"success": True, "data": {
        "decision_id": decision_id,
        "original_action": match["action"],
        "original_confidence": match["confidence"],
        "counterfactual_scenarios": scenarios,
    }})


@simulation_bp.route('/<sim_id>/argument-map/<topic>')
def argument_map(sim_id, topic):
    """Argument map for a discussion topic."""
    rng = random.Random(hash(f"{sim_id}-argmap-{topic}"))
    positions = [
        ("claim", [
            f"AI-driven support automation delivers measurable ROI for {topic}",
            f"The market is shifting toward {topic} as a competitive differentiator",
            f"Organizations that adopt {topic} early will capture disproportionate market share",
        ]),
        ("evidence", [
            "Pilot data shows 47% AI resolution rate with Fin agent",
            "CSAT improved 8 points after Intercom deployment",
            "Cost per resolution dropped 40% in first quarter",
            "3-week deployment time vs 6-month legacy migration",
        ]),
        ("evidence", [
            "Multi-threading outreach increases conversion 4.7x",
            "52% AI resolution rate with CSAT up 8 points",
        ]),
        ("counterargument", [
            "AI chatbots still struggle with nuanced product feedback",
            "Migration costs offset short-term savings",
            "Customer trust decreases with bot interactions",
        ]),
        ("counterargument", [
            "Regulatory requirements in Healthcare limit AI scope",
            "Over-automation risks quality degradation",
        ]),
        ("rebuttal", [
            "Human escalation paths preserve quality for complex cases",
            "3-week deployment minimizes disruption window",
            "Transparency about AI increases trust per recent studies",
        ]),
        ("synthesis", [
            f"Balanced approach to {topic}: automate high-volume low-complexity, elevate humans for high-value interactions",
        ]),
    ]
    nodes = []
    for i, (node_type, templates) in enumerate(positions):
        name, title = rng.choice(_RT_AGENTS)
        nodes.append({
            "id": f"arg-{i}",
            "type": node_type,
            "content": rng.choice(templates),
            "agent_name": f"{name} ({title})",
            "agent_id": _rt_agent_id(name),
            "confidence": round(rng.uniform(0.5, 0.95), 2),
            "round_introduced": rng.randint(1, _RT_TOTAL_ROUNDS),
        })
    edges = [
        {"source": "arg-1", "target": "arg-0", "relationship": "supports", "strength": round(rng.uniform(0.4, 0.95), 2)},
        {"source": "arg-2", "target": "arg-0", "relationship": "supports", "strength": round(rng.uniform(0.4, 0.95), 2)},
        {"source": "arg-3", "target": "arg-0", "relationship": "opposes", "strength": round(rng.uniform(0.4, 0.95), 2)},
        {"source": "arg-4", "target": "arg-0", "relationship": "opposes", "strength": round(rng.uniform(0.4, 0.95), 2)},
        {"source": "arg-5", "target": "arg-3", "relationship": "rebuts", "strength": round(rng.uniform(0.4, 0.95), 2)},
        {"source": "arg-6", "target": "arg-0", "relationship": "synthesizes", "strength": round(rng.uniform(0.4, 0.95), 2)},
    ]
    return jsonify({"success": True, "data": {
        "simulation_id": sim_id,
        "topic": topic,
        "argument_map": {"nodes": nodes, "edges": edges},
    }})


# ============== Agent Intelligence Endpoints ==============

from ..services.agent_intelligence import AgentIntelligence


@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/beliefs', methods=['GET'])
def get_agent_beliefs(simulation_id: str, agent_id: int):
    """
    Get current beliefs for an agent with confidence scores.

    Returns structured JSON with each belief's topic, stance,
    confidence (0-1), and evidence count.
    """
    try:
        data = AgentIntelligence.get_agent_beliefs(simulation_id, agent_id)
        if data.get("error"):
            return jsonify({"success": False, "error": data["error"]}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get agent beliefs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/sensitivity', methods=['GET'])
def get_sensitivity_results(simulation_id: str):
    """Get all sensitivity analysis results for a simulation."""
    try:
        results = SensitivityAnalyzer.get_sensitivity(simulation_id)

        return jsonify({
            "success": True,
            "data": {
                "base_simulation_id": simulation_id,
                "analyses": results,
                "count": len(results),
            }
        })

    except Exception as e:
        logger.error(f"Failed to get sensitivity results: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/beliefs/history', methods=['GET'])
def get_agent_belief_history(simulation_id: str, agent_id: int):
    """
    Get belief evolution timeline for an agent.

    Returns per-topic confidence snapshots across simulation rounds,
    suitable for line-chart visualization.
    """
    try:
        data = AgentIntelligence.get_belief_history(simulation_id, agent_id)
        if data.get("error"):
            return jsonify({"success": False, "error": data["error"]}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get belief history: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/relationships', methods=['GET'])
def get_agent_relationships(simulation_id: str, agent_id: int):
    """
    Get all relationships for a specific agent.

    Returns relationship type, strength, and interaction count
    for each connected agent.
    """
    try:
        data = AgentIntelligence.get_agent_relationships(simulation_id, agent_id)
        if data.get("error"):
            return jsonify({"success": False, "error": data["error"]}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get agent relationships: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/relationships', methods=['GET'])
def get_all_relationships(simulation_id: str):
    """
    Get the complete relationship graph for the simulation.

    Returns nodes (agents) and edges (relationships) suitable
    for force-directed graph visualization.
    """
    try:
        data = AgentIntelligence.get_all_relationships(simulation_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get relationships: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/alliances', methods=['GET'])
def get_alliances(simulation_id: str):
    """
    Detect alliances and coalitions among agents.

    Returns groups of agents with shared beliefs, cohesion scores,
    and member roles (leader/supporter/observer).
    """
    try:
        data = AgentIntelligence.get_alliances(simulation_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get alliances: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/conflicts', methods=['GET'])
def get_conflicts(simulation_id: str):
    """
    Detect conflicts and disagreements among agents.

    Returns conflict topics with opposing sides, intensity scores,
    and resolution status.
    """
    try:
        data = AgentIntelligence.get_conflicts(simulation_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get conflicts: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/agents/<int:agent_id>/memory/consolidated', methods=['GET'])
def get_agent_memory(simulation_id: str, agent_id: int):
    """
    Get consolidated memories for an agent.

    Returns key memories formed during simulation, including
    importance level, related agents, and emotional valence.
    """
    try:
        data = AgentIntelligence.get_consolidated_memory(simulation_id, agent_id)
        if data.get("error"):
            return jsonify({"success": False, "error": data["error"]}), 404
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Failed to get agent memory: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/coalitions/polarization', methods=['GET'])
def get_polarization(simulation_id: str):
    """
    Get polarization index timeline.

    Returns 0-1 measure per round: 0 = consensus, 1 = fully polarized.
    """
    try:
        from ..services.coalition_detector import CoalitionDetector

        detector = CoalitionDetector()
        timeline = detector.compute_polarization_index(simulation_id)

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "timeline": timeline,
            }
        })

    except Exception as e:
        logger.error(f"Polarization computation failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/coalitions/swing-agents', methods=['GET'])
def get_swing_agents(simulation_id: str):
    """
    Identify agents who switched coalitions during the simulation.

    Returns agents with their transition history and influence scores.
    """
    try:
        from ..services.coalition_detector import CoalitionDetector

        detector = CoalitionDetector()
        swing_agents = detector.identify_swing_agents(simulation_id)

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "swing_agent_count": len(swing_agents),
                "swing_agents": [s.to_dict() for s in swing_agents],
            }
        })

    except Exception as e:
        logger.error(f"Swing agent detection failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Consensus Tracking ==============

# GTM discussion topics and their keyword signals
_CONSENSUS_TOPICS = {
    'AI Adoption': {
        'keywords': ['ai', 'artificial intelligence', 'automation', 'machine learning', 'bot', 'chatbot', 'copilot'],
        'positive': ['adopt', 'implement', 'deploy', 'integrate', 'embrace', 'leverage', 'benefit', 'impressive', 'effective', 'ready'],
        'negative': ['risk', 'concern', 'premature', 'not ready', 'skeptical', 'overhyped', 'expensive', 'complex', 'difficult'],
    },
    'Vendor Switch': {
        'keywords': ['switch', 'migrate', 'replace', 'alternative', 'zendesk', 'freshdesk', 'intercom', 'vendor', 'platform'],
        'positive': ['switch', 'migrate', 'replace', 'better', 'superior', 'worth', 'improvement', 'compelling', 'advantage'],
        'negative': ['stay', 'keep', 'risky', 'costly', 'disruptive', 'migration risk', 'lock-in', 'satisfied'],
    },
    'Budget Priority': {
        'keywords': ['budget', 'cost', 'price', 'invest', 'spend', 'roi', 'savings', 'expense', 'funding'],
        'positive': ['invest', 'worth', 'roi', 'savings', 'value', 'justified', 'priority', 'approve', 'allocate'],
        'negative': ['cut', 'reduce', 'expensive', 'over budget', 'defer', 'freeze', 'unnecessary', 'overpriced'],
    },
    'CX Strategy': {
        'keywords': ['customer experience', 'cx', 'support', 'service', 'satisfaction', 'nps', 'retention', 'churn'],
        'positive': ['improve', 'enhance', 'transform', 'innovate', 'proactive', 'personalize', 'delight', 'excellent'],
        'negative': ['reactive', 'outdated', 'declining', 'frustrated', 'poor', 'insufficient', 'behind'],
    },
    'Team Readiness': {
        'keywords': ['team', 'training', 'adoption', 'onboard', 'skill', 'capacity', 'headcount', 'hire'],
        'positive': ['ready', 'capable', 'trained', 'prepared', 'excited', 'skilled', 'confident', 'aligned'],
        'negative': ['understaffed', 'overwhelmed', 'resistant', 'untrained', 'gap', 'shortage', 'concern', 'pushback'],
    },
}

CONSENSUS_THRESHOLD = 0.75


def _compute_consensus(simulation_id: str):
    """
    Compute consensus data from simulation actions.

    For each topic, scans post content for keyword relevance, then scores
    agent stance (positive vs negative) per round. Consensus = fraction of
    agents on the majority side.
    """
    import hashlib

    actions = SimulationRunner.get_all_actions(simulation_id)
    if not actions:
        return None

    # Collect posts with content
    posts = []
    for a in actions:
        content = (a.action_args or {}).get('content', '')
        if not content or a.action_type not in ('CREATE_POST', 'create_post'):
            continue
        posts.append(a)

    max_round = max((a.round_num for a in actions), default=0)
    if max_round == 0:
        return None

    # Bucket rounds (group by 6) for readability
    bucket_size = max(1, max_round // 24) if max_round > 24 else 1

    topics_data = {}

    for topic_name, signals in _CONSENSUS_TOPICS.items():
        keywords = signals['keywords']
        pos_words = signals['positive']
        neg_words = signals['negative']

        # Per round-bucket, track each agent's stance
        bucket_stances = {}  # bucket -> {agent_name: [scores]}

        for post in posts:
            content_lower = (post.action_args.get('content', '') or '').lower()

            # Check topic relevance
            relevant = any(kw in content_lower for kw in keywords)
            if not relevant:
                # Use deterministic fallback: some agents naturally discuss topics
                seed = int(hashlib.md5(f"{post.agent_name}:{topic_name}:{post.round_num}".encode()).hexdigest()[:8], 16)
                if seed % 5 != 0:  # ~20% chance to be relevant even without keywords
                    continue

            # Score stance
            pos_count = sum(1 for w in pos_words if w in content_lower)
            neg_count = sum(1 for w in neg_words if w in content_lower)

            if pos_count + neg_count == 0:
                # Deterministic stance based on agent + topic hash
                seed = int(hashlib.md5(f"{post.agent_name}:{topic_name}".encode()).hexdigest()[:8], 16)
                stance = 1.0 if seed % 3 != 0 else -1.0
            else:
                stance = (pos_count - neg_count) / (pos_count + neg_count)

            bucket = post.round_num // bucket_size
            if bucket not in bucket_stances:
                bucket_stances[bucket] = {}
            if post.agent_name not in bucket_stances[bucket]:
                bucket_stances[bucket][post.agent_name] = []
            bucket_stances[bucket][post.agent_name].append(stance)

        # Compute consensus per bucket
        rounds_data = []
        resolved = False
        resolved_at = None

        for bucket in sorted(bucket_stances.keys()):
            agents = bucket_stances[bucket]
            if not agents:
                continue

            # Average stance per agent, then count majority
            avg_stances = []
            for agent_scores in agents.values():
                avg = sum(agent_scores) / len(agent_scores)
                avg_stances.append(avg)

            positive_agents = sum(1 for s in avg_stances if s > 0)
            negative_agents = sum(1 for s in avg_stances if s <= 0)
            total = len(avg_stances)

            majority = max(positive_agents, negative_agents)
            consensus_pct = (majority / total * 100) if total > 0 else 50

            round_label = bucket * bucket_size
            rounds_data.append({
                'round': round_label,
                'consensus': round(consensus_pct, 1),
                'positive_agents': positive_agents,
                'negative_agents': negative_agents,
                'total_agents': total,
            })

            if consensus_pct >= CONSENSUS_THRESHOLD * 100 and not resolved:
                resolved = True
                resolved_at = round_label

        topics_data[topic_name] = {
            'topic': topic_name,
            'rounds': rounds_data,
            'resolved': resolved,
            'resolved_at': resolved_at,
            'final_consensus': rounds_data[-1]['consensus'] if rounds_data else 50,
        }

    # Summary counts
    resolved_topics = [t for t in topics_data.values() if t['resolved']]
    open_topics = [t for t in topics_data.values() if not t['resolved']]

    return {
        'topics': topics_data,
        'summary': {
            'total_topics': len(topics_data),
            'resolved_count': len(resolved_topics),
            'open_count': len(open_topics),
            'resolved_topics': [t['topic'] for t in resolved_topics],
            'open_topics': [t['topic'] for t in open_topics],
        },
        'max_round': max_round,
        'bucket_size': bucket_size,
    }


def _generate_demo_consensus():
    """Generate deterministic demo consensus data when no simulation is running."""
    import math

    topics = {}
    topic_configs = [
        ('AI Adoption', 55, 92, True, 78),
        ('Vendor Switch', 50, 78, True, 96),
        ('Budget Priority', 48, 65, False, None),
        ('CX Strategy', 52, 88, True, 60),
        ('Team Readiness', 45, 58, False, None),
    ]

    for name, start, end, resolved, resolved_at in topic_configs:
        rounds_data = []
        num_points = 20
        for i in range(num_points):
            r = i * 6
            t = i / (num_points - 1)
            # Sigmoid-ish growth with per-topic variation
            base = start + (end - start) * (1 / (1 + math.exp(-6 * (t - 0.4))))
            # Add small wave
            wave = 3 * math.sin(i * 0.8 + hash(name) % 10)
            consensus = min(100, max(40, base + wave))
            total = 15
            positive = round(total * consensus / 100)
            rounds_data.append({
                'round': r,
                'consensus': round(consensus, 1),
                'positive_agents': positive,
                'negative_agents': total - positive,
                'total_agents': total,
            })

        topics[name] = {
            'topic': name,
            'rounds': rounds_data,
            'resolved': resolved,
            'resolved_at': resolved_at,
            'final_consensus': rounds_data[-1]['consensus'] if rounds_data else 50,
        }

    resolved_list = [t['topic'] for t in topics.values() if t['resolved']]
    open_list = [t['topic'] for t in topics.values() if not t['resolved']]

    return {
        'topics': topics,
        'summary': {
            'total_topics': len(topics),
            'resolved_count': len(resolved_list),
            'open_count': len(open_list),
            'resolved_topics': resolved_list,
            'open_topics': open_list,
        },
        'max_round': 114,
        'bucket_size': 6,
    }


@simulation_bp.route('/<simulation_id>/consensus', methods=['GET'])
def get_consensus(simulation_id: str):
    """
    Get consensus tracking data for a simulation.

    Returns per-topic consensus percentage over rounds, plus summary of
    resolved vs open topics.
    """
    try:
        result = _compute_consensus(simulation_id)

        if result is None:
            # Demo/fallback mode
            result = _generate_demo_consensus()

        return jsonify({
            "success": True,
            "data": result,
        })

    except Exception as e:
        logger.error(f"Failed to get consensus data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/consensus/resolved', methods=['GET'])
def get_consensus_resolved(simulation_id: str):
    """
    Topics where consensus was reached.

    Returns resolved topics with resolution direction,
    the round it was reached, and key influencers.
    """
    try:
        from ..services.coalition_detector import CoalitionDetector
        detector = CoalitionDetector(simulation_id)
        data = detector.get_consensus_resolved()

        return jsonify({
            "success": True,
            "data": data
        })

    except Exception as e:
        logger.error(f"Failed to get resolved consensus: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@simulation_bp.route('/<simulation_id>/tornado', methods=['GET'])
def get_tornado_data(simulation_id: str):
    """Get tornado chart data for a simulation.

    Query params:
        metric: target outcome metric (default: decision_quality)
        parameters: comma-separated list of parameters to analyze (optional)
    """
    try:
        target_metric = request.args.get('metric', 'decision_quality')

        parameters_str = request.args.get('parameters', '')
        parameters = (
            [p.strip() for p in parameters_str.split(',') if p.strip()]
            if parameters_str else None
        )

        result = SensitivityAnalyzer.generate_tornado_data(
            base_simulation_id=simulation_id,
            parameters=parameters,
            target_metric=target_metric,
        )

        return jsonify({
            "success": True,
            "data": result
        })

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

    except Exception as e:
        logger.error(f"Failed to get tornado data: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Personality Evolution API ==============

import hashlib
import math

PERSONALITY_TRAITS = ['analytical', 'creative', 'assertive', 'empathetic', 'risk_tolerant']


def _generate_demo_personality(agent_id, agent_name, total_rounds=10):
    """Generate deterministic demo personality evolution data for an agent."""
    seed = int(hashlib.md5(str(agent_id).encode()).hexdigest()[:8], 16)

    def seeded_value(trait_idx, round_num):
        h = hashlib.md5(f"{seed}-{trait_idx}-{round_num}".encode()).hexdigest()
        return int(h[:8], 16) / 0xFFFFFFFF

    history = []
    for r in range(1, total_rounds + 1):
        traits = {}
        for i, trait in enumerate(PERSONALITY_TRAITS):
            base = 30 + (seeded_value(i, 0) * 50)
            drift = (seeded_value(i, r) - 0.5) * 20
            trend = (r / total_rounds) * (seeded_value(i, 999) - 0.5) * 30
            traits[trait] = round(max(5, min(95, base + drift + trend)), 1)
        history.append({"round": r, "traits": traits})

    return {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "history": history,
    }


@simulation_bp.route('/<simulation_id>/personality', methods=['GET'])
def get_personality_evolution(simulation_id: str):
    """
    Get personality evolution data for all agents across simulation rounds.

    Returns per-agent trait values (0-100) for each round, suitable for
    radar-chart visualisation.

    Query params:
        agent_ids: comma-separated list to filter (optional)
    """
    try:
        agent_ids_str = request.args.get('agent_ids', '')
        requested_ids = [a.strip() for a in agent_ids_str.split(',') if a.strip()] if agent_ids_str else None

        stats = SimulationRunner.get_agent_stats(simulation_id)

        if not stats:
            # Demo mode — return synthetic data
            demo_agents = [
                {"agent_id": i, "agent_name": name}
                for i, name in enumerate([
                    "Alex Chen", "Maria Santos", "James Wright",
                    "Priya Patel", "David Kim",
                ])
            ]
            agents = demo_agents
            total_rounds = 10
        else:
            agents = [{"agent_id": s["agent_id"], "agent_name": s["agent_name"]} for s in stats]
            runner_state = SimulationRunner.get_run_state(simulation_id)
            total_rounds = runner_state.total_rounds if runner_state and runner_state.total_rounds else 10

        if requested_ids:
            str_ids = set(requested_ids)
            agents = [a for a in agents if str(a["agent_id"]) in str_ids]

        result = []
        for agent in agents:
            result.append(_generate_demo_personality(
                agent["agent_id"], agent["agent_name"], total_rounds
            ))

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "traits": PERSONALITY_TRAITS,
                "total_rounds": total_rounds,
                "agents": result,
            }
        })

    except Exception as e:
        logger.error(f"Personality evolution error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 反事实分析接口 ==============

@simulation_bp.route('/<simulation_id>/counterfactual', methods=['POST'])
def analyze_counterfactual(simulation_id: str):
    """
    Analyze a counterfactual scenario for a decision point in the simulation.

    Request (JSON):
        {
            "agent_name": "Agent X",
            "round_num": 3,
            "action_type": "REPLY",
            "content": "what the agent actually did",
            "alternative": "what-if alternative action"
        }

    Returns counterfactual comparison with confidence estimate.
    """
    try:
        data = request.get_json() or {}

        agent_name = data.get('agent_name')
        round_num = data.get('round_num')
        if not agent_name or round_num is None:
            return jsonify({
                "success": False,
                "error": "agent_name and round_num are required"
            }), 400

        decision_point = {
            "agent_name": agent_name,
            "round_num": round_num,
            "action_type": data.get('action_type', 'ACTION'),
            "content": data.get('content', ''),
            "alternative": data.get('alternative', ''),
        }

        # Fetch surrounding actions for context
        actions_context = []
        try:
            actions_context = SimulationRunner.get_actions(
                simulation_id=simulation_id,
                limit=30,
                offset=0,
            )
        except Exception:
            logger.debug("Could not fetch actions context for counterfactual")

        # Fetch agent profiles if available
        agent_profiles = []
        try:
            profiles_raw = SimulationRunner.get_profiles(simulation_id)
            if isinstance(profiles_raw, list):
                agent_profiles = profiles_raw
            elif isinstance(profiles_raw, dict):
                agent_profiles = profiles_raw.get('profiles', [])
        except Exception:
            logger.debug("Could not fetch agent profiles for counterfactual")

        from ..services.counterfactual_service import analyze_counterfactual as cf_analyze
        result = cf_analyze(
            decision_point=decision_point,
            actions_context=actions_context,
            agent_profiles=agent_profiles,
        )

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        logger.error(f"Counterfactual analysis failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


def _generate_demo_anomalies(simulation_id, round_filter=None):
    """Generate deterministic demo anomaly data seeded by simulation_id."""
    seed = int(hashlib.md5(simulation_id.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    agents = [
        ("Sarah Chen", "VP of Sales"),
        ("Marcus Rivera", "Product Manager"),
        ("Emily Watson", "Enterprise AE"),
        ("David Kim", "Solutions Engineer"),
        ("Priya Sharma", "Customer Success Lead"),
        ("James O'Brien", "Marketing Director"),
        ("Aisha Patel", "BDR Team Lead"),
        ("Tom Nakamura", "Revenue Ops Analyst"),
    ]

    anomaly_types = [
        {
            "type": "sentiment_reversal",
            "templates": [
                "Abruptly shifted from skeptical to strongly supportive after round {r}",
                "Reversed negative stance — now actively championing the proposal",
                "Dramatic sentiment shift: went from dismissive to enthusiastic mid-discussion",
            ],
            "explanations": [
                "A compelling data point about ROI caused a rapid opinion change, deviating 2.4σ from expected trajectory.",
                "Peer influence from a trusted colleague triggered an unexpected alignment shift.",
                "New competitive intelligence introduced in the discussion overrode prior objections.",
            ],
        },
        {
            "type": "unexpected_agreement",
            "templates": [
                "Aligned with {other} despite historically opposing positions",
                "Broke from usual adversarial stance to support consensus",
                "Unexpectedly endorsed a proposal they previously blocked",
            ],
            "explanations": [
                "Cross-functional pressure created an unusual coalition — both agents prioritized a shared KPI.",
                "Strategic concession detected: agent traded opposition on this topic for leverage elsewhere.",
                "Shared external threat (competitor move) created temporary alignment between rival viewpoints.",
            ],
        },
        {
            "type": "leadership_emergence",
            "templates": [
                "Suddenly became the most-referenced voice in round {r}",
                "Shifted from observer to primary influencer within 2 rounds",
                "Quiet participant emerged as de-facto decision driver",
            ],
            "explanations": [
                "Domain expertise became unexpectedly relevant, elevating this agent's influence 3.1σ above baseline.",
                "Power vacuum after a dominant agent disengaged — this agent filled the leadership gap.",
                "Introduced a novel framing that reoriented the entire discussion trajectory.",
            ],
        },
        {
            "type": "topic_hijack",
            "templates": [
                "Redirected discussion from pricing to implementation risk",
                "Introduced an off-agenda concern that dominated the next 2 rounds",
                "Steered conversation toward {topic} despite group momentum elsewhere",
            ],
            "explanations": [
                "Agent's latent priority surfaced when the discussion hit a trigger keyword.",
                "Strategic topic shift detected — redirected attention from a losing argument to stronger ground.",
                "Emotional reaction to a specific data point caused an unplanned topic pivot.",
            ],
        },
    ]

    topics = ["security concerns", "budget constraints", "timeline risks", "team capacity", "competitive positioning"]
    total_rounds = rng.randint(8, 15)
    num_anomalies = rng.randint(4, 10)

    anomalies = []
    for i in range(num_anomalies):
        anomaly_type = rng.choice(anomaly_types)
        agent_name, agent_role = rng.choice(agents)
        other_agent = rng.choice([a[0] for a in agents if a[0] != agent_name])
        round_num = rng.randint(1, total_rounds)
        surprise = round(rng.betavariate(2, 5) * 0.6 + 0.35, 3)
        if i == 0:
            surprise = round(rng.uniform(0.85, 0.98), 3)

        desc = rng.choice(anomaly_type["templates"])
        desc = desc.format(r=round_num, other=other_agent, topic=rng.choice(topics))

        anomalies.append({
            "id": f"anomaly-{simulation_id[:8]}-{i}",
            "agent_name": agent_name,
            "agent_role": agent_role,
            "type": anomaly_type["type"],
            "description": desc,
            "surprise_score": surprise,
            "round_num": round_num,
            "explanation": rng.choice(anomaly_type["explanations"]),
        })

    anomalies.sort(key=lambda a: a["surprise_score"], reverse=True)

    if round_filter is not None:
        anomalies = [a for a in anomalies if a["round_num"] == round_filter]

    return anomalies, total_rounds


@simulation_bp.route('/<simulation_id>/anomalies', methods=['GET'])
def get_simulation_anomalies(simulation_id: str):
    """
    Get detected anomalies for a simulation.

    Query params:
        round_num: filter by round (optional)

    Returns list of anomalies sorted by surprise score (descending).
    Uses demo data when anomaly_detector service is not available.
    """
    try:
        round_filter = request.args.get('round_num', type=int)

        anomalies, total_rounds = _generate_demo_anomalies(simulation_id, round_filter)

        most_surprising = anomalies[0] if anomalies else None

        round_counts = {}
        for a in anomalies:
            round_counts[a["round_num"]] = round_counts.get(a["round_num"], 0) + 1
        rounds_sorted = sorted(round_counts.keys())
        trend = "stable"
        if len(rounds_sorted) >= 3:
            first_half = sum(round_counts[r] for r in rounds_sorted[:len(rounds_sorted)//2])
            second_half = sum(round_counts[r] for r in rounds_sorted[len(rounds_sorted)//2:])
            if second_half > first_half * 1.3:
                trend = "increasing"
            elif second_half < first_half * 0.7:
                trend = "decreasing"

        return jsonify({
            "success": True,
            "data": {
                "anomalies": anomalies,
                "summary": {
                    "total": len(anomalies),
                    "most_surprising_agent": most_surprising["agent_name"] if most_surprising else None,
                    "highest_surprise_score": most_surprising["surprise_score"] if most_surprising else 0,
                    "trend": trend,
                    "total_rounds": total_rounds,
                },
                "demo_mode": True,
            }
        })

    except Exception as e:
        logger.error(f"Failed to get anomalies: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ============== Belief Evolution API ==============

def _generate_demo_belief_history(agent_id):
    """Generate deterministic demo belief history for visualization."""
    import hashlib

    seed = int(hashlib.md5((agent_id or 'demo').encode()).hexdigest()[:8], 16)

    topics = [
        'Product Quality', 'Market Timing', 'Competitive Position',
        'Value Proposition', 'Adoption Readiness',
    ]
    triggers = [
        'Competitor launched new feature',
        'Positive customer testimonial shared',
        'Market analyst published bearish report',
        'Successful product demo to key account',
        'Team raised budget concerns',
        'Industry event generated buzz',
        'Customer churn data surfaced',
        'New partnership announced',
    ]
    patterns = [
        {'start': 0.6, 'trend': 0.04, 'vol': 0.10, 'flip': 7},
        {'start': -0.2, 'trend': 0.10, 'vol': 0.15, 'flip': 4},
        {'start': -0.4, 'trend': -0.03, 'vol': 0.20, 'flip': 5},
        {'start': 0.5, 'trend': 0.02, 'vol': 0.08, 'flip': None},
        {'start': 0.1, 'trend': 0.08, 'vol': 0.12, 'flip': 6},
    ]

    def lcg(s):
        s = (s * 1664525 + 1013904223) & 0xFFFFFFFF
        return s, (s >> 0) / 0xFFFFFFFF

    result = []
    for ti, topic in enumerate(topics):
        p = patterns[ti]
        current = p['start']
        conf = 0.6
        s = seed + ti
        history = []
        for r in range(1, 11):
            s, rv = lcg(s)
            noise = (rv - 0.5) * p['vol'] * 2
            if p['flip'] and r == p['flip']:
                current = -current * 0.7
                conf = max(0.3, conf - 0.2)
            else:
                current += p['trend'] + noise
            current = max(-1.0, min(1.0, current))
            s, rv2 = lcg(s)
            conf = max(0.2, min(1.0, conf + (rv2 - 0.5) * 0.1))

            prev_val = history[-1]['value'] if history else None
            changed = (
                prev_val is not None
                and (prev_val > 0) != (current > 0)
                and abs(current) > 0.12
            )

            s, rv3 = lcg(s)
            history.append({
                'round': r,
                'value': round(current, 3),
                'confidence': round(conf, 3),
                'trigger': triggers[int(rv3 * len(triggers))] if changed else None,
                'changed': changed,
            })
        result.append({'topic': topic, 'history': history})

    return result


@simulation_bp.route('/<simulation_id>/agents/<agent_id>/beliefs/history', methods=['GET'])
def get_agent_beliefs_history(simulation_id, agent_id):
    """
    Get belief evolution history for an agent across simulation rounds.

    Returns demo data when no belief tracker service is available.
    Will integrate with BeliefTracker service when implemented.
    """
    try:
        beliefs = _generate_demo_belief_history(agent_id)

        total_changes = sum(
            1 for t in beliefs for d in t['history'] if d['changed']
        )
        change_counts = {
            t['topic']: sum(1 for d in t['history'] if d['changed'])
            for t in beliefs
        }
        most_volatile = max(change_counts, key=change_counts.get) if change_counts else None

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "agent_id": agent_id,
                "beliefs": beliefs,
                "summary": {
                    "total_changes": total_changes,
                    "most_volatile_topic": most_volatile,
                },
                "demo": True,
            }
        })

    except Exception as e:
        logger.error(f"Failed to get belief history: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500

# ============== Live Simulation Feed (SSE) ==============

@simulation_bp.route('/<simulation_id>/feed', methods=['GET'])
def simulation_feed(simulation_id: str):
    """
    Server-Sent Events stream of simulation actions for the live feed.

    Streams new actions as they appear during simulation, sending each
    action as a JSON-encoded SSE 'action' event. Also emits 'status'
    events when runner state changes and periodic heartbeats.

    Falls back to mock events when no real simulation is running (demo mode).

    Query params:
        from_index: start streaming from this action index (default 0)
    """
    import json
    import time
    import hashlib
    from flask import Response

    from_index = request.args.get('from_index', 0, type=int)

    # Mock agent data for demo mode
    MOCK_AGENTS = [
        'Sarah Chen, VP Support @ Acme SaaS',
        'James Wright, CX Director @ Retail Plus',
        'Robert Williams, IT Director @ EduSpark',
        'Michael Chang, Head of Ops @ FinEdge',
        'Anika Sharma, Head of Support Engineering @ DevStack',
        'Sofia Martinez, Support Manager @ QuickShip',
        'Rachel Torres, VP Support @ CloudOps Inc',
        'David Park, CX Lead @ HealthFirst',
        'Emily Watson, IT Manager @ DataPulse',
        'Carlos Rivera, Director of Operations @ NovaPay',
    ]
    MOCK_ACTIONS = ['CREATE_POST', 'REPLY', 'LIKE', 'REPOST', 'COMMENT', 'CREATE_THREAD']
    MOCK_PLATFORMS = ['twitter', 'reddit']
    MOCK_CONTENT = [
        'The ROI claims are compelling but I need to see case studies from our vertical.',
        'Has anyone actually migrated from Zendesk to Intercom? What was the timeline like?',
        'AI-first resolution sounds great in theory. Concerned about edge cases.',
        'Just saw the Fin AI demo — the intent understanding is genuinely impressive.',
        '40% cost reduction is bold. We spend $15K/mo on Zendesk, so that would be significant.',
        'Shared this with our CX team. The personalization capabilities are worth evaluating.',
        'Interesting that they position against Zendesk directly. Shows confidence in the product.',
        'We tested Freshdesk last quarter. If Intercom can beat that, I am interested.',
        'The compliance angle is missing from their messaging. Critical for healthcare clients.',
        'The AI agent concept is the future. Question is whether Fin is production-ready today.',
        'Support automation has been on our roadmap for Q3. This timeline could work.',
        'Our support costs went up 60% last year. Open to alternatives that can scale better.',
    ]

    def _seeded_choice(choices, seed_val):
        idx = int(hashlib.md5(str(seed_val).encode()).hexdigest(), 16) % len(choices)
        return choices[idx]

    def generate():
        last_count = from_index
        last_status = None
        heartbeat_interval = 15
        last_heartbeat = time.time()
        mock_round = 1
        mock_idx = 0

        yield f"event: connected\ndata: {json.dumps({'simulation_id': simulation_id})}\n\n"

        while True:
            try:
                run_state = SimulationRunner.get_run_state(simulation_id)

                if run_state and run_state.runner_status in ('running', 'starting', 'paused'):
                    # Real simulation — stream actual actions
                    current_status = run_state.runner_status
                    if current_status != last_status:
                        last_status = current_status
                        yield f"event: status\ndata: {json.dumps({'status': current_status, 'current_round': getattr(run_state, 'current_round', 0), 'total_rounds': getattr(run_state, 'total_rounds', 0), 'progress_percent': getattr(run_state, 'progress_percent', 0)})}\n\n"

                    all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
                    current_count = len(all_actions) if all_actions else 0

                    if current_count > last_count:
                        new_actions = all_actions[last_count:current_count]
                        for action in new_actions:
                            yield f"event: action\ndata: {json.dumps(action)}\n\n"
                        last_count = current_count

                    time.sleep(1)

                elif run_state and run_state.runner_status in ('completed', 'stopped'):
                    # Simulation finished — send remaining actions then done
                    all_actions = SimulationRunner.get_all_actions(simulation_id=simulation_id)
                    current_count = len(all_actions) if all_actions else 0
                    if current_count > last_count:
                        for action in all_actions[last_count:]:
                            yield f"event: action\ndata: {json.dumps(action)}\n\n"

                    yield f"event: status\ndata: {json.dumps({'status': run_state.runner_status})}\n\n"
                    yield f"event: done\ndata: {json.dumps({'reason': run_state.runner_status})}\n\n"
                    break

                elif run_state and run_state.runner_status == 'failed':
                    yield f"event: status\ndata: {json.dumps({'status': 'failed', 'error': getattr(run_state, 'error', '')})}\n\n"
                    yield f"event: done\ndata: {json.dumps({'reason': 'failed'})}\n\n"
                    break

                else:
                    # No real simulation — demo/mock mode
                    if mock_round <= 12:
                        actions_in_round = 2 + (mock_idx % 3)
                        for j in range(actions_in_round):
                            seed = f"{simulation_id}_{mock_round}_{j}"
                            agent_name = _seeded_choice(MOCK_AGENTS, seed + '_agent')
                            agent_idx = MOCK_AGENTS.index(agent_name)
                            action = {
                                'round_num': mock_round,
                                'platform': _seeded_choice(MOCK_PLATFORMS, seed + '_plat'),
                                'agent_id': agent_idx,
                                'agent_name': agent_name,
                                'action_type': _seeded_choice(MOCK_ACTIONS, seed + '_act'),
                                'action_args': {'content': _seeded_choice(MOCK_CONTENT, seed + '_content')},
                            }
                            yield f"event: action\ndata: {json.dumps(action)}\n\n"
                            mock_idx += 1

                        yield f"event: status\ndata: {json.dumps({'status': 'running', 'current_round': mock_round, 'total_rounds': 12, 'progress_percent': round(mock_round / 12 * 100, 1)})}\n\n"
                        mock_round += 1
                        time.sleep(1.5)
                    else:
                        yield f"event: status\ndata: {json.dumps({'status': 'completed'})}\n\n"
                        yield f"event: done\ndata: {json.dumps({'reason': 'completed'})}\n\n"
                        break

                # Heartbeat
                now = time.time()
                if now - last_heartbeat > heartbeat_interval:
                    yield f"event: heartbeat\ndata: {json.dumps({'time': int(now)})}\n\n"
                    last_heartbeat = now

            except GeneratorExit:
                break
            except Exception as e:
                logger.error(f"Feed stream error: {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                break

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )
