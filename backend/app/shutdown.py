"""
Graceful shutdown coordination.

Provides a shared shutdown event that signals the application is terminating.
Used by the health endpoint to return 503 during shutdown (load balancer draining)
and by cleanup handlers to coordinate orderly teardown.
"""

import threading
import logging

logger = logging.getLogger('mirofish.shutdown')

_shutdown_event = threading.Event()


def is_shutting_down():
    return _shutdown_event.is_set()


def begin_shutdown():
    if not _shutdown_event.is_set():
        logger.info("Shutdown initiated — health endpoint will return 503")
        _shutdown_event.set()
