"""
Backend health monitoring service.
Tracks request count, error count, avg response time, active connections,
and memory usage. Resets metrics hourly with 24h snapshot retention.
"""

import time
import threading
import psutil
from datetime import datetime, timezone
from typing import Dict, Any, List

from ..utils.logger import get_logger

logger = get_logger('mirofish.health')


class HealthMonitor:
    """Singleton health monitor with thread-safe counters."""

    _instance = None
    _lock = threading.Lock()

    # Alert thresholds
    ERROR_RATE_THRESHOLD = 0.05      # 5%
    AVG_RESPONSE_TIME_THRESHOLD = 2.0  # 2 seconds
    MEMORY_THRESHOLD = 0.80          # 80%
    MAX_SNAPSHOTS = 24               # keep last 24 hourly snapshots

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._metrics_lock = threading.Lock()
        self._reset_metrics()
        self._snapshots: List[Dict[str, Any]] = []
        self._hour_start = self._current_hour()

    def _current_hour(self) -> str:
        return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:00:00Z')

    def _reset_metrics(self):
        self._request_count = 0
        self._error_count = 0
        self._total_response_time = 0.0
        self._active_connections = 0

    def _maybe_rotate(self):
        """Rotate metrics into a snapshot if the hour changed."""
        current_hour = self._current_hour()
        if current_hour != self._hour_start:
            snapshot = self._build_snapshot()
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self.MAX_SNAPSHOTS:
                self._snapshots = self._snapshots[-self.MAX_SNAPSHOTS:]
            self._reset_metrics()
            self._hour_start = current_hour

    def _build_snapshot(self) -> Dict[str, Any]:
        error_rate = (self._error_count / self._request_count) if self._request_count else 0.0
        avg_response = (self._total_response_time / self._request_count) if self._request_count else 0.0
        return {
            'hour': self._hour_start,
            'request_count': self._request_count,
            'error_count': self._error_count,
            'error_rate': round(error_rate, 4),
            'avg_response_time': round(avg_response, 4),
        }

    # -- Request lifecycle hooks --

    def on_request_start(self):
        with self._metrics_lock:
            self._maybe_rotate()
            self._active_connections += 1

    def on_request_end(self, duration: float, is_error: bool):
        with self._metrics_lock:
            self._active_connections = max(0, self._active_connections - 1)
            self._request_count += 1
            self._total_response_time += duration
            if is_error:
                self._error_count += 1

    # -- Alerting --

    def _check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        alerts = []
        if metrics['error_rate'] > self.ERROR_RATE_THRESHOLD:
            msg = f"Error rate {metrics['error_rate']:.1%} exceeds {self.ERROR_RATE_THRESHOLD:.0%} threshold"
            alerts.append({'level': 'warning', 'message': msg})
            logger.warning(msg)
        if metrics['avg_response_time'] > self.AVG_RESPONSE_TIME_THRESHOLD:
            msg = f"Avg response time {metrics['avg_response_time']:.3f}s exceeds {self.AVG_RESPONSE_TIME_THRESHOLD}s threshold"
            alerts.append({'level': 'warning', 'message': msg})
            logger.warning(msg)
        if metrics['memory_usage_percent'] > self.MEMORY_THRESHOLD * 100:
            msg = f"Memory usage {metrics['memory_usage_percent']:.1f}% exceeds {self.MEMORY_THRESHOLD:.0%} threshold"
            alerts.append({'level': 'warning', 'message': msg})
            logger.warning(msg)
        return alerts

    # -- Public API --

    def get_metrics(self) -> Dict[str, Any]:
        """Return current metrics, alerts, and recent hourly snapshots."""
        with self._metrics_lock:
            self._maybe_rotate()

            request_count = self._request_count
            error_count = self._error_count
            error_rate = (error_count / request_count) if request_count else 0.0
            avg_response = (self._total_response_time / request_count) if request_count else 0.0
            active_connections = self._active_connections

        process = psutil.Process()
        mem_info = process.memory_info()
        system_mem = psutil.virtual_memory()

        metrics = {
            'request_count': request_count,
            'error_count': error_count,
            'error_rate': round(error_rate, 4),
            'avg_response_time': round(avg_response, 4),
            'active_connections': active_connections,
            'memory_usage_mb': round(mem_info.rss / (1024 * 1024), 2),
            'memory_usage_percent': round(system_mem.percent, 2),
            'uptime_seconds': round(time.time() - _start_time, 1),
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

        alerts = self._check_alerts(metrics)

        return {
            'status': 'degraded' if alerts else 'healthy',
            'metrics': metrics,
            'alerts': alerts,
            'hourly_snapshots': list(self._snapshots),
        }


# Module-level singleton and process start time
_start_time = time.time()
health_monitor = HealthMonitor()
