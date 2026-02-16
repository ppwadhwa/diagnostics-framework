"""
Generic Example System
======================
A template system demonstrating the diagnostics framework plugin pattern.
Copy this file and modify it to create diagnostics for your own system.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from diagnostics_framework.models import DiagnosticResult, DiagnosticStatus
from diagnostics_framework.registry import register_system, register_test, register_plot, register_report

SYSTEM_NAME = "generic_example"


@register_system(SYSTEM_NAME, description="Generic example system for tabular data", version="0.1.0")
class GenericExampleSystem:
    pass


# ---------------------------------------------------------------------------
# Diagnostic Tests
# ---------------------------------------------------------------------------

@register_test(SYSTEM_NAME, name="check_not_empty", description="Verify the data is not empty")
def check_not_empty(data) -> DiagnosticResult:
    if isinstance(data, pd.DataFrame):
        is_empty = data.empty
        size = len(data)
    elif isinstance(data, (list, dict)):
        is_empty = len(data) == 0
        size = len(data)
    else:
        is_empty = data is None
        size = 0 if data is None else 1

    if is_empty:
        return DiagnosticResult(
            test_name="check_not_empty",
            status=DiagnosticStatus.FAIL,
            message="Data is empty.",
        )
    return DiagnosticResult(
        test_name="check_not_empty",
        status=DiagnosticStatus.PASS,
        message=f"Data has {size} records.",
        details={"record_count": size},
    )


@register_test(SYSTEM_NAME, name="check_no_nulls", description="Check for null or missing values")
def check_no_nulls(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame):
        return DiagnosticResult(
            test_name="check_no_nulls",
            status=DiagnosticStatus.WARNING,
            message="Null check only supported for DataFrame input. Skipped.",
        )

    null_counts = data.isnull().sum()
    total_nulls = int(null_counts.sum())
    cols_with_nulls = {col: int(count) for col, count in null_counts.items() if count > 0}

    if total_nulls == 0:
        return DiagnosticResult(
            test_name="check_no_nulls",
            status=DiagnosticStatus.PASS,
            message="No null values found.",
        )

    return DiagnosticResult(
        test_name="check_no_nulls",
        status=DiagnosticStatus.WARNING if total_nulls < len(data) else DiagnosticStatus.FAIL,
        message=f"Found {total_nulls} null value(s) across {len(cols_with_nulls)} column(s).",
        details={"columns_with_nulls": cols_with_nulls},
    )


@register_test(SYSTEM_NAME, name="check_numeric_ranges", description="Validate numeric columns have finite values")
def check_numeric_ranges(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame):
        return DiagnosticResult(
            test_name="check_numeric_ranges",
            status=DiagnosticStatus.WARNING,
            message="Range check only supported for DataFrame input. Skipped.",
        )

    numeric_cols = data.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return DiagnosticResult(
            test_name="check_numeric_ranges",
            status=DiagnosticStatus.WARNING,
            message="No numeric columns found to check.",
        )

    issues = {}
    for col in numeric_cols:
        inf_count = int(np.isinf(data[col].dropna()).sum())
        if inf_count > 0:
            issues[col] = {"infinite_values": inf_count}

    if issues:
        return DiagnosticResult(
            test_name="check_numeric_ranges",
            status=DiagnosticStatus.FAIL,
            message=f"Found infinite values in {len(issues)} column(s).",
            details={"columns_with_issues": issues},
        )

    return DiagnosticResult(
        test_name="check_numeric_ranges",
        status=DiagnosticStatus.PASS,
        message=f"All {len(numeric_cols)} numeric column(s) have finite values.",
        details={"numeric_columns": numeric_cols},
    )


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

@register_plot(SYSTEM_NAME, name="data_overview", description="Overview histogram of numeric columns")
def data_overview_plot(data) -> plt.Figure:
    if not isinstance(data, pd.DataFrame):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Plot requires DataFrame input", ha="center", va="center")
        return fig

    numeric_cols = data.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No numeric columns to plot", ha="center", va="center")
        return fig

    n_cols = len(numeric_cols)
    fig, axes = plt.subplots(1, n_cols, figsize=(4 * n_cols, 4), squeeze=False)
    for i, col in enumerate(numeric_cols):
        axes[0][i].hist(data[col].dropna(), bins=20, edgecolor="black", alpha=0.7)
        axes[0][i].set_title(col)
        axes[0][i].set_xlabel("Value")
        axes[0][i].set_ylabel("Count")
    fig.suptitle("Numeric Column Distributions", fontsize=14)
    fig.tight_layout()
    return fig


@register_plot(SYSTEM_NAME, name="null_heatmap", description="Heatmap showing location of null values")
def null_heatmap(data) -> plt.Figure:
    if not isinstance(data, pd.DataFrame):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Plot requires DataFrame input", ha="center", va="center")
        return fig

    fig, ax = plt.subplots(figsize=(max(6, len(data.columns)), max(4, len(data) * 0.05)))
    sns.heatmap(data.isnull().astype(int), cbar=False, cmap="YlOrRd", ax=ax, yticklabels=False)
    ax.set_title("Null Values (yellow = present, red = null)")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@register_report(SYSTEM_NAME, name="summary_report", description="Text summary of the dataset")
def summary_report(data) -> str:
    if not isinstance(data, pd.DataFrame):
        return f"Data type: {type(data).__name__}\nCannot generate detailed summary for non-DataFrame data."

    lines = [
        "# Data Summary Report",
        "",
        f"**Rows:** {len(data)}",
        f"**Columns:** {len(data.columns)}",
        "",
        "## Column Types",
    ]
    for col in data.columns:
        lines.append(f"- **{col}**: {data[col].dtype}")

    lines.append("")
    lines.append("## Null Counts")
    null_counts = data.isnull().sum()
    for col, count in null_counts.items():
        if count > 0:
            lines.append(f"- **{col}**: {count} nulls ({count / len(data) * 100:.1f}%)")
    if null_counts.sum() == 0:
        lines.append("- No null values found.")

    numeric_cols = data.select_dtypes(include="number")
    if not numeric_cols.empty:
        lines.append("")
        lines.append("## Numeric Summary")
        for col in numeric_cols.columns:
            series = numeric_cols[col].dropna()
            lines.append(f"- **{col}**: min={series.min():.4g}, max={series.max():.4g}, "
                         f"mean={series.mean():.4g}, std={series.std():.4g}")

    return "\n".join(lines)
