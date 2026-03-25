"""
LLM Insight Generation Service

Generates structured insights from GTM data using LLM when available,
with template-based fallback for demo/mock mode.
"""

import time
import threading
from dataclasses import dataclass, asdict
from enum import Enum
from typing import List, Optional, Dict, Any

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.insights')


class InsightType(str, Enum):
    TREND = "trend"
    ANOMALY = "anomaly"
    RECOMMENDATION = "recommendation"
    COMPARISON = "comparison"


SUPPORTED_DATA_TYPES = ["revenue", "pipeline", "simulation_results", "campaign", "reconciliation"]


@dataclass
class Insight:
    title: str
    description: str
    evidence: str
    confidence: float
    insight_type: str
    data_type: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class _RateLimiter:
    """Sliding-window rate limiter: max `limit` calls per `window` seconds."""

    def __init__(self, limit: int = 5, window: int = 60):
        self._limit = limit
        self._window = window
        self._timestamps: List[float] = []
        self._lock = threading.Lock()

    def allow(self) -> bool:
        now = time.time()
        with self._lock:
            self._timestamps = [t for t in self._timestamps if now - t < self._window]
            if len(self._timestamps) >= self._limit:
                return False
            self._timestamps.append(now)
            return True


class InsightGenerator:
    """Generates structured insights from GTM data.

    Uses LLM when an API key is configured; falls back to
    deterministic template rules otherwise (demo/mock mode).
    """

    _rate_limiter = _RateLimiter(limit=5, window=60)

    def generate_insights(
        self,
        data_type: str,
        data: Dict[str, Any],
        limit: int = 5,
    ) -> List[Insight]:
        if data_type not in SUPPORTED_DATA_TYPES:
            raise ValueError(f"Unsupported data_type: {data_type}. Must be one of {SUPPORTED_DATA_TYPES}")

        if not self._rate_limiter.allow():
            raise RateLimitError("Rate limit exceeded: max 5 insight requests per minute")

        if Config.LLM_API_KEY:
            try:
                return self._generate_with_llm(data_type, data, limit)
            except Exception as e:
                logger.warning(f"LLM insight generation failed, falling back to templates: {e}")
                return self._generate_with_templates(data_type, data, limit)
        else:
            logger.info("No LLM_API_KEY configured — using template-based insights")
            return self._generate_with_templates(data_type, data, limit)

    # ------------------------------------------------------------------
    # LLM-powered generation
    # ------------------------------------------------------------------

    def _generate_with_llm(
        self,
        data_type: str,
        data: Dict[str, Any],
        limit: int,
    ) -> List[Insight]:
        from ..utils.llm_client import LLMClient

        client = LLMClient()
        prompt = self._build_prompt(data_type, data, limit)
        messages = [
            {"role": "system", "content": (
                "You are a GTM analytics expert. Analyze the provided data and return "
                "structured insights. Respond with a JSON object containing an \"insights\" "
                "array. Each insight must have: title (str), description (str), evidence (str), "
                "confidence (float 0-1), insight_type (one of: trend, anomaly, recommendation, comparison)."
            )},
            {"role": "user", "content": prompt},
        ]

        result = client.chat_json(messages=messages, temperature=0.4, max_tokens=2048)
        raw_insights = result.get("insights", [])

        insights: List[Insight] = []
        for item in raw_insights[:limit]:
            insight_type = item.get("insight_type", "trend")
            if insight_type not in [e.value for e in InsightType]:
                insight_type = "trend"
            insights.append(Insight(
                title=item.get("title", "Untitled Insight"),
                description=item.get("description", ""),
                evidence=item.get("evidence", ""),
                confidence=max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
                insight_type=insight_type,
                data_type=data_type,
            ))

        return insights

    def _build_prompt(self, data_type: str, data: Dict[str, Any], limit: int) -> str:
        import json
        return (
            f"Analyze the following {data_type} data and generate up to {limit} insights.\n"
            f"Look for: trends, anomalies, actionable recommendations, and comparisons.\n\n"
            f"Data:\n```json\n{json.dumps(data, indent=2, default=str)}\n```"
        )

    # ------------------------------------------------------------------
    # Template-based fallback (demo / mock mode)
    # ------------------------------------------------------------------

    def _generate_with_templates(
        self,
        data_type: str,
        data: Dict[str, Any],
        limit: int,
    ) -> List[Insight]:
        handler = self._template_handlers.get(data_type, self._generic_templates)
        return handler(self, data, data_type)[:limit]

    def _revenue_templates(self, data: Dict[str, Any], data_type: str) -> List[Insight]:
        insights: List[Insight] = []
        growth = data.get("growth_rate", data.get("growth", 0))
        total = data.get("total", data.get("revenue", 0))
        target = data.get("target", 0)

        if isinstance(growth, (int, float)) and growth > 10:
            insights.append(Insight(
                title="Strong revenue growth detected",
                description=f"Revenue is growing at {growth}%, significantly above typical benchmarks.",
                evidence=f"Current growth rate: {growth}%",
                confidence=0.85,
                insight_type=InsightType.TREND.value,
                data_type=data_type,
            ))
        elif isinstance(growth, (int, float)) and growth < -5:
            insights.append(Insight(
                title="Revenue decline requires attention",
                description=f"Revenue has declined by {abs(growth)}%. Investigate contributing factors.",
                evidence=f"Current growth rate: {growth}%",
                confidence=0.80,
                insight_type=InsightType.ANOMALY.value,
                data_type=data_type,
            ))

        if target and total and isinstance(total, (int, float)) and isinstance(target, (int, float)):
            pct = (total / target) * 100 if target else 0
            if pct >= 100:
                insights.append(Insight(
                    title="Revenue target exceeded",
                    description=f"Revenue has reached {pct:.0f}% of target.",
                    evidence=f"Total: {total}, Target: {target}",
                    confidence=0.95,
                    insight_type=InsightType.TREND.value,
                    data_type=data_type,
                ))
            elif pct < 70:
                insights.append(Insight(
                    title="Revenue significantly below target",
                    description=f"Revenue is only at {pct:.0f}% of target — consider pipeline acceleration.",
                    evidence=f"Total: {total}, Target: {target}",
                    confidence=0.80,
                    insight_type=InsightType.RECOMMENDATION.value,
                    data_type=data_type,
                ))

        if not insights:
            insights.append(self._default_insight(data_type))
        return insights

    def _pipeline_templates(self, data: Dict[str, Any], data_type: str) -> List[Insight]:
        insights: List[Insight] = []
        conversion = data.get("conversion_rate", data.get("conversion", 0))
        deals = data.get("total_deals", data.get("deals", 0))
        avg_deal = data.get("avg_deal_size", data.get("average_deal", 0))

        if isinstance(conversion, (int, float)) and conversion < 15:
            insights.append(Insight(
                title="Low pipeline conversion rate",
                description=f"Conversion rate of {conversion}% is below the 15% benchmark. Review qualification criteria.",
                evidence=f"Current conversion rate: {conversion}%",
                confidence=0.78,
                insight_type=InsightType.ANOMALY.value,
                data_type=data_type,
            ))

        if isinstance(deals, (int, float)) and deals > 0 and isinstance(avg_deal, (int, float)):
            insights.append(Insight(
                title="Pipeline composition summary",
                description=f"Pipeline contains {deals} deals with an average size of ${avg_deal:,.0f}.",
                evidence=f"Total deals: {deals}, Avg deal: ${avg_deal:,.0f}",
                confidence=0.90,
                insight_type=InsightType.COMPARISON.value,
                data_type=data_type,
            ))

        if not insights:
            insights.append(self._default_insight(data_type))
        return insights

    def _simulation_results_templates(self, data: Dict[str, Any], data_type: str) -> List[Insight]:
        insights: List[Insight] = []
        total_actions = data.get("total_actions", 0)
        rounds = data.get("rounds", data.get("total_rounds", 0))
        sentiment = data.get("sentiment", data.get("avg_sentiment", None))

        if isinstance(total_actions, (int, float)) and total_actions > 0:
            insights.append(Insight(
                title="Simulation activity summary",
                description=f"Simulation generated {total_actions} actions across {rounds} rounds.",
                evidence=f"Total actions: {total_actions}, Rounds: {rounds}",
                confidence=0.95,
                insight_type=InsightType.TREND.value,
                data_type=data_type,
            ))

        if sentiment is not None and isinstance(sentiment, (int, float)):
            label = "positive" if sentiment > 0.6 else "negative" if sentiment < 0.4 else "neutral"
            insights.append(Insight(
                title=f"Overall sentiment is {label}",
                description=f"Average sentiment score of {sentiment:.2f} indicates {label} reception.",
                evidence=f"Avg sentiment: {sentiment:.2f}",
                confidence=0.75,
                insight_type=InsightType.TREND.value,
                data_type=data_type,
            ))

        if not insights:
            insights.append(self._default_insight(data_type))
        return insights

    def _campaign_templates(self, data: Dict[str, Any], data_type: str) -> List[Insight]:
        insights: List[Insight] = []
        ctr = data.get("ctr", data.get("click_through_rate", 0))
        spend = data.get("spend", data.get("total_spend", 0))
        roas = data.get("roas", data.get("return_on_ad_spend", 0))

        if isinstance(ctr, (int, float)) and ctr > 3:
            insights.append(Insight(
                title="Above-average click-through rate",
                description=f"CTR of {ctr}% exceeds the 2% industry average — creative is resonating.",
                evidence=f"CTR: {ctr}%",
                confidence=0.82,
                insight_type=InsightType.TREND.value,
                data_type=data_type,
            ))

        if isinstance(roas, (int, float)) and roas < 1:
            insights.append(Insight(
                title="Campaign ROAS below break-even",
                description=f"ROAS of {roas:.1f}x is under 1x — consider pausing or optimizing spend.",
                evidence=f"ROAS: {roas:.1f}x, Spend: ${spend:,.0f}" if isinstance(spend, (int, float)) else f"ROAS: {roas:.1f}x",
                confidence=0.85,
                insight_type=InsightType.RECOMMENDATION.value,
                data_type=data_type,
            ))

        if not insights:
            insights.append(self._default_insight(data_type))
        return insights

    def _reconciliation_templates(self, data: Dict[str, Any], data_type: str) -> List[Insight]:
        insights: List[Insight] = []
        discrepancy = data.get("discrepancy", data.get("gap", 0))
        matched = data.get("matched_pct", data.get("match_rate", 0))

        if isinstance(matched, (int, float)) and matched < 90:
            insights.append(Insight(
                title="Low reconciliation match rate",
                description=f"Only {matched}% of records matched — investigate data quality.",
                evidence=f"Match rate: {matched}%",
                confidence=0.80,
                insight_type=InsightType.ANOMALY.value,
                data_type=data_type,
            ))

        if isinstance(discrepancy, (int, float)) and abs(discrepancy) > 0:
            insights.append(Insight(
                title="Reconciliation discrepancy found",
                description=f"A discrepancy of ${abs(discrepancy):,.0f} was detected between sources.",
                evidence=f"Discrepancy: ${discrepancy:,.0f}",
                confidence=0.88,
                insight_type=InsightType.ANOMALY.value,
                data_type=data_type,
            ))

        if not insights:
            insights.append(self._default_insight(data_type))
        return insights

    def _generic_templates(self, data: Dict[str, Any], data_type: str) -> List[Insight]:
        return [self._default_insight(data_type)]

    @staticmethod
    def _default_insight(data_type: str) -> Insight:
        return Insight(
            title=f"Data received for {data_type}",
            description=f"Data was provided for {data_type} analysis. Add more structured fields for richer insights.",
            evidence="Baseline observation",
            confidence=0.50,
            insight_type=InsightType.TREND.value,
            data_type=data_type,
        )

    _template_handlers = {
        "revenue": _revenue_templates,
        "pipeline": _pipeline_templates,
        "simulation_results": _simulation_results_templates,
        "campaign": _campaign_templates,
        "reconciliation": _reconciliation_templates,
    }


class RateLimitError(Exception):
    pass
