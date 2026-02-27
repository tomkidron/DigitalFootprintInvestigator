import glob
import logging
import os
import time

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
    """Custom logging handler to send logs to a Streamlit container"""

    def __init__(self, container_placeholder):
        super().__init__()
        self.container_placeholder = container_placeholder
        self.logs = []
        # Capture the context from the main thread where the handler is created
        self.ctx = get_script_run_ctx()

    def emit(self, record):
        # If calling from a thread without context, attach the captured context
        if not get_script_run_ctx():
            add_script_run_ctx(ctx=self.ctx)

        msg = self.format(record)
        self.logs.append(msg)
        # Keep only last 50 logs to avoid overflow
        if len(self.logs) > 50:
            self.logs.pop(0)

        # Join logs and render in code block
        log_text = "\n".join(self.logs)
        self.container_placeholder.code(log_text, language="log")


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


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("No Anthropic API key found in .env file. Please configure your API keys.")

    # Initialize session state variables
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "report_content" not in st.session_state:
        st.session_state.report_content = None
    if "latest_report_file" not in st.session_state:
        st.session_state.latest_report_file = None

    def start_investigation():
        st.session_state.processing = True
        st.session_state.report_content = None
        st.session_state.latest_report_file = None

    # Sidebar Configuration
    with st.sidebar:
        st.header("Configuration")

        config = load_config()

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
            "Network Analysis",
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

        st.divider()
        st.info("Ensure you have set up your API keys in .env for full functionality.")

    # Main Content
    st.title("Digital Footprint Investigator")
    st.markdown("""
    > **EDUCATIONAL USE ONLY**: This tool is designed for educational purposes, security research, and legitimate OSINT investigations.
    > Users must comply with all applicable laws and ethical guidelines.
    """)

    # Input Section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input(
            "Target Identifier", placeholder="Enter Name, Email, Username, or Phone Number...", key="target_input"
        )

    with col2:
        st.write("")
        st.write("")

        if st.session_state.processing:
            st.button("Investigation in progress...", disabled=True, use_container_width=True, key="processing_btn")
        else:
            st.button(
                "Start Investigation",
                type="primary",
                use_container_width=True,
                on_click=start_investigation,
                key="start_btn",
            )

    # Processing Logic
    if st.session_state.processing:
        target_val = st.session_state.target_input

        if not target_val or not target_val.strip():
            st.error("Please enter a valid target.")
            st.session_state.processing = False
            time.sleep(1)
            st.rerun()
        else:
            status_container = st.empty()
            logs_expander = st.expander("Investigation Logs", expanded=True)
            log_placeholder = logs_expander.empty()

            st_handler = StreamlitLogHandler(log_placeholder)
            root_logger = logging.getLogger()
            root_logger.addHandler(st_handler)
            root_logger.setLevel(logging.INFO)

            try:
                with st.spinner(f"Investigating '{target_val}'..."):
                    status_container.info("Initializing workflow agents...")
                    app = create_workflow()

                    inputs = {"target": target_val, "config": config}
                    thread_config = {"configurable": {"thread_id": f"web_{int(time.time())}"}}

                    status_container.info("Running searches and analysis... (Parallel Execution)")

                    result = app.invoke(inputs, thread_config)

                    status_container.success("Investigation Complete!")

                    report_content = None
                    latest_file = None

                    # 1. Exact Name Match
                    normalized_target = target_val.replace(" ", "_")
                    search_pattern = f"reports/*{normalized_target}*.md"
                    list_of_files = glob.glob(search_pattern)

                    # 2. Fallback: Recent files
                    if not list_of_files:
                        all_reports = glob.glob("reports/*.md")
                        if all_reports:
                            newest_file = max(all_reports, key=os.path.getmtime)
                            if time.time() - os.path.getmtime(newest_file) < 120:
                                list_of_files = [newest_file]

                    if list_of_files:
                        latest_file = max(list_of_files, key=os.path.getctime)
                        with open(latest_file, "r", encoding="utf-8") as f:
                            report_content = f.read()
                    elif "messages" in result and result["messages"]:
                        report_content = result["messages"][-1].content
                    else:
                        report_content = "### Report Not Found\nCould not locate the generated report file or message content. Please check the logs."

                    st.session_state.report_content = report_content
                    st.session_state.latest_report_file = latest_file

            except Exception:
                import traceback

                error_details = traceback.format_exc()
                st.session_state.report_content = (
                    f"### Error\nAn error occurred during investigation:\n\n```\n{error_details}\n```"
                )
                st.error("An error occurred. Check the report section for details.")
            finally:
                root_logger.removeHandler(st_handler)
                st.session_state.processing = False
                st.rerun()

    # Result Display (Persistent)
    if st.session_state.report_content:
        st.divider()
        st.subheader("Investigation Report")
        st.markdown(st.session_state.report_content)

        if st.session_state.latest_report_file:
            file_name_dl = os.path.basename(st.session_state.latest_report_file)
        else:
            file_name_dl = "report.md"

        st.download_button(
            label="Download Report", data=st.session_state.report_content, file_name=file_name_dl, mime="text/markdown"
        )


if __name__ == "__main__":
    main()
