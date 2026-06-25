import glob
import logging
import os
import threading
import time
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx  # noqa: E402

from graph.workflow import create_workflow

# Page config must be the first Streamlit command
st.set_page_config(page_title="Digital Footprint Investigator", layout="wide", initial_sidebar_state="expanded")

# Load environment variables
load_dotenv()


class StreamlitLogHandler(logging.Handler):
    """Appends log records to a list stored in session_state.
    The main thread polling loop reads from that list and renders it."""

    def __init__(self, log_buffer: list):
        super().__init__()
        self.log_buffer = log_buffer
        self.ctx = get_script_run_ctx()

    def emit(self, record):
        if not get_script_run_ctx():
            add_script_run_ctx(ctx=self.ctx)
        self.log_buffer.append(self.format(record))
        if len(self.log_buffer) > 50:
            self.log_buffer.pop(0)


@st.cache_data
def load_config():
    """Load configuration from config.yaml"""
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {
            "platforms": {},
            "advanced_analysis": {
                "timeline_correlation": False,
                "network_analysis": False,
                "deep_content_analysis": False,
            },
        }


def get_saved_reports() -> list[Path]:
    """Return all saved report .md files sorted newest-first."""
    reports_dir = Path("reports").resolve()
    if not reports_dir.exists():
        return []
    files = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    valid_files = []
    for f in files:
        resolved = f.resolve()
        if str(resolved).startswith(str(reports_dir)):
            valid_files.append(resolved)
    return valid_files


def render_reports_page():
    """Render the saved reports browser page."""
    st.title("Saved Reports")
    st.markdown("Browse and open previously generated investigation reports.")

    report_files = get_saved_reports()

    if not report_files:
        st.info("No reports found in the `reports/` folder yet. Run an investigation to generate one.")
        return

    if "delete_confirm" not in st.session_state:
        st.session_state.delete_confirm = False
    if "delete_all_confirm" not in st.session_state:
        st.session_state.delete_all_confirm = False
    if "previous_selected_report" not in st.session_state:
        st.session_state.previous_selected_report = None

    # Let the user pick a report
    report_names = [p.name for p in report_files]
    selected_name = st.selectbox(
        "Select a report",
        options=report_names,
        index=0,
        help="Reports are sorted newest-first.",
    )

    if st.session_state.previous_selected_report != selected_name:
        st.session_state.previous_selected_report = selected_name
        st.session_state.delete_confirm = False
        st.session_state.delete_all_confirm = False

    selected_path = (Path("reports") / selected_name).resolve()
    if not str(selected_path).startswith(str(Path("reports").resolve())):
        raise ValueError(f"Invalid report path: {selected_path}")
    base_path = selected_path.with_suffix("")

    try:
        with open(selected_path, "r", encoding="utf-8") as fh:
            content = fh.read()

        json_path = base_path.with_suffix(".json")
        html_path = base_path.with_suffix(".html")
        pdf_path = base_path.with_suffix(".pdf")

        json_content = json_path.read_text(encoding="utf-8") if json_path.exists() else ""
        html_content = html_path.read_text(encoding="utf-8") if html_path.exists() else ""
        pdf_content = pdf_path.read_bytes() if pdf_path.exists() else b""
    except Exception as e:
        st.error(f"Error reading report: {e}")
        return

    st.markdown("### Download Options")
    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
    with dl_col1:
        st.download_button(
            label="📥 Markdown (.md)",
            data=content,
            file_name=selected_name,
            mime="text/markdown",
            key="btn_download_report",
        )
    with dl_col2:
        if pdf_content:
            st.download_button(
                label="📥 PDF Document",
                data=pdf_content,
                file_name=f"{base_path.name}.pdf",
                mime="application/pdf",
                key="btn_download_pdf",
            )
    with dl_col3:
        if html_content:
            st.download_button(
                label="📥 HTML Format",
                data=html_content,
                file_name=f"{base_path.name}.html",
                mime="text/html",
                key="btn_download_html",
            )
    with dl_col4:
        if json_content:
            st.download_button(
                label="📥 JSON Data",
                data=json_content,
                file_name=f"{base_path.name}.json",
                mime="application/json",
                key="btn_download_json",
            )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete Selected Report", key="btn_delete_selected"):
            st.session_state.delete_confirm = True
            st.session_state.delete_all_confirm = False
    with col2:
        if st.button("Delete All Reports", key="btn_delete_all"):
            st.session_state.delete_all_confirm = True
            st.session_state.delete_confirm = False

    if st.session_state.delete_confirm:
        st.warning(f"Are you sure you want to delete {selected_name} and its associated formats?")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Yes, Delete", key="btn_confirm_delete_selected"):
                try:
                    for ext in [".md", ".json", ".html", ".pdf"]:
                        p = base_path.with_suffix(ext)
                        if p.exists():
                            p.unlink()
                    st.success(f"Deleted {selected_name} and associated formats")
                    st.session_state.delete_confirm = False
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting file: {e}")
        with col_c2:
            if st.button("Cancel", key="btn_cancel_delete_selected"):
                st.session_state.delete_confirm = False
                st.rerun()

    elif st.session_state.delete_all_confirm:
        st.warning("Are you sure you want to delete ALL reports? This action cannot be undone.")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("Yes, Delete All", key="btn_confirm_delete_all"):
                try:
                    deleted_count = 0
                    for rf in report_files:
                        bp = rf.with_suffix("")
                        for ext in [".md", ".json", ".html", ".pdf"]:
                            p = bp.with_suffix(ext)
                            if p.exists():
                                p.unlink()
                        deleted_count += 1
                    st.success(f"Deleted {deleted_count} reports and their associated formats")
                    st.session_state.delete_all_confirm = False
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting files: {e}")
        with col_c2:
            if st.button("Cancel", key="btn_cancel_delete_all"):
                st.session_state.delete_all_confirm = False
                st.rerun()

    if not st.session_state.delete_confirm and not st.session_state.delete_all_confirm:
        st.divider()
        st.markdown(content)
        st.divider()


def main():
    if not os.getenv("GEMINI_API_KEY"):
        st.warning("No Gemini API key found in .env file. Please configure your API keys.")

    # Initialize session state variables
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "report_content" not in st.session_state:
        st.session_state.report_content = None
    if "latest_report_file" not in st.session_state:
        st.session_state.latest_report_file = None
    if "stop_requested" not in st.session_state:
        st.session_state.stop_requested = False
    if "investigation_thread" not in st.session_state:
        st.session_state.investigation_thread = None
    if "log_buffer" not in st.session_state:
        st.session_state.log_buffer = []

    def start_investigation():
        st.session_state.processing = True
        st.session_state.stop_requested = False
        st.session_state.report_content = None
        st.session_state.latest_report_file = None
        st.session_state.log_buffer = []

    def stop_investigation():
        st.session_state.stop_requested = True

    # Sidebar Configuration
    with st.sidebar:
        st.header("Configuration")

        config = load_config()

        st.subheader("Scan Configuration")
        if "scan_mode" not in st.session_state:
            st.session_state.scan_mode = config.get("search", {}).get("mode", "advanced").capitalize()

        scan_mode_val = st.radio(
            "Scan Mode",
            options=["Quick", "Advanced"],
            index=0 if st.session_state.scan_mode == "Quick" else 1,
            help="Quick Scan runs unauthenticated using free, as-is services. Advanced Scan runs using configured API keys and premium services.",
            key="scan_mode_radio",
        )
        st.session_state.scan_mode = scan_mode_val
        config["scan_mode"] = scan_mode_val.lower()

        if scan_mode_val == "Advanced":
            st.subheader("Advanced Analysis")
            if "timeline" not in st.session_state:
                st.session_state.timeline = config["advanced_analysis"].get("timeline_correlation", False)
            if "network" not in st.session_state:
                st.session_state.network = config["advanced_analysis"].get("network_analysis", False)
            if "deep_content" not in st.session_state:
                st.session_state.deep_content = config["advanced_analysis"].get("deep_content_analysis", False)

            timeline = st.toggle(
                "Timeline Correlation",
                value=st.session_state.timeline,
                help="Constructs a chronological timeline of the target's activities across all discovered platforms.",
            )
            network = st.toggle(
                "Social Connection Analysis",
                value=st.session_state.network,
                help="Visualizes relationships and interactions between the target and other entities or accounts.",
            )
            deep_content = st.toggle(
                "Deep Content Analysis",
                value=st.session_state.deep_content,
                help="Performs in-depth analysis of post content, including sentiment, topics, and behavioral patterns.",
            )

            config["advanced_analysis"]["timeline_correlation"] = timeline
            config["advanced_analysis"]["network_analysis"] = network
            config["advanced_analysis"]["deep_content_analysis"] = deep_content
        else:
            config["advanced_analysis"]["timeline_correlation"] = False
            config["advanced_analysis"]["network_analysis"] = False
            config["advanced_analysis"]["deep_content_analysis"] = False

        st.divider()
        st.info("Ensure you have set up your API keys in .env for full functionality.")

    # Main Content — tabs
    tab_investigate, tab_reports = st.tabs(["🔍 Investigate", "📂 Reports"])

    with tab_reports:
        render_reports_page()

    with tab_investigate:
        st.title("Digital Footprint Investigator")
        st.markdown("""
        > **EDUCATIONAL USE ONLY**: This tool is designed for educational purposes, security research, and legitimate OSINT investigations.
        > Users must comply with all applicable laws and ethical guidelines. Misuse for stalking, harassment, or illegal
        > activities is strictly prohibited. By using this tool you accept full responsibility for compliance with all
        > applicable laws and platform Terms of Service, including Twitter/X, Reddit, and others.
        """)

        # Consent gate
        if "consent" not in st.session_state:
            st.session_state.consent = False

        consent = st.checkbox(
            "I confirm I have a legitimate purpose (security research, due diligence, personal privacy audit, or investigative journalism) "
            "and will comply with all applicable laws and platform Terms of Service.",
            value=st.session_state.consent,
            key="consent_checkbox",
        )
        st.session_state.consent = consent

        # Input Section
        col1, col2 = st.columns([3, 1], vertical_alignment="bottom")
        with col1:
            target_val = st.text_input(
                "Target Identifier", placeholder="Enter Name, Email, Username, or Phone Number...", key="target_input"
            )

        with col2:
            is_disabled = not target_val or not target_val.strip() or not consent

            if st.session_state.processing:
                st.button(
                    "⏹ Stop Investigation",
                    type="primary",
                    use_container_width=True,
                    on_click=stop_investigation,
                    key="stop_btn",
                )
            else:
                st.button(
                    "Start Investigation",
                    type="primary",
                    use_container_width=True,
                    disabled=is_disabled,
                    on_click=start_investigation,
                    key="start_btn",
                )

        # Processing Logic
        if st.session_state.processing:
            target_val = st.session_state.target_input

            if target_val and target_val.strip():
                st_handler = StreamlitLogHandler(st.session_state.log_buffer)
                root_logger = logging.getLogger()
                root_logger.addHandler(st_handler)
                root_logger.setLevel(logging.INFO)

                result_holder = {}

                def run_investigation():
                    try:
                        app = create_workflow()
                        inputs = {"target": target_val, "config": config}
                        import uuid

                        thread_config = {"configurable": {"thread_id": f"web_{uuid.uuid4()}"}}
                        result_holder["result"] = app.invoke(inputs, thread_config)
                    except Exception:
                        import traceback

                        result_holder["error"] = traceback.format_exc()

                thread = threading.Thread(target=run_investigation, daemon=True)
                st.session_state.investigation_thread = thread
                thread.start()

                status_container = st.empty()
                logs_expander = st.expander("Investigation Logs", expanded=True)
                log_placeholder = logs_expander.empty()

                with st.spinner(f"Investigating '{target_val}'..."):
                    status_container.info("Running searches and analysis... (Parallel Execution)")
                    while thread.is_alive():
                        if st.session_state.stop_requested:
                            status_container.warning("Stopping investigation...")
                            thread.join(timeout=2)
                            break
                        log_placeholder.code("\n".join(st.session_state.log_buffer) or " ", language="log")
                        time.sleep(0.5)
                    # Final render after thread finishes
                    log_placeholder.code("\n".join(st.session_state.log_buffer) or " ", language="log")

                if st.session_state.stop_requested:
                    st.session_state.report_content = (
                        "### Investigation Stopped\nThe investigation was manually stopped."
                    )
                elif "error" in result_holder:
                    st.session_state.report_content = (
                        f"### Error\nAn error occurred during investigation:\n\n```\n{result_holder['error']}\n```"
                    )
                else:
                    result = result_holder.get("result", {})
                    status_container.success("Investigation Complete!")

                    report_content = None
                    latest_file = None

                    normalized_target = target_val.replace(" ", "_")
                    list_of_files = glob.glob(f"reports/*{normalized_target}*.md")

                    if not list_of_files:
                        all_reports = glob.glob("reports/*.md")
                        if all_reports:
                            newest_file = max(all_reports, key=os.path.getmtime)
                            if time.time() - os.path.getmtime(newest_file) < 120:
                                list_of_files = [newest_file]

                    if list_of_files:
                        latest_file = Path(max(list_of_files, key=os.path.getctime)).resolve()
                        if not str(latest_file).startswith(str(Path("reports").resolve())):
                            raise ValueError(f"Invalid report path: {latest_file}")
                        with open(latest_file, "r", encoding="utf-8") as f:
                            report_content = f.read()
                    elif "messages" in result and result["messages"]:
                        report_content = result["messages"][-1].content
                    else:
                        report_content = "### Report Not Found\nCould not locate the generated report file or message content. Please check the logs."

                    st.session_state.report_content = report_content
                    st.session_state.latest_report_file = latest_file

                root_logger.removeHandler(st_handler)
                st.session_state.processing = False
                st.session_state.stop_requested = False
                st.session_state.investigation_thread = None
                st.rerun()

        # Result Display (Persistent)
        if st.session_state.report_content:
            st.divider()
            st.subheader("Investigation Report")
            st.markdown(st.session_state.report_content)

            if st.session_state.log_buffer:
                with st.expander("Investigation Logs (Debug)", expanded=False):
                    st.code("\n".join(st.session_state.log_buffer), language="log")

            if st.session_state.latest_report_file:
                file_name_dl = os.path.basename(st.session_state.latest_report_file)
                st.info(
                    "Report saved in multiple formats (PDF, JSON, HTML) in the `reports/` folder. Check the **Reports** tab to download them."
                )
            else:
                file_name_dl = "report.md"

            st.download_button(
                label="Download Markdown Report",
                data=st.session_state.report_content,
                file_name=file_name_dl,
                mime="text/markdown",
            )


if __name__ == "__main__":
    main()
