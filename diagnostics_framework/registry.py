from diagnostics_framework.models import SystemInfo, TestInfo, PlotInfo, ReportInfo


class DiagnosticsRegistry:
    """Singleton registry for systems, tests, plots, and reports."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._systems = {}
            cls._instance._tests = {}
            cls._instance._plots = {}
            cls._instance._reports = {}
        return cls._instance

    def add_system(self, name: str, description: str = "", version: str = "0.1.0"):
        self._systems[name] = SystemInfo(name=name, description=description, version=version)
        self._tests.setdefault(name, [])
        self._plots.setdefault(name, [])
        self._reports.setdefault(name, [])

    def add_test(self, system: str, test_info: TestInfo):
        self._tests.setdefault(system, []).append(test_info)

    def add_plot(self, system: str, plot_info: PlotInfo):
        self._plots.setdefault(system, []).append(plot_info)

    def add_report(self, system: str, report_info: ReportInfo):
        self._reports.setdefault(system, []).append(report_info)

    def get_systems(self) -> dict[str, SystemInfo]:
        return dict(self._systems)

    def get_tests(self, system: str) -> list[TestInfo]:
        return list(self._tests.get(system, []))

    def get_plots(self, system: str) -> list[PlotInfo]:
        return list(self._plots.get(system, []))

    def get_reports(self, system: str) -> list[ReportInfo]:
        return list(self._reports.get(system, []))


# Module-level singleton
registry = DiagnosticsRegistry()


def register_system(name: str, description: str = "", version: str = "0.1.0"):
    """Decorator that registers a system. Apply to any function or class (it's returned unchanged)."""
    def decorator(obj):
        registry.add_system(name, description, version)
        return obj
    return decorator


def register_test(system: str, name: str, description: str = ""):
    """Decorator that registers a diagnostic test function for a system."""
    def decorator(fn):
        registry.add_test(system, TestInfo(name=name, description=description, fn=fn))
        return fn
    return decorator


def register_plot(system: str, name: str, description: str = ""):
    """Decorator that registers a plot function for a system."""
    def decorator(fn):
        registry.add_plot(system, PlotInfo(name=name, description=description, fn=fn))
        return fn
    return decorator


def register_report(system: str, name: str, description: str = ""):
    """Decorator that registers a report function for a system."""
    def decorator(fn):
        registry.add_report(system, ReportInfo(name=name, description=description, fn=fn))
        return fn
    return decorator
