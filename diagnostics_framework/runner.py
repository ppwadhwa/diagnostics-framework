import traceback
from datetime import datetime
from typing import Any

import matplotlib.figure

from diagnostics_framework.models import DiagnosticResult, DiagnosticStatus, DiagnosticSummary
from diagnostics_framework.registry import registry


def run_diagnostics(system_name: str, data: Any) -> DiagnosticSummary:
    """Run all registered diagnostic tests for a system against the provided data."""
    tests = registry.get_tests(system_name)
    results = []

    for test_info in tests:
        try:
            result = test_info.fn(data)
            if isinstance(result, DiagnosticResult):
                results.append(result)
            else:
                results.append(DiagnosticResult(
                    test_name=test_info.name,
                    status=DiagnosticStatus.ERROR,
                    message=f"Test '{test_info.name}' did not return a DiagnosticResult.",
                ))
        except Exception as e:
            results.append(DiagnosticResult(
                test_name=test_info.name,
                status=DiagnosticStatus.ERROR,
                message=f"Test raised an exception: {e}",
                details={"traceback": traceback.format_exc()},
            ))

    return DiagnosticSummary(
        system_name=system_name,
        results=results,
        timestamp=datetime.now(),
    )


def generate_plot(system_name: str, plot_name: str, data: Any) -> matplotlib.figure.Figure:
    """Generate a plot by name for a system. Returns a matplotlib Figure."""
    plots = registry.get_plots(system_name)
    for plot_info in plots:
        if plot_info.name == plot_name:
            return plot_info.fn(data)
    raise ValueError(f"Plot '{plot_name}' not found for system '{system_name}'.")


def generate_report(system_name: str, report_name: str, data: Any) -> str:
    """Generate a report by name for a system. Returns a string (plain text or markdown)."""
    reports = registry.get_reports(system_name)
    for report_info in reports:
        if report_info.name == report_name:
            return report_info.fn(data)
    raise ValueError(f"Report '{report_name}' not found for system '{system_name}'.")
