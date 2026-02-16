import io
import json

import pandas as pd
import streamlit as st

# Import systems to trigger decorator registration
import diagnostics_framework.systems  # noqa: F401

from diagnostics_framework.models import DiagnosticStatus
from diagnostics_framework.registry import registry
from diagnostics_framework.runner import run_diagnostics, generate_plot, generate_report


STATUS_COLORS = {
    DiagnosticStatus.PASS: "#28a745",
    DiagnosticStatus.FAIL: "#dc3545",
    DiagnosticStatus.WARNING: "#ffc107",
    DiagnosticStatus.ERROR: "#6c757d",
}

STATUS_ICONS = {
    DiagnosticStatus.PASS: "PASS",
    DiagnosticStatus.FAIL: "FAIL",
    DiagnosticStatus.WARNING: "WARN",
    DiagnosticStatus.ERROR: "ERR",
}


def load_data(uploaded_file) -> pd.DataFrame | dict | None:
    """Attempt to load an uploaded file as a DataFrame or dict."""
    if uploaded_file is None:
        return None

    name = uploaded_file.name.lower()
    try:
        if name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif name.endswith(".json"):
            content = json.load(uploaded_file)
            if isinstance(content, list) and all(isinstance(r, dict) for r in content):
                return pd.DataFrame(content)
            return content
        elif name.endswith((".xls", ".xlsx")):
            return pd.read_excel(uploaded_file)
        elif name.endswith(".parquet"):
            return pd.read_parquet(io.BytesIO(uploaded_file.read()))
        else:
            return uploaded_file.read().decode("utf-8", errors="replace")
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return None


def render_results(summary):
    """Render diagnostic results as a styled table."""
    st.subheader("Diagnostic Results")

    cols = st.columns(4)
    cols[0].metric("Total", len(summary.results))
    cols[1].metric("Pass", summary.pass_count)
    cols[2].metric("Fail", summary.fail_count)
    cols[3].metric("Warn / Error", summary.warning_count + summary.error_count)

    for result in summary.results:
        color = STATUS_COLORS[result.status]
        icon = STATUS_ICONS[result.status]
        with st.container():
            st.markdown(
                f"<div style='border-left: 4px solid {color}; padding: 8px 12px; margin: 4px 0;'>"
                f"<strong>[{icon}]</strong> <strong>{result.test_name}</strong><br/>"
                f"{result.message}"
                f"</div>",
                unsafe_allow_html=True,
            )
            if result.details:
                with st.expander("Details"):
                    st.json(result.details)


def render_plots(system_name, data):
    """Render plot buttons and display generated plots."""
    st.subheader("Plots")
    plots = registry.get_plots(system_name)
    if not plots:
        st.info("No plots registered for this system.")
        return

    for plot_info in plots:
        with st.expander(f"{plot_info.name} — {plot_info.description}"):
            try:
                fig = generate_plot(system_name, plot_info.name, data)
                st.pyplot(fig)
            except Exception as e:
                st.error(f"Error generating plot: {e}")


def render_reports(system_name, data):
    """Render report buttons and display generated reports."""
    st.subheader("Reports")
    reports = registry.get_reports(system_name)
    if not reports:
        st.info("No reports registered for this system.")
        return

    for report_info in reports:
        with st.expander(f"{report_info.name} — {report_info.description}"):
            try:
                report_text = generate_report(system_name, report_info.name, data)
                st.markdown(report_text)
            except Exception as e:
                st.error(f"Error generating report: {e}")


def main():
    st.set_page_config(page_title="Diagnostics Dashboard", layout="wide")
    st.title("Diagnostics Dashboard")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Configuration")

        systems = registry.get_systems()
        if not systems:
            st.warning("No systems registered. Add a system module to diagnostics_framework/systems/.")
            return

        system_names = list(systems.keys())
        selected = st.selectbox(
            "Select System",
            system_names,
            format_func=lambda s: f"{s} — {systems[s].description}" if systems[s].description else s,
        )

        st.markdown("---")
        st.subheader("Upload Data")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["csv", "json", "xlsx", "xls", "parquet", "txt"],
        )

        run_button = st.button("Run Diagnostics", type="primary", use_container_width=True)

    # --- Main area ---
    if uploaded_file is not None:
        data = load_data(uploaded_file)
        if data is None:
            return

        if isinstance(data, pd.DataFrame):
            with st.expander("Preview uploaded data"):
                st.dataframe(data.head(50))

        if run_button:
            with st.spinner("Running diagnostics..."):
                summary = run_diagnostics(selected, data)
            st.session_state["last_summary"] = summary
            st.session_state["last_data"] = data
            st.session_state["last_system"] = selected

        if "last_summary" in st.session_state and st.session_state.get("last_system") == selected:
            tab_results, tab_plots, tab_reports = st.tabs(["Results", "Plots", "Reports"])
            with tab_results:
                render_results(st.session_state["last_summary"])
            with tab_plots:
                render_plots(selected, st.session_state.get("last_data", data))
            with tab_reports:
                render_reports(selected, st.session_state.get("last_data", data))
    else:
        st.info("Upload a data file in the sidebar and click **Run Diagnostics** to begin.")

        # Show registered info for the selected system
        if "selected" not in dir():
            return
        st.markdown(f"### System: {selected}")
        tests = registry.get_tests(selected)
        plots = registry.get_plots(selected)
        reports = registry.get_reports(selected)
        st.markdown(f"- **{len(tests)}** diagnostic test(s) registered")
        st.markdown(f"- **{len(plots)}** plot(s) registered")
        st.markdown(f"- **{len(reports)}** report(s) registered")


if __name__ == "__main__":
    main()
