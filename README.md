# Diagnostics Framework

A pluggable Python framework for running diagnostic tests, generating plots, and viewing reports for any system — all from a Streamlit dashboard.

## Overview

The framework uses a **plugin architecture**: each "system" is a self-contained module that registers its own diagnostic tests, plots, and reports using simple decorators. Adding a new system is as easy as dropping a new Python file into the `systems/` folder.

**Built-in example systems:**

| System | Description |
|--------|-------------|
| `generic_example` | Basic tabular data checks (nulls, ranges, emptiness) |
| `sensor_monitoring` | IoT sensor diagnostics with battery health, temperature validation, and status tracking |

## Quick Start

### Install

```bash
# Create a virtual environment (Python 3.10+ required)
python -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .
```

### Run the Dashboard

```bash
streamlit run diagnostics_framework/app.py
```

Open http://localhost:8501, select a system, upload a data file, and click **Run Diagnostics**.

A sample dataset is included at `sample_data.csv` for testing the `sensor_monitoring` system.

## Project Structure

```
diagnostics_framework/
├── models.py           # Dataclasses: DiagnosticResult, DiagnosticStatus, etc.
├── registry.py         # Singleton registry + decorator API
├── runner.py           # Test execution engine with error isolation
├── app.py              # Streamlit dashboard
└── systems/
    ├── __init__.py             # Auto-discovers all system modules
    ├── generic_example.py      # Example: generic tabular data checks
    └── sensor_monitoring.py    # Example: IoT sensor diagnostics
```

## Adding a New System

Create a new file in `diagnostics_framework/systems/` — it will be auto-discovered on import.

```python
# diagnostics_framework/systems/my_system.py
from diagnostics_framework import (
    register_system, register_test, register_plot, register_report,
    DiagnosticResult, DiagnosticStatus,
)

SYSTEM_NAME = "my_system"

@register_system(SYSTEM_NAME, description="My custom system")
class MySystem:
    pass

@register_test(SYSTEM_NAME, name="my_check", description="Validates something important")
def my_check(data):
    # Your test logic here
    return DiagnosticResult(
        test_name="my_check",
        status=DiagnosticStatus.PASS,
        message="Everything looks good.",
    )

@register_plot(SYSTEM_NAME, name="my_plot", description="Visualizes the data")
def my_plot(data):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    # Your plotting logic here
    return fig

@register_report(SYSTEM_NAME, name="my_report", description="Summary of findings")
def my_report(data):
    return "# My Report\n\nEverything is fine."
```

That's it — the new system will appear in the dashboard dropdown automatically.

## Decorator API

| Decorator | Purpose |
|-----------|---------|
| `@register_system(name, description, version)` | Register a new system |
| `@register_test(system, name, description)` | Add a diagnostic test |
| `@register_plot(system, name, description)` | Add a plot generator |
| `@register_report(system, name, description)` | Add a report generator |

## Diagnostic Result Statuses

| Status | Meaning |
|--------|---------|
| `PASS` | Test passed successfully |
| `FAIL` | Test found a problem |
| `WARNING` | Test found something worth noting |
| `ERROR` | Test itself crashed (caught automatically by the runner) |

## Programmatic Usage

You can also use the framework without the dashboard:

```python
import pandas as pd
from diagnostics_framework import run_diagnostics

data = pd.read_csv("sample_data.csv")
summary = run_diagnostics("sensor_monitoring", data)

for result in summary.results:
    print(f"[{result.status.value}] {result.test_name}: {result.message}")
```

## Dependencies

- Python >= 3.10
- streamlit
- pandas
- matplotlib
- seaborn
