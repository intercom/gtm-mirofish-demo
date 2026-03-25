"""
Report API路由
提供模拟报告生成、获取、对话等接口
"""

import os
import traceback
import threading
from flask import request, jsonify, send_file

from . import report_bp
from ..config import Config
from ..services.report_agent import (
    ReportAgent, ReportManager, ReportStatus, REPORT_TYPES,
)
from ..services.report_templates import (
    generate_demo_report, CHART_DATA_DEMO,
    list_templates, get_template, get_template_dict,
)
from ..services.simulation_manager import SimulationManager
from ..services.data_sources import DataSourceService
from ..models.project import ProjectManager
from ..models.task import TaskManager, TaskStatus
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.report')


def _is_demo_mode() -> bool:
    """Check if we should operate in demo mode (no LLM key configured)."""
    return not Config.LLM_API_KEY


# ============== 报告生成接口 ==============

@report_bp.route('/types', methods=['GET'])
def list_report_types():
    """List available report types."""
    return jsonify({
        "success": True,
        "data": {
            "types": [
                {"id": k, "description": v}
                for k, v in REPORT_TYPES.items()
            ],
            "default": "executive_summary",
        }
    })


@report_bp.route('/generate', methods=['POST'])
def generate_report():
    """
    生成模拟分析报告（异步任务）

    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",          // 必填，模拟ID
            "report_type": "executive_summary",   // 可选，报告类型
            "custom_prompt": "Focus on ...",      // 可选，自定义生成指令
            "include_charts": true,               // 可选，是否包含图表数据
            "force_regenerate": false              // 可选，强制重新生成
        }

    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "report_id": "report_xxxx",
                "task_id": "task_xxxx",
                "status": "generating",
                "demo_mode": false
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

        report_type = data.get('report_type', 'executive_summary')
        if report_type not in REPORT_TYPES:
            return jsonify({
                "success": False,
                "error": f"不支持的报告类型: {report_type}. 可选: {list(REPORT_TYPES.keys())}"
            }), 400

        template_id = data.get('template_id')
        custom_prompt = data.get('custom_prompt')
        include_charts = data.get('include_charts', True)
        force_regenerate = data.get('force_regenerate', False)

        # 检查是否已有报告
        if not force_regenerate:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "message": "报告已存在",
                        "already_generated": True
                    }
                })

        import uuid
        report_id = f"report_{uuid.uuid4().hex[:12]}"

        # Demo mode: generate instantly from templates
        if _is_demo_mode():
            report = generate_demo_report(
                report_id=report_id,
                simulation_id=simulation_id,
                report_type=report_type,
                custom_prompt=custom_prompt,
                include_charts=include_charts,
            )
            return jsonify({
                "success": True,
                "data": {
                    "simulation_id": simulation_id,
                    "report_id": report.report_id,
                    "task_id": None,
                    "status": "completed",
                    "message": "Demo report generated from template",
                    "demo_mode": True,
                    "already_generated": False,
                }
            })

        # Live mode: requires simulation + graph
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)

        if not state:
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404

        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"项目不存在: {state.project_id}"
            }), 404

        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "缺少图谱ID，请确保已构建图谱"
            }), 400

        simulation_requirement = project.simulation_requirement
        if not simulation_requirement:
            return jsonify({
                "success": False,
                "error": "缺少模拟需求描述"
            }), 400

        # Resolve template if provided
        template = get_template(template_id) if template_id else None

        # 创建异步任务
        task_manager = TaskManager()
        task_id = task_manager.create_task(
            task_type="report_generate",
            metadata={
                "simulation_id": simulation_id,
                "graph_id": graph_id,
                "report_id": report_id,
                "report_type": report_type,
                "custom_prompt": custom_prompt,
                "include_charts": include_charts,
                "template_id": template_id,
            }
        )

        def run_generate():
            try:
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.PROCESSING,
                    progress=0,
                    message="初始化Report Agent..."
                )

                agent = ReportAgent(
                    graph_id=graph_id,
                    simulation_id=simulation_id,
                    simulation_requirement=simulation_requirement
                )

                def progress_callback(stage, progress, message):
                    task_manager.update_task(
                        task_id,
                        progress=progress,
                        message=f"[{stage}] {message}"
                    )

                report = agent.generate_report(
                    progress_callback=progress_callback,
                    report_id=report_id,
                    template=template,
                )

                # Attach generation metadata
                report.report_type = report_type
                report.custom_prompt = custom_prompt
                report.include_charts = include_charts
                if include_charts:
                    report.chart_data = CHART_DATA_DEMO

                ReportManager.save_report(report)

                if report.status == ReportStatus.COMPLETED:
                    task_manager.complete_task(
                        task_id,
                        result={
                            "report_id": report.report_id,
                            "simulation_id": simulation_id,
                            "status": "completed"
                        }
                    )
                else:
                    task_manager.fail_task(task_id, report.error or "报告生成失败")

            except Exception as e:
                logger.error(f"报告生成失败: {str(e)}")
                task_manager.fail_task(task_id, str(e))

        thread = threading.Thread(target=run_generate, daemon=True)
        thread.start()

        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "report_id": report_id,
                "task_id": task_id,
                "status": "generating",
                "message": "报告生成任务已启动",
                "demo_mode": False,
                "already_generated": False,
            }
        })

    except Exception as e:
        logger.error(f"启动报告生成任务失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/generate/status', methods=['POST'])
def get_generate_status():
    """
    查询报告生成任务进度
    
    请求（JSON）：
        {
            "task_id": "task_xxxx",         // 可选，generate返回的task_id
            "simulation_id": "sim_xxxx"     // 可选，模拟ID
        }
    
    返回：
        {
            "success": true,
            "data": {
                "task_id": "task_xxxx",
                "status": "processing|completed|failed",
                "progress": 45,
                "message": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        task_id = data.get('task_id')
        simulation_id = data.get('simulation_id')
        
        # 如果提供了simulation_id，先检查是否已有完成的报告
        if simulation_id:
            existing_report = ReportManager.get_report_by_simulation(simulation_id)
            if existing_report and existing_report.status == ReportStatus.COMPLETED:
                return jsonify({
                    "success": True,
                    "data": {
                        "simulation_id": simulation_id,
                        "report_id": existing_report.report_id,
                        "status": "completed",
                        "progress": 100,
                        "message": "报告已生成",
                        "already_completed": True
                    }
                })
        
        if not task_id:
            return jsonify({
                "success": False,
                "error": "请提供 task_id 或 simulation_id"
            }), 400
        
        task_manager = TaskManager()
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({
                "success": False,
                "error": f"任务不存在: {task_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": task.to_dict()
        })
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@report_bp.route('/<report_id>/status', methods=['GET'])
def get_report_status(report_id: str):
    """
    GET-based report generation status.

    Returns the report's current status plus progress info if still generating.
    """
    try:
        report = ReportManager.get_report(report_id)
        if not report:
            return jsonify({
                "success": False,
                "error": f"报告不存在: {report_id}"
            }), 404

        result = {
            "report_id": report_id,
            "status": report.status.value,
            "report_type": report.report_type,
        }

        if report.status == ReportStatus.COMPLETED:
            result["progress"] = 100
            result["message"] = "Report generation complete"
            result["completed_at"] = report.completed_at
        elif report.status == ReportStatus.FAILED:
            result["progress"] = 0
            result["message"] = report.error or "Generation failed"
        else:
            progress = ReportManager.get_progress(report_id)
            if progress:
                result["progress"] = progress.get("progress", 0)
                result["message"] = progress.get("message", "")
                result["current_section"] = progress.get("current_section")
                result["completed_sections"] = progress.get("completed_sections", [])
            else:
                result["progress"] = 0
                result["message"] = "Pending"

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"获取报告状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/tool-calls', methods=['GET'])
def get_tool_calls(report_id: str):
    """
    Transparency log of tool calls the report agent made.

    Filters the agent log to show only ReACT Thought/Action/Observation entries.
    """
    try:
        report = ReportManager.get_report(report_id)
        if not report:
            return jsonify({
                "success": False,
                "error": f"报告不存在: {report_id}"
            }), 404

        log_data = ReportManager.get_agent_log(report_id, from_line=0)
        all_logs = log_data.get("logs", [])

        tool_actions = ("react_thought", "tool_call", "tool_result", "llm_response")
        tool_calls = [
            entry for entry in all_logs
            if entry.get("action") in tool_actions
        ]

        # Compute summary stats
        thoughts = [e for e in tool_calls if e.get("action") == "react_thought"]
        calls = [e for e in tool_calls if e.get("action") == "tool_call"]
        results = [e for e in tool_calls if e.get("action") == "tool_result"]

        summary = {
            "total_thoughts": len(thoughts),
            "total_tool_calls": len(calls),
            "total_results": len(results),
            "tools_used": list({
                e.get("details", {}).get("tool_name", "unknown")
                for e in calls
            }),
        }
        if all_logs:
            first_ts = all_logs[0].get("timestamp", "")
            last_ts = all_logs[-1].get("timestamp", "")
            summary["started_at"] = first_ts
            summary["ended_at"] = last_ts

        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "summary": summary,
                "tool_calls": tool_calls,
                "count": len(tool_calls),
            }
        })

    except Exception as e:
        logger.error(f"获取工具调用日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 报告获取接口 ==============

@report_bp.route('/<report_id>', methods=['GET'])
def get_report(report_id: str):
    """
    获取报告详情
    
    返回：
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "simulation_id": "sim_xxxx",
                "status": "completed",
                "outline": {...},
                "markdown_content": "...",
                "created_at": "...",
                "completed_at": "..."
            }
        }
    """
    try:
        report = ReportManager.get_report(report_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": f"报告不存在: {report_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict()
        })
        
    except Exception as e:
        logger.error(f"获取报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/by-simulation/<simulation_id>', methods=['GET'])
def get_report_by_simulation(simulation_id: str):
    """
    根据模拟ID获取报告
    
    返回：
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                ...
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": f"该模拟暂无报告: {simulation_id}",
                "has_report": False
            }), 404
        
        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "has_report": True
        })
        
    except Exception as e:
        logger.error(f"获取报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/list', methods=['GET'])
def list_reports():
    """
    列出所有报告
    
    Query参数：
        simulation_id: 按模拟ID过滤（可选）
        limit: 返回数量限制（默认50）
    
    返回：
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    """
    try:
        simulation_id = request.args.get('simulation_id')
        limit = request.args.get('limit', 50, type=int)
        
        reports = ReportManager.list_reports(
            simulation_id=simulation_id,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": [r.to_dict() for r in reports],
            "count": len(reports)
        })
        
    except Exception as e:
        logger.error(f"列出报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/download', methods=['GET'])
def download_report(report_id: str):
    """
    下载报告（Markdown格式）
    
    返回Markdown文件
    """
    try:
        report = ReportManager.get_report(report_id)
        
        if not report:
            return jsonify({
                "success": False,
                "error": f"报告不存在: {report_id}"
            }), 404
        
        md_path = ReportManager._get_report_markdown_path(report_id)
        
        if not os.path.exists(md_path):
            # 如果MD文件不存在，生成一个临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(report.markdown_content)
                temp_path = f.name
            
            return send_file(
                temp_path,
                as_attachment=True,
                download_name=f"{report_id}.md"
            )
        
        return send_file(
            md_path,
            as_attachment=True,
            download_name=f"{report_id}.md"
        )
        
    except Exception as e:
        logger.error(f"下载报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id: str):
    """删除报告"""
    try:
        success = ReportManager.delete_report(report_id)
        
        if not success:
            return jsonify({
                "success": False,
                "error": f"报告不存在: {report_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "message": f"报告已删除: {report_id}"
        })
        
    except Exception as e:
        logger.error(f"删除报告失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Report Agent对话接口 ==============

@report_bp.route('/chat', methods=['POST'])
def chat_with_report_agent():
    """
    与Report Agent对话
    
    Report Agent可以在对话中自主调用检索工具来回答问题
    
    请求（JSON）：
        {
            "simulation_id": "sim_xxxx",        // 必填，模拟ID
            "message": "请解释一下舆情走向",    // 必填，用户消息
            "chat_history": [                   // 可选，对话历史
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
    
    返回：
        {
            "success": true,
            "data": {
                "response": "Agent回复...",
                "tool_calls": [调用的工具列表],
                "sources": [信息来源]
            }
        }
    """
    try:
        data = request.get_json() or {}
        
        simulation_id = data.get('simulation_id')
        message = data.get('message')
        chat_history = data.get('chat_history', [])
        
        if not simulation_id:
            return jsonify({
                "success": False,
                "error": "请提供 simulation_id"
            }), 400
        
        if not message:
            return jsonify({
                "success": False,
                "error": "请提供 message"
            }), 400
        
        # 获取模拟和项目信息
        manager = SimulationManager()
        state = manager.get_simulation(simulation_id)
        
        if not state:
            return jsonify({
                "success": False,
                "error": f"模拟不存在: {simulation_id}"
            }), 404
        
        project = ProjectManager.get_project(state.project_id)
        if not project:
            return jsonify({
                "success": False,
                "error": f"项目不存在: {state.project_id}"
            }), 404
        
        graph_id = state.graph_id or project.graph_id
        if not graph_id:
            return jsonify({
                "success": False,
                "error": "缺少图谱ID"
            }), 400
        
        simulation_requirement = project.simulation_requirement or ""
        
        # 创建Agent并进行对话
        agent = ReportAgent(
            graph_id=graph_id,
            simulation_id=simulation_id,
            simulation_requirement=simulation_requirement
        )
        
        result = agent.chat(message=message, chat_history=chat_history)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"对话失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 报告进度与分章节接口 ==============

@report_bp.route('/<report_id>/progress', methods=['GET'])
def get_report_progress(report_id: str):
    """
    获取报告生成进度（实时）
    
    返回：
        {
            "success": true,
            "data": {
                "status": "generating",
                "progress": 45,
                "message": "正在生成章节: 关键发现",
                "current_section": "关键发现",
                "completed_sections": ["执行摘要", "模拟背景"],
                "updated_at": "2025-12-09T..."
            }
        }
    """
    try:
        progress = ReportManager.get_progress(report_id)
        
        if not progress:
            return jsonify({
                "success": False,
                "error": f"报告不存在或进度信息不可用: {report_id}"
            }), 404
        
        return jsonify({
            "success": True,
            "data": progress
        })
        
    except Exception as e:
        logger.error(f"获取报告进度失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/sections', methods=['GET'])
def get_report_sections(report_id: str):
    """
    获取已生成的章节列表（分章节输出）
    
    前端可以轮询此接口获取已生成的章节内容，无需等待整个报告完成
    
    返回：
        {
            "success": true,
            "data": {
                "report_id": "report_xxxx",
                "sections": [
                    {
                        "filename": "section_01.md",
                        "section_index": 1,
                        "content": "## 执行摘要\\n\\n..."
                    },
                    ...
                ],
                "total_sections": 3,
                "is_complete": false
            }
        }
    """
    try:
        sections = ReportManager.get_generated_sections(report_id)
        
        # 获取报告状态
        report = ReportManager.get_report(report_id)
        is_complete = report is not None and report.status == ReportStatus.COMPLETED
        
        return jsonify({
            "success": True,
            "data": {
                "report_id": report_id,
                "sections": sections,
                "total_sections": len(sections),
                "is_complete": is_complete
            }
        })
        
    except Exception as e:
        logger.error(f"获取章节列表失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/section/<int:section_index>', methods=['GET'])
def get_single_section(report_id: str, section_index: int):
    """
    获取单个章节内容
    
    返回：
        {
            "success": true,
            "data": {
                "filename": "section_01.md",
                "content": "## 执行摘要\\n\\n..."
            }
        }
    """
    try:
        section_path = ReportManager._get_section_path(report_id, section_index)
        
        if not os.path.exists(section_path):
            return jsonify({
                "success": False,
                "error": f"章节不存在: section_{section_index:02d}.md"
            }), 404
        
        with open(section_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "data": {
                "filename": f"section_{section_index:02d}.md",
                "section_index": section_index,
                "content": content
            }
        })
        
    except Exception as e:
        logger.error(f"获取章节内容失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 报告状态检查接口 ==============

@report_bp.route('/check/<simulation_id>', methods=['GET'])
def check_report_status(simulation_id: str):
    """
    检查模拟是否有报告，以及报告状态
    
    用于前端判断是否解锁Interview功能
    
    返回：
        {
            "success": true,
            "data": {
                "simulation_id": "sim_xxxx",
                "has_report": true,
                "report_status": "completed",
                "report_id": "report_xxxx",
                "interview_unlocked": true
            }
        }
    """
    try:
        report = ReportManager.get_report_by_simulation(simulation_id)
        
        has_report = report is not None
        report_status = report.status.value if report else None
        report_id = report.report_id if report else None
        
        # 只有报告完成后才解锁interview
        interview_unlocked = has_report and report.status == ReportStatus.COMPLETED
        
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": simulation_id,
                "has_report": has_report,
                "report_status": report_status,
                "report_id": report_id,
                "interview_unlocked": interview_unlocked
            }
        })
        
    except Exception as e:
        logger.error(f"检查报告状态失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Agent 日志接口 ==============

@report_bp.route('/<report_id>/agent-log', methods=['GET'])
def get_agent_log(report_id: str):
    """
    获取 Report Agent 的详细执行日志
    
    实时获取报告生成过程中的每一步动作，包括：
    - 报告开始、规划开始/完成
    - 每个章节的开始、工具调用、LLM响应、完成
    - 报告完成或失败
    
    Query参数：
        from_line: 从第几行开始读取（可选，默认0，用于增量获取）
    
    返回：
        {
            "success": true,
            "data": {
                "logs": [
                    {
                        "timestamp": "2025-12-13T...",
                        "elapsed_seconds": 12.5,
                        "report_id": "report_xxxx",
                        "action": "tool_call",
                        "stage": "generating",
                        "section_title": "执行摘要",
                        "section_index": 1,
                        "details": {
                            "tool_name": "insight_forge",
                            "parameters": {...},
                            ...
                        }
                    },
                    ...
                ],
                "total_lines": 25,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)
        
        log_data = ReportManager.get_agent_log(report_id, from_line=from_line)
        
        return jsonify({
            "success": True,
            "data": log_data
        })
        
    except Exception as e:
        logger.error(f"获取Agent日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/agent-log/stream', methods=['GET'])
def stream_agent_log(report_id: str):
    """
    获取完整的 Agent 日志（一次性获取全部）
    
    返回：
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 25
            }
        }
    """
    try:
        logs = ReportManager.get_agent_log_stream(report_id)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f"获取Agent日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== 控制台日志接口 ==============

@report_bp.route('/<report_id>/console-log', methods=['GET'])
def get_console_log(report_id: str):
    """
    获取 Report Agent 的控制台输出日志
    
    实时获取报告生成过程中的控制台输出（INFO、WARNING等），
    这与 agent-log 接口返回的结构化 JSON 日志不同，
    是纯文本格式的控制台风格日志。
    
    Query参数：
        from_line: 从第几行开始读取（可选，默认0，用于增量获取）
    
    返回：
        {
            "success": true,
            "data": {
                "logs": [
                    "[19:46:14] INFO: 搜索完成: 找到 15 条相关事实",
                    "[19:46:14] INFO: 图谱搜索: graph_id=xxx, query=...",
                    ...
                ],
                "total_lines": 100,
                "from_line": 0,
                "has_more": false
            }
        }
    """
    try:
        from_line = request.args.get('from_line', 0, type=int)
        
        log_data = ReportManager.get_console_log(report_id, from_line=from_line)
        
        return jsonify({
            "success": True,
            "data": log_data
        })
        
    except Exception as e:
        logger.error(f"获取控制台日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/<report_id>/console-log/stream', methods=['GET'])
def stream_console_log(report_id: str):
    """
    获取完整的控制台日志（一次性获取全部）
    
    返回：
        {
            "success": true,
            "data": {
                "logs": [...],
                "count": 100
            }
        }
    """
    try:
        logs = ReportManager.get_console_log_stream(report_id)
        
        return jsonify({
            "success": True,
            "data": {
                "logs": logs,
                "count": len(logs)
            }
        })
        
    except Exception as e:
        logger.error(f"获取控制台日志失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Campaign Spend Visualization ==============

@report_bp.route('/campaign-spend', methods=['GET'])
def get_campaign_spend():
    """
    Campaign spend allocation data for treemap visualization.
    Returns mock GTM campaign data — works without LLM key.
    """
    campaigns = [
        {"name": "Zendesk Displacement Email", "channel": "Email", "spend": 45000, "budget": 50000},
        {"name": "LinkedIn Sponsored Content", "channel": "Paid Social", "spend": 38000, "budget": 40000},
        {"name": "AI Agent Launch Email", "channel": "Email", "spend": 32000, "budget": 35000},
        {"name": "Google Search — Competitor", "channel": "Search", "spend": 29000, "budget": 30000},
        {"name": "Enterprise Webinar Series", "channel": "Events", "spend": 25000, "budget": 28000},
        {"name": "LinkedIn InMail", "channel": "Paid Social", "spend": 22000, "budget": 25000},
        {"name": "Content SEO Program", "channel": "Content", "spend": 18000, "budget": 20000},
        {"name": "Google Display Retargeting", "channel": "Search", "spend": 15000, "budget": 18000},
        {"name": "SDR Direct Outreach", "channel": "Outbound", "spend": 12000, "budget": 15000},
    ]

    total_spend = sum(c["spend"] for c in campaigns)
    total_budget = sum(c["budget"] for c in campaigns)

    channels = {}
    for c in campaigns:
        ch = c["channel"]
        if ch not in channels:
            channels[ch] = {"budget": 0, "spend": 0}
        channels[ch]["budget"] += c["budget"]
        channels[ch]["spend"] += c["spend"]

    return jsonify({
        "success": True,
        "data": {
            "total_budget": total_budget,
            "total_spend": total_spend,
            "campaigns": campaigns,
            "channels": channels,
        }
    })


# ============== 报告模板接口 ==============

@report_bp.route('/templates', methods=['GET'])
def list_report_templates():
    """List all available report templates."""
    return jsonify({
        "success": True,
        "data": list_templates()
    })


@report_bp.route('/templates/<template_id>', methods=['GET'])
def get_report_template(template_id: str):
    """Get a specific report template with full section definitions."""
    template = get_template_dict(template_id)
    if not template:
        return jsonify({
            "success": False,
            "error": f"Template not found: {template_id}"
        }), 404

    return jsonify({
        "success": True,
        "data": template
    })


# ============== Report Sharing ==============

@report_bp.route('/<report_id>/share', methods=['POST'])
def create_share_link(report_id: str):
    """Create a shareable link for a report."""
    try:
        share_info = ReportManager.create_share(report_id)
        if not share_info:
            return jsonify({"success": False, "error": "Report not found"}), 404

        return jsonify({"success": True, "data": share_info})
    except Exception as e:
        logger.error(f"Failed to create share link: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/share', methods=['GET'])
def get_share_link(report_id: str):
    """Get current share info for a report."""
    try:
        share_info = ReportManager.get_share(report_id)
        return jsonify({
            "success": True,
            "data": share_info,
            "is_shared": share_info is not None,
        })
    except Exception as e:
        logger.error(f"Failed to get share info: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/<report_id>/share', methods=['DELETE'])
def revoke_share_link(report_id: str):
    """Revoke the share link for a report."""
    try:
        revoked = ReportManager.revoke_share(report_id)
        if not revoked:
            return jsonify({"success": False, "error": "No active share link"}), 404

        return jsonify({"success": True, "message": "Share link revoked"})
    except Exception as e:
        logger.error(f"Failed to revoke share link: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/shared/<token>', methods=['GET'])
def get_shared_report(token: str):
    """
    Public endpoint: access a report via share token.
    Returns report sections for read-only viewing.
    """
    try:
        report = ReportManager.get_report_by_share_token(token)
        if not report:
            return jsonify({"success": False, "error": "Invalid or expired share link"}), 404

        if report.status != ReportStatus.COMPLETED:
            return jsonify({"success": False, "error": "Report is not yet complete"}), 400

        sections = ReportManager.get_generated_sections(report.report_id)

        return jsonify({
            "success": True,
            "data": {
                "report_id": report.report_id,
                "sections": sections,
                "total_sections": len(sections),
                "created_at": report.created_at,
                "completed_at": report.completed_at,
            },
        })
    except Exception as e:
        logger.error(f"Failed to access shared report: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============== 工具调用接口（供调试使用）==============

@report_bp.route('/tools/search', methods=['POST'])
def search_graph_tool():
    """
    图谱搜索工具接口（供调试使用）
    
    请求（JSON）：
        {
            "graph_id": "mirofish_xxxx",
            "query": "搜索查询",
            "limit": 10
        }
    """
    try:
        data = request.get_json() or {}
        
        graph_id = data.get('graph_id')
        query = data.get('query')
        limit = data.get('limit', 10)
        
        if not graph_id or not query:
            return jsonify({
                "success": False,
                "error": "请提供 graph_id 和 query"
            }), 400
        
        from ..services.zep_tools import ZepToolsService
        
        tools = ZepToolsService()
        result = tools.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "data": result.to_dict()
        })
        
    except Exception as e:
        logger.error(f"图谱搜索失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@report_bp.route('/tools/statistics', methods=['POST'])
def get_graph_statistics_tool():
    """
    图谱统计工具接口（供调试使用）
    
    请求（JSON）：
        {
            "graph_id": "mirofish_xxxx"
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
        
        from ..services.zep_tools import ZepToolsService
        
        tools = ZepToolsService()
        result = tools.get_graph_statistics(graph_id)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"获取图谱统计失败: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


# ============== Data Source Connector Endpoints ==============

@report_bp.route('/data-sources', methods=['GET'])
def list_data_sources():
    """
    List available report data source types.

    Returns:
        {
            "success": true,
            "data": [
                {
                    "id": "simulation",
                    "name": "Simulation Results",
                    "description": "...",
                    "category": "internal",
                    "icon": "simulation",
                    "connected": true
                },
                ...
            ]
        }
    """
    try:
        sources = DataSourceService.list_sources()
        return jsonify({"success": True, "data": sources})
    except Exception as e:
        logger.error(f"Failed to list data sources: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@report_bp.route('/data-sources/<source_type>/preview', methods=['GET'])
def preview_data_source(source_type: str):
    """
    Get preview data for a data source type.

    Query params:
        simulation_id: required when source_type is "simulation"

    Returns:
        {
            "success": true,
            "data": {
                "source_type": "simulation",
                "is_mock": false,
                "metrics": [...],
                "sample_rows": [...]
            }
        }
    """
    try:
        source = DataSourceService.get_source(source_type)
        if not source:
            return jsonify({
                "success": False,
                "error": f"Unknown data source type: {source_type}"
            }), 404

        simulation_id = request.args.get('simulation_id')
        preview = DataSourceService.get_preview(source_type, simulation_id=simulation_id)

        return jsonify({"success": True, "data": preview})
    except Exception as e:
        logger.error(f"Failed to get data source preview: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
