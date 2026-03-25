"""
Parameter Sensitivity Analyzer

Analyzes how individual parameters affect simulation outcomes by running
parameter sweeps and computing impact scores. Uses deterministic mock
data when no real simulation backend is available.
"""

import hashlib
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..utils.logger import get_logger
from .whatif_engine import (
    OUTCOME_METRICS,
    SUPPORTED_PARAMETERS,
    _compute_mock_outcomes,
    _seed_rng,
)

logger = get_logger('mirofish.sensitivity')

# In-memory store for sensitivity results
_sensitivity_results: Dict[str, Dict[str, Any]] = {}


class SensitivityAnalyzer:
    """Analyzes which simulation parameters most affect outcomes."""

    @staticmethod
    def run_sensitivity(
        base_simulation_id: str,
        parameter: str,
        min_value: float,
        max_value: float,
        steps: int = 5,
    ) -> Dict[str, Any]:
        """Run a parameter sweep and return sensitivity data.

        Generates `steps` evenly-spaced values between min_value and max_value,
        computes mock outcomes for each, and returns the full sweep results.
        """
        if parameter not in SUPPORTED_PARAMETERS:
            raise ValueError(
                f"Unknown parameter '{parameter}'. "
                f"Supported: {list(SUPPORTED_PARAMETERS.keys())}"
            )

        steps = max(2, min(steps, 20))

        step_size = (max_value - min_value) / (steps - 1) if steps > 1 else 0
        sweep_values = [round(min_value + i * step_size, 4) for i in range(steps)]

        base_rng = _seed_rng(base_simulation_id, 'base')
        base_outcomes = _compute_mock_outcomes(base_rng, [])

        sweep_results = []
        for val in sweep_values:
            rng = _seed_rng(base_simulation_id, parameter, val)
            modifications = [{'parameter': parameter, 'value': val}]
            outcomes = _compute_mock_outcomes(rng, modifications)

            deltas = {}
            for metric in OUTCOME_METRICS:
                base_val = base_outcomes[metric]
                if base_val != 0:
                    deltas[metric] = round(
                        (outcomes[metric] - base_val) / abs(base_val) * 100, 2
                    )
                else:
                    deltas[metric] = 0.0

            sweep_results.append({
                'value': val,
                'outcomes': outcomes,
                'deltas': deltas,
            })

        sensitivity_scores = {}
        for metric in OUTCOME_METRICS:
            values = [r['outcomes'][metric] for r in sweep_results]
            if values:
                spread = max(values) - min(values)
                base_val = base_outcomes[metric]
                if base_val != 0:
                    sensitivity_scores[metric] = round(spread / abs(base_val), 4)
                else:
                    sensitivity_scores[metric] = round(spread, 4)

        result_id = f"sens_{base_simulation_id}_{parameter}"
        result = {
            'result_id': result_id,
            'base_simulation_id': base_simulation_id,
            'parameter': parameter,
            'parameter_info': SUPPORTED_PARAMETERS[parameter],
            'min_value': min_value,
            'max_value': max_value,
            'steps': steps,
            'base_outcomes': base_outcomes,
            'sweep_results': sweep_results,
            'sensitivity_scores': sensitivity_scores,
            'created_at': datetime.now().isoformat(),
        }

        _sensitivity_results[result_id] = result
        logger.info(
            f"Sensitivity analysis for {parameter} on {base_simulation_id}: "
            f"{steps} steps [{min_value} → {max_value}]"
        )
        return result

    @staticmethod
    def get_sensitivity(base_simulation_id: str) -> List[Dict[str, Any]]:
        """Get all sensitivity results for a base simulation."""
        prefix = f"sens_{base_simulation_id}_"
        return [
            v for k, v in _sensitivity_results.items()
            if k.startswith(prefix)
        ]

    @staticmethod
    def generate_tornado_data(
        base_simulation_id: str,
        parameters: Optional[List[str]] = None,
        target_metric: str = 'consensus_score',
    ) -> Dict[str, Any]:
        """Generate tornado chart data showing best/worst case per parameter.

        For each parameter, tests its min and max values and records the
        impact on the target metric.
        """
        if target_metric not in OUTCOME_METRICS:
            raise ValueError(
                f"Unknown metric '{target_metric}'. "
                f"Supported: {OUTCOME_METRICS}"
            )

        if parameters is None:
            parameters = list(SUPPORTED_PARAMETERS.keys())
        else:
            parameters = [p for p in parameters if p in SUPPORTED_PARAMETERS]

        base_rng = _seed_rng(base_simulation_id, 'base')
        base_outcomes = _compute_mock_outcomes(base_rng, [])
        base_value = base_outcomes[target_metric]

        bars = []
        for param in parameters:
            info = SUPPORTED_PARAMETERS[param]
            low_val = info['min']
            high_val = info['max']

            low_rng = _seed_rng(base_simulation_id, param, low_val)
            low_outcomes = _compute_mock_outcomes(
                low_rng, [{'parameter': param, 'value': low_val}]
            )

            high_rng = _seed_rng(base_simulation_id, param, high_val)
            high_outcomes = _compute_mock_outcomes(
                high_rng, [{'parameter': param, 'value': high_val}]
            )

            low_impact = round(low_outcomes[target_metric] - base_value, 4)
            high_impact = round(high_outcomes[target_metric] - base_value, 4)

            bars.append({
                'parameter': param,
                'parameter_label': param.replace('_', ' ').title(),
                'low_value': low_val,
                'high_value': high_val,
                'low_impact': low_impact,
                'high_impact': high_impact,
                'total_range': round(abs(high_impact - low_impact), 4),
            })

        bars.sort(key=lambda b: b['total_range'], reverse=True)

        return {
            'base_simulation_id': base_simulation_id,
            'target_metric': target_metric,
            'base_value': base_value,
            'bars': bars,
            'parameters_analyzed': len(bars),
            'created_at': datetime.now().isoformat(),
        }
