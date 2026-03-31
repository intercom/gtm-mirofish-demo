"""
Startup diagnostics — pre-flight checks before the server accepts requests.

Checks Python version, required packages, env vars, data directories,
external service reachability, port availability, and disk space.
Logs results and determines operating mode: full / partial / demo.
"""

import importlib
import logging
import os
import platform
import shutil
import socket
import sys

from ..config import Config, LLM_PROVIDERS

logger = logging.getLogger("mirofish.diagnostics")

REQUIRED_PACKAGES = [
    "flask",
    "flask_cors",
    "openai",
    "dotenv",
]

OPTIONAL_PACKAGES = [
    ("anthropic", "Anthropic LLM provider"),
    ("zep_cloud", "Zep Cloud knowledge graph memory"),
    ("google.generativeai", "Gemini LLM provider"),
]

DATA_DIRS = [
    "data/simulations",
    "data/dashboards",
    "data/templates",
    "data/reports",
]

MIN_PYTHON = (3, 10)
MIN_DISK_MB = 100


class DiagnosticResult:
    """Collects pass / warn / fail results from each check."""

    def __init__(self):
        self.passed: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add_pass(self, msg: str):
        self.passed.append(msg)

    def add_warn(self, msg: str):
        self.warnings.append(msg)

    def add_error(self, msg: str):
        self.errors.append(msg)


def _check_python_version(result: DiagnosticResult):
    v = sys.version_info
    label = f"Python {v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= MIN_PYTHON:
        result.add_pass(label)
    else:
        result.add_error(
            f"{label} — Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required"
        )


def _check_required_packages(result: DiagnosticResult):
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            result.add_pass(f"Package '{pkg}' installed")
        except ImportError:
            result.add_error(f"Required package '{pkg}' is missing — pip install -r requirements.txt")


def _check_optional_packages(result: DiagnosticResult):
    for pkg, description in OPTIONAL_PACKAGES:
        try:
            importlib.import_module(pkg)
            result.add_pass(f"Package '{pkg}' installed ({description})")
        except ImportError:
            result.add_warn(f"Optional package '{pkg}' not installed — {description} unavailable")


def _check_env_vars(result: DiagnosticResult):
    provider = os.environ.get("LLM_PROVIDER", "").lower()
    api_key = os.environ.get("LLM_API_KEY", "")
    zep_key = os.environ.get("ZEP_API_KEY", "")

    if provider and provider in LLM_PROVIDERS:
        result.add_pass(f"LLM_PROVIDER={provider}")
    elif provider:
        result.add_warn(
            f"LLM_PROVIDER='{provider}' is not a known provider "
            f"(expected: {', '.join(LLM_PROVIDERS)})"
        )
    else:
        result.add_warn("LLM_PROVIDER not set — using default OpenAI-compatible config")

    if api_key:
        result.add_pass("LLM_API_KEY configured")
    else:
        result.add_warn("LLM_API_KEY not set — LLM features will use fallback mode")

    if provider and not api_key:
        result.add_warn(
            f"LLM_PROVIDER is '{provider}' but LLM_API_KEY is missing — "
            "set LLM_API_KEY or remove LLM_PROVIDER"
        )

    if zep_key:
        result.add_pass("ZEP_API_KEY configured")
    else:
        result.add_warn("ZEP_API_KEY not set — knowledge graph memory unavailable")


def _check_data_dirs(result: DiagnosticResult):
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for rel in DATA_DIRS:
        path = os.path.join(backend_root, rel)
        if os.path.isdir(path):
            result.add_pass(f"Directory exists: {rel}")
        else:
            try:
                os.makedirs(path, exist_ok=True)
                result.add_pass(f"Directory created: {rel}")
            except OSError as exc:
                result.add_warn(f"Could not create {rel}: {exc}")


def _check_llm_reachable(result: DiagnosticResult):
    if not Config.LLM_API_KEY:
        return
    provider = os.environ.get("LLM_PROVIDER", "").lower()
    host_map = {
        "anthropic": "api.anthropic.com",
        "openai": "api.openai.com",
        "gemini": "generativelanguage.googleapis.com",
    }
    host = host_map.get(provider)
    if not host:
        return
    try:
        socket.create_connection((host, 443), timeout=5).close()
        result.add_pass(f"LLM endpoint reachable ({host})")
    except OSError:
        result.add_warn(f"Cannot reach LLM endpoint ({host}) — network issue or firewall")


def _check_zep_reachable(result: DiagnosticResult):
    if not Config.ZEP_API_KEY:
        return
    try:
        socket.create_connection(("api.getzep.com", 443), timeout=5).close()
        result.add_pass("Zep Cloud reachable (api.getzep.com)")
    except OSError:
        result.add_warn("Cannot reach Zep Cloud (api.getzep.com) — network issue or firewall")


def _check_port_available(result: DiagnosticResult):
    port = int(os.environ.get("FLASK_PORT", os.environ.get("BACKEND_PORT", 5001)))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
        result.add_pass(f"Port {port} available")
    except OSError:
        result.add_warn(f"Port {port} already in use — server may fail to bind")


def _check_disk_space(result: DiagnosticResult):
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    usage = shutil.disk_usage(backend_root)
    free_mb = usage.free // (1024 * 1024)
    if free_mb >= MIN_DISK_MB:
        result.add_pass(f"Disk space: {free_mb} MB free")
    else:
        result.add_error(f"Low disk space: {free_mb} MB free (minimum {MIN_DISK_MB} MB)")


def _determine_mode() -> str:
    """Return 'full', 'partial', or 'demo' based on configured services."""
    has_llm = bool(Config.LLM_API_KEY)
    has_zep = bool(Config.ZEP_API_KEY)
    if has_llm and has_zep:
        return "full"
    if has_llm or has_zep:
        return "partial"
    return "demo"


def run_diagnostics() -> DiagnosticResult:
    """Run all startup diagnostics and log a summary.

    Returns the DiagnosticResult so callers can inspect errors.
    """
    result = DiagnosticResult()

    logger.info("Running startup diagnostics...")

    _check_python_version(result)
    _check_required_packages(result)
    _check_optional_packages(result)
    _check_env_vars(result)
    _check_data_dirs(result)
    _check_llm_reachable(result)
    _check_zep_reachable(result)
    _check_port_available(result)
    _check_disk_space(result)

    # Log individual results
    for msg in result.passed:
        logger.info(f"  [PASS] {msg}")
    for msg in result.warnings:
        logger.warning(f"  [WARN] {msg}")
    for msg in result.errors:
        logger.error(f"  [FAIL] {msg}")

    # Summary
    mode = _determine_mode()
    summary = (
        f"MiroFish GTM Demo starting in [{mode}] mode  "
        f"({len(result.passed)} passed, {len(result.warnings)} warnings, "
        f"{len(result.errors)} errors)  "
        f"[{platform.system()} {platform.release()}, Python {platform.python_version()}]"
    )

    if result.errors:
        logger.error(summary)
    elif result.warnings:
        logger.warning(summary)
    else:
        logger.info(summary)

    return result
