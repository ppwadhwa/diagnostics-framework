from diagnostics_framework.registry import register_system, register_test, register_plot, register_report, registry
from diagnostics_framework.models import DiagnosticResult, DiagnosticStatus, DiagnosticSummary
from diagnostics_framework.runner import run_diagnostics, generate_plot, generate_report

# Auto-discover and register all system plugins
import diagnostics_framework.systems  # noqa: F401
