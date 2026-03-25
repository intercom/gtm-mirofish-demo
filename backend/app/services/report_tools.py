"""
ReportAgent GTM Tool Definitions

Defines tools available to the ReportAgent for GTM simulation data analysis.
Each tool has two representations:
  1. OpenAI function-calling format (JSON Schema) for API compatibility
  2. Simplified format consumed by the existing ReACT prompt system

Tools:
  1. query_simulation_data   — Fetch simulation metrics (engagement, conversion, pipeline)
  2. analyze_sentiment_trend  — Compute sentiment statistics across agents over time
  3. identify_key_decisions   — Extract key decisions from simulation history
  4. compare_agent_behaviors  — Comparative analysis between agent personas
  5. generate_chart_data      — Prepare structured data for frontend chart rendering
  6. search_knowledge_graph   — Search Zep graph for relevant GTM information
  7. calculate_gtm_metrics    — Compute GTM-specific calculations (CAC, LTV, win rate, etc.)
"""

from typing import Dict, Any, List


# ═══════════════════════════════════════════════════════════════
# Tool Description Constants (injected into LLM prompt)
# ═══════════════════════════════════════════════════════════════

TOOL_DESC_QUERY_SIMULATION_DATA = """\
【模拟数据查询 - 获取仿真指标】
从GTM模拟中提取特定运营指标数据。支持按时间范围筛选，返回结构化的指标数值。

【支持的指标类型】
- engagement_rate: Agent互动率（点赞、评论、转发）
- response_rate: 外呼/触达的回复率
- conversion_rate: 漏斗各阶段转化率
- pipeline_velocity: 商机推进速度
- activity_volume: 各平台动作总量（发帖、评论等）
- agent_activity: 单个Agent的活跃度统计

【使用场景】
- 需要获取模拟中的硬指标数据
- 需要对比不同时间段的指标变化
- 需要用数据支撑报告中的结论

【返回内容】
- 指标名称和数值
- 按时间段的趋势数据点
- 相关统计摘要（均值、峰值、变化率）"""

TOOL_DESC_ANALYZE_SENTIMENT_TREND = """\
【情感趋势分析 - 追踪Agent态度变化】
分析模拟中Agent群体的情感倾向及其变化趋势。可聚焦特定Agent子集或分析全局情感走向。

【分析维度】
- 整体情感分布（正面/中性/负面）
- 情感随模拟轮次的变化曲线
- 不同Agent群体间的情感差异
- 情感转折点识别

【使用场景】
- 需要了解目标受众对GTM策略的态度
- 需要识别策略执行中的情感拐点
- 需要对比不同角色群体的反应差异

【返回内容】
- 情感分布统计（正面/中性/负面百分比）
- 按轮次的情感变化数据
- 关键情感转折事件
- 代表性正面和负面表述摘录"""

TOOL_DESC_IDENTIFY_KEY_DECISIONS = """\
【关键决策提取 - 识别模拟中的决策节点】
从模拟历史中提取关键决策点，包括Agent自主做出的决策和策略转折。

【识别范围】
- Agent主动发起的策略行动（如改变话术、调整频率）
- 群体行为的突变点（如集体响应或抵触）
- 平台间的行为迁移（从Twitter到Reddit或反之）
- 模拟参数触发的事件

【使用场景】
- 需要还原模拟中"发生了什么"的关键时刻
- 需要识别策略成功或失败的转折点
- 需要为报告提供叙事主线

【返回内容】
- 决策事件列表（时间、Agent、行动、影响）
- 决策的上下文背景
- 决策导致的后续连锁反应"""

TOOL_DESC_COMPARE_AGENT_BEHAVIORS = """\
【Agent行为对比 - 多角色比较分析】
在模拟中对比不同Agent的行为模式，揭示角色差异和群体动态。

【对比维度】
- 活跃度对比（发帖频率、互动频率）
- 内容策略对比（话题偏好、语气风格）
- 影响力对比（被互动次数、传播范围）
- 跨平台行为差异（同一Agent在Twitter vs Reddit）

【使用场景】
- 需要对比不同客户角色（如Enterprise vs SMB）的反应
- 需要分析竞争对手Agent vs 目标客户Agent的行为差异
- 需要识别最有价值的Agent群体

【返回内容】
- 多维度对比矩阵
- 每组Agent的行为特征摘要
- 显著差异和相似性分析"""

TOOL_DESC_GENERATE_CHART_DATA = """\
【图表数据生成 - 为可视化准备结构化数据】
根据指定的图表类型和数据查询，从模拟结果中提取并格式化适合前端渲染的数据。

【支持的图表类型】
- line: 折线图（趋势变化，如指标随时间变化）
- bar: 柱状图（类别对比，如各Agent群体的指标对比）
- pie: 饼图（占比分布，如情感分布、行动类型分布）
- scatter: 散点图（相关性分析，如活跃度与影响力的关系）
- heatmap: 热力图（时间×Agent的活跃度矩阵）
- funnel: 漏斗图（GTM漏斗各阶段转化）

【使用场景】
- 需要在报告中插入可视化图表
- 需要将复杂数据转化为直观展示
- 需要对比多个维度的数据

【返回内容】
- chart_type: 图表类型
- labels: 数据标签列表
- datasets: 数据集列表（含label、data、color）
- options: 图表配置建议（标题、坐标轴等）"""

TOOL_DESC_SEARCH_KNOWLEDGE_GRAPH = """\
【知识图谱检索 - 搜索Zep图谱中的GTM信息】
在Zep知识图谱中执行语义搜索，检索与查询相关的实体、关系和事实。
这是对底层图谱数据的直接检索，适合查找具体的实体信息和关系链。

【使用场景】
- 需要查找特定实体（人物、公司、产品）的信息
- 需要了解实体间的关系（如客户与产品的关联）
- 需要检索模拟中注入的种子数据和背景知识

【返回内容】
- 匹配的事实列表
- 相关实体信息
- 实体间的关系描述"""

TOOL_DESC_CALCULATE_GTM_METRICS = """\
【GTM指标计算 - 专业营销运营指标】
计算GTM（Go-To-Market）领域的专业指标，基于模拟数据进行量化分析。

【支持的指标】
- cac: 客户获取成本（Customer Acquisition Cost）
- ltv: 客户终身价值（Lifetime Value）
- ltv_cac_ratio: LTV/CAC比率
- win_rate: 商机赢单率
- pipeline_coverage: 管线覆盖率
- conversion_rate: 指定漏斗阶段的转化率
- time_to_close: 平均成交周期
- engagement_score: 综合互动评分
- channel_effectiveness: 渠道效果对比
- outreach_efficiency: 外呼效率（触达/回复/转化）

【使用场景】
- 需要用专业GTM指标评估模拟效果
- 需要对比不同策略的ROI
- 需要为管理层提供业务导向的数据

【返回内容】
- 计算后的指标数值
- 计算公式和输入参数
- 行业基准对比（如适用）
- 指标含义说明"""


# ═══════════════════════════════════════════════════════════════
# OpenAI Function-Calling Format Schemas
# ═══════════════════════════════════════════════════════════════

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "query_simulation_data",
            "description": "Fetch specific simulation metrics by name and optional time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "simulation_id": {
                        "type": "string",
                        "description": "The simulation ID to query data from."
                    },
                    "metric": {
                        "type": "string",
                        "enum": [
                            "engagement_rate",
                            "response_rate",
                            "conversion_rate",
                            "pipeline_velocity",
                            "activity_volume",
                            "agent_activity",
                        ],
                        "description": "The metric to retrieve."
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["all", "first_half", "second_half", "last_3_rounds", "last_5_rounds"],
                        "description": "Time range filter. Defaults to 'all'."
                    },
                },
                "required": ["simulation_id", "metric"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_sentiment_trend",
            "description": "Compute sentiment statistics for agents in a simulation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "simulation_id": {
                        "type": "string",
                        "description": "The simulation ID to analyze."
                    },
                    "agent_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Optional list of agent IDs to focus on. Analyzes all agents if omitted."
                    },
                },
                "required": ["simulation_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "identify_key_decisions",
            "description": "Extract key decision points and turning moments from simulation history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "simulation_id": {
                        "type": "string",
                        "description": "The simulation ID to analyze."
                    },
                },
                "required": ["simulation_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_agent_behaviors",
            "description": "Comparative analysis of behaviors between specified agents or agent groups.",
            "parameters": {
                "type": "object",
                "properties": {
                    "simulation_id": {
                        "type": "string",
                        "description": "The simulation ID to analyze."
                    },
                    "agent_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of agent IDs to compare. Must include at least 2."
                    },
                },
                "required": ["simulation_id", "agent_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_chart_data",
            "description": "Prepare structured data for a specific chart type from simulation results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chart_type": {
                        "type": "string",
                        "enum": ["line", "bar", "pie", "scatter", "heatmap", "funnel"],
                        "description": "The type of chart to generate data for."
                    },
                    "data_query": {
                        "type": "string",
                        "description": "Natural language description of what data to chart (e.g., 'engagement rate over time by agent group')."
                    },
                },
                "required": ["chart_type", "data_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_graph",
            "description": "Search the Zep knowledge graph for entities, relationships, and facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query for the knowledge graph."
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_gtm_metrics",
            "description": "Compute GTM-specific business metrics from simulation data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "enum": [
                            "cac",
                            "ltv",
                            "ltv_cac_ratio",
                            "win_rate",
                            "pipeline_coverage",
                            "conversion_rate",
                            "time_to_close",
                            "engagement_score",
                            "channel_effectiveness",
                            "outreach_efficiency",
                        ],
                        "description": "The GTM metric to calculate."
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Metric-specific parameters (e.g., {'funnel_stage': 'mql_to_sql'} for conversion_rate).",
                        "additionalProperties": True,
                    },
                },
                "required": ["metric_name"],
            },
        },
    },
]


# ═══════════════════════════════════════════════════════════════
# Simplified Format (for existing ReACT prompt system)
# ═══════════════════════════════════════════════════════════════

def get_report_tool_definitions() -> Dict[str, Dict[str, Any]]:
    """
    Return tool definitions in the simplified format used by
    ReportAgent._define_tools() and _get_tools_description().

    Format per tool:
        {
            "name": str,
            "description": str,          # Chinese description constant
            "parameters": {param: desc}   # param name -> human-readable description
        }
    """
    return {
        "query_simulation_data": {
            "name": "query_simulation_data",
            "description": TOOL_DESC_QUERY_SIMULATION_DATA,
            "parameters": {
                "metric": "要查询的指标名称（engagement_rate / response_rate / conversion_rate / pipeline_velocity / activity_volume / agent_activity）",
                "time_range": "时间范围（all / first_half / second_half / last_3_rounds / last_5_rounds），默认 all",
            },
        },
        "analyze_sentiment_trend": {
            "name": "analyze_sentiment_trend",
            "description": TOOL_DESC_ANALYZE_SENTIMENT_TREND,
            "parameters": {
                "agent_ids": "要分析的Agent ID列表（可选，不填则分析全部Agent）",
            },
        },
        "identify_key_decisions": {
            "name": "identify_key_decisions",
            "description": TOOL_DESC_IDENTIFY_KEY_DECISIONS,
            "parameters": {},
        },
        "compare_agent_behaviors": {
            "name": "compare_agent_behaviors",
            "description": TOOL_DESC_COMPARE_AGENT_BEHAVIORS,
            "parameters": {
                "agent_ids": "要对比的Agent ID列表（至少2个）",
            },
        },
        "generate_chart_data": {
            "name": "generate_chart_data",
            "description": TOOL_DESC_GENERATE_CHART_DATA,
            "parameters": {
                "chart_type": "图表类型（line / bar / pie / scatter / heatmap / funnel）",
                "data_query": "数据查询描述，用自然语言说明需要什么数据（如：'各Agent群体的互动率趋势'）",
            },
        },
        "search_knowledge_graph": {
            "name": "search_knowledge_graph",
            "description": TOOL_DESC_SEARCH_KNOWLEDGE_GRAPH,
            "parameters": {
                "query": "语义搜索查询字符串",
            },
        },
        "calculate_gtm_metrics": {
            "name": "calculate_gtm_metrics",
            "description": TOOL_DESC_CALCULATE_GTM_METRICS,
            "parameters": {
                "metric_name": "GTM指标名称（cac / ltv / ltv_cac_ratio / win_rate / pipeline_coverage / conversion_rate / time_to_close / engagement_score / channel_effectiveness / outreach_efficiency）",
                "parameters": "指标专用参数（可选，JSON对象，如 {\"funnel_stage\": \"mql_to_sql\"}）",
            },
        },
    }


def get_openai_tool_schemas() -> List[Dict[str, Any]]:
    """
    Return tool definitions in OpenAI function-calling format.
    Suitable for passing to the OpenAI API's `tools` parameter.
    """
    return TOOL_SCHEMAS


# Names of all GTM report tools, for validation in tool-call parsing
VALID_GTM_TOOL_NAMES = frozenset(
    schema["function"]["name"] for schema in TOOL_SCHEMAS
)
