"""
Sensor Monitoring System
========================
Diagnostics for IoT/environmental sensor data with time series,
battery health, and anomaly detection checks.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from diagnostics_framework.models import DiagnosticResult, DiagnosticStatus
from diagnostics_framework.registry import register_system, register_test, register_plot, register_report

SYSTEM_NAME = "sensor_monitoring"


@register_system(SYSTEM_NAME, description="IoT sensor monitoring diagnostics", version="0.1.0")
class SensorMonitoringSystem:
    pass


# ---------------------------------------------------------------------------
# Diagnostic Tests
# ---------------------------------------------------------------------------

@register_test(SYSTEM_NAME, name="check_not_empty", description="Verify sensor data is not empty")
def check_not_empty(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame) or data.empty:
        return DiagnosticResult(
            test_name="check_not_empty",
            status=DiagnosticStatus.FAIL,
            message="No data found.",
        )
    return DiagnosticResult(
        test_name="check_not_empty",
        status=DiagnosticStatus.PASS,
        message=f"Dataset has {len(data)} rows and {len(data.columns)} columns.",
        details={"rows": len(data), "columns": list(data.columns)},
    )


@register_test(SYSTEM_NAME, name="check_missing_readings", description="Check for missing sensor readings")
def check_missing_readings(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame):
        return DiagnosticResult(test_name="check_missing_readings", status=DiagnosticStatus.WARNING, message="Skipped: not a DataFrame.")

    null_counts = data.isnull().sum()
    total_nulls = int(null_counts.sum())
    total_cells = int(data.size)
    pct = total_nulls / total_cells * 100 if total_cells > 0 else 0
    cols_with_nulls = {col: int(c) for col, c in null_counts.items() if c > 0}

    if total_nulls == 0:
        return DiagnosticResult(test_name="check_missing_readings", status=DiagnosticStatus.PASS, message="No missing readings.")

    status = DiagnosticStatus.WARNING if pct < 5 else DiagnosticStatus.FAIL
    return DiagnosticResult(
        test_name="check_missing_readings",
        status=status,
        message=f"{total_nulls} missing values ({pct:.1f}% of all cells) across {len(cols_with_nulls)} column(s).",
        details={"missing_by_column": cols_with_nulls, "total_missing": total_nulls, "percent_missing": round(pct, 2)},
    )


@register_test(SYSTEM_NAME, name="check_battery_health", description="Flag sensors with low battery levels")
def check_battery_health(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame) or "battery_level" not in data.columns:
        return DiagnosticResult(test_name="check_battery_health", status=DiagnosticStatus.WARNING, message="No battery_level column found.")

    low_threshold = 20.0
    critical_threshold = 10.0
    battery = data[["sensor_id", "battery_level"]].dropna() if "sensor_id" in data.columns else data[["battery_level"]].dropna()

    if "sensor_id" in data.columns:
        latest = battery.groupby("sensor_id")["battery_level"].last()
        critical = latest[latest < critical_threshold].to_dict()
        low = latest[(latest >= critical_threshold) & (latest < low_threshold)].to_dict()
    else:
        last_val = float(battery["battery_level"].iloc[-1])
        critical = {"unknown": last_val} if last_val < critical_threshold else {}
        low = {"unknown": last_val} if critical_threshold <= last_val < low_threshold else {}

    if critical:
        return DiagnosticResult(
            test_name="check_battery_health",
            status=DiagnosticStatus.FAIL,
            message=f"{len(critical)} sensor(s) at CRITICAL battery level (<{critical_threshold}%).",
            details={"critical_sensors": critical, "low_sensors": low},
        )
    if low:
        return DiagnosticResult(
            test_name="check_battery_health",
            status=DiagnosticStatus.WARNING,
            message=f"{len(low)} sensor(s) with low battery (<{low_threshold}%).",
            details={"low_sensors": low},
        )
    return DiagnosticResult(
        test_name="check_battery_health",
        status=DiagnosticStatus.PASS,
        message="All sensors have healthy battery levels.",
    )


@register_test(SYSTEM_NAME, name="check_temperature_range", description="Validate temperature readings are within expected range")
def check_temperature_range(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame) or "temperature" not in data.columns:
        return DiagnosticResult(test_name="check_temperature_range", status=DiagnosticStatus.WARNING, message="No temperature column found.")

    temp = data["temperature"].dropna()
    min_expected, max_expected = -10.0, 50.0
    out_of_range = temp[(temp < min_expected) | (temp > max_expected)]

    if len(out_of_range) > 0:
        return DiagnosticResult(
            test_name="check_temperature_range",
            status=DiagnosticStatus.FAIL,
            message=f"{len(out_of_range)} readings outside expected range [{min_expected}, {max_expected}].",
            details={"out_of_range_count": len(out_of_range), "min_observed": float(temp.min()), "max_observed": float(temp.max())},
        )
    return DiagnosticResult(
        test_name="check_temperature_range",
        status=DiagnosticStatus.PASS,
        message=f"All {len(temp)} temperature readings within [{min_expected}, {max_expected}]. Range: {temp.min():.1f} to {temp.max():.1f}.",
        details={"min": float(temp.min()), "max": float(temp.max()), "mean": float(temp.mean())},
    )


@register_test(SYSTEM_NAME, name="check_sensor_status", description="Check for sensors in warning or critical status")
def check_sensor_status(data) -> DiagnosticResult:
    if not isinstance(data, pd.DataFrame) or "status" not in data.columns:
        return DiagnosticResult(test_name="check_sensor_status", status=DiagnosticStatus.WARNING, message="No status column found.")

    status_counts = data["status"].value_counts().to_dict()
    critical_count = status_counts.get("critical", 0)
    warning_count = status_counts.get("warning", 0)

    if critical_count > 0:
        return DiagnosticResult(
            test_name="check_sensor_status",
            status=DiagnosticStatus.FAIL,
            message=f"{critical_count} readings in 'critical' status, {warning_count} in 'warning'.",
            details={"status_breakdown": status_counts},
        )
    if warning_count > 0:
        return DiagnosticResult(
            test_name="check_sensor_status",
            status=DiagnosticStatus.WARNING,
            message=f"{warning_count} readings in 'warning' status.",
            details={"status_breakdown": status_counts},
        )
    return DiagnosticResult(
        test_name="check_sensor_status",
        status=DiagnosticStatus.PASS,
        message="All sensors reporting normal status.",
        details={"status_breakdown": status_counts},
    )


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

@register_plot(SYSTEM_NAME, name="temperature_timeseries", description="Temperature over time per sensor")
def temperature_timeseries(data) -> plt.Figure:
    if not isinstance(data, pd.DataFrame) or "temperature" not in data.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Requires 'temperature' column", ha="center", va="center")
        return fig

    fig, ax = plt.subplots(figsize=(12, 5))
    if "sensor_id" in data.columns and "timestamp" in data.columns:
        for sensor_id, group in data.groupby("sensor_id"):
            ts = pd.to_datetime(group["timestamp"], errors="coerce")
            ax.plot(ts, group["temperature"], marker="o", markersize=3, label=sensor_id)
        ax.legend(title="Sensor")
        ax.set_xlabel("Time")
    else:
        ax.plot(data.index, data["temperature"], marker="o", markersize=3)
        ax.set_xlabel("Index")
    ax.set_ylabel("Temperature")
    ax.set_title("Temperature Over Time")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


@register_plot(SYSTEM_NAME, name="battery_levels", description="Battery level per sensor over time")
def battery_levels(data) -> plt.Figure:
    if not isinstance(data, pd.DataFrame) or "battery_level" not in data.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Requires 'battery_level' column", ha="center", va="center")
        return fig

    fig, ax = plt.subplots(figsize=(12, 5))
    if "sensor_id" in data.columns and "timestamp" in data.columns:
        for sensor_id, group in data.groupby("sensor_id"):
            ts = pd.to_datetime(group["timestamp"], errors="coerce")
            ax.plot(ts, group["battery_level"], marker="o", markersize=3, label=sensor_id)
        ax.legend(title="Sensor")
        ax.set_xlabel("Time")
    else:
        ax.plot(data.index, data["battery_level"], marker="o", markersize=3)
        ax.set_xlabel("Index")

    ax.axhline(y=20, color="orange", linestyle="--", alpha=0.7, label="Low threshold (20%)")
    ax.axhline(y=10, color="red", linestyle="--", alpha=0.7, label="Critical threshold (10%)")
    ax.set_ylabel("Battery Level (%)")
    ax.set_title("Battery Level Over Time")
    ax.legend(title="Sensor")
    ax.grid(True, alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig


@register_plot(SYSTEM_NAME, name="correlation_heatmap", description="Correlation matrix of numeric columns")
def correlation_heatmap(data) -> plt.Figure:
    if not isinstance(data, pd.DataFrame):
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Requires DataFrame input", ha="center", va="center")
        return fig

    numeric = data.select_dtypes(include="number")
    if numeric.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No numeric columns", ha="center", va="center")
        return fig

    fig, ax = plt.subplots(figsize=(8, 6))
    corr = numeric.corr()
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax, square=True)
    ax.set_title("Correlation Matrix")
    fig.tight_layout()
    return fig


@register_plot(SYSTEM_NAME, name="sensor_status_breakdown", description="Pie chart of sensor status counts")
def sensor_status_breakdown(data) -> plt.Figure:
    if not isinstance(data, pd.DataFrame) or "status" not in data.columns:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Requires 'status' column", ha="center", va="center")
        return fig

    status_counts = data["status"].value_counts()
    colors = {"active": "#28a745", "warning": "#ffc107", "critical": "#dc3545", "inactive": "#6c757d"}
    pie_colors = [colors.get(s, "#999999") for s in status_counts.index]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.0f%%", colors=pie_colors, startangle=90)
    ax.set_title("Sensor Status Breakdown")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@register_report(SYSTEM_NAME, name="sensor_health_report", description="Full health report across all sensors")
def sensor_health_report(data) -> str:
    if not isinstance(data, pd.DataFrame):
        return "Report requires DataFrame input."

    lines = ["# Sensor Health Report", ""]

    lines.append(f"**Total readings:** {len(data)}")
    if "sensor_id" in data.columns:
        sensors = data["sensor_id"].nunique()
        lines.append(f"**Unique sensors:** {sensors}")
        lines.append(f"**Sensors:** {', '.join(sorted(data['sensor_id'].unique()))}")
    lines.append("")

    # Missing data
    null_counts = data.isnull().sum()
    total_nulls = int(null_counts.sum())
    lines.append("## Data Completeness")
    if total_nulls == 0:
        lines.append("All readings complete — no missing values.")
    else:
        lines.append(f"**{total_nulls} missing values** detected:")
        for col, count in null_counts.items():
            if count > 0:
                lines.append(f"- {col}: {count} missing ({count / len(data) * 100:.1f}%)")
    lines.append("")

    # Battery
    if "battery_level" in data.columns and "sensor_id" in data.columns:
        lines.append("## Battery Status")
        latest_battery = data.groupby("sensor_id")["battery_level"].last()
        for sensor_id, level in latest_battery.items():
            if pd.isna(level):
                emoji = "unknown"
            elif level < 10:
                emoji = "CRITICAL"
            elif level < 20:
                emoji = "LOW"
            else:
                emoji = "OK"
            display_level = f"{level:.1f}%" if not pd.isna(level) else "N/A"
            lines.append(f"- **{sensor_id}**: {display_level} [{emoji}]")
        lines.append("")

    # Temperature
    if "temperature" in data.columns:
        temp = data["temperature"].dropna()
        lines.append("## Temperature Summary")
        lines.append(f"- Min: {temp.min():.1f}")
        lines.append(f"- Max: {temp.max():.1f}")
        lines.append(f"- Mean: {temp.mean():.1f}")
        lines.append(f"- Std Dev: {temp.std():.1f}")
        lines.append("")

    # Status
    if "status" in data.columns:
        lines.append("## Status Summary")
        for status, count in data["status"].value_counts().items():
            lines.append(f"- **{status}**: {count} readings ({count / len(data) * 100:.0f}%)")

    return "\n".join(lines)
