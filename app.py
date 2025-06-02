import streamlit as st
import json
import pandas as pd
import asyncio
from typing import List

from diagnostics.config_parser import parse_machine_configs_from_file, ConfigParseError
from diagnostics.machine import Machine, create_machine
from diagnostics.enums import MachineType

def results_to_dataframe(machines: List[Machine]) -> pd.DataFrame:
    all_check_results = []
    for machine in machines:
        for check_result in machine.diagnostic_results:
            row = {
                "Machine Name": machine.name,
                "IP Address": machine.ip_address,
                "Machine Type": str(machine.machine_type),
                "Check Name": check_result.get('check'),
                "Status": check_result.get('status'),
                "Duration (s)": f"{check_result.get('duration_sec', 0):.3f}",
                "Details": check_result.get('details'),
                "Commands Run": ", ".join(check_result.get('commands_run', [])),
                "Attempts": check_result.get('attempts')
            }
            all_check_results.append(row)

    if not all_check_results:
        return pd.DataFrame()
    return pd.DataFrame(all_check_results)

async def run_diagnostics_on_machines(machine_instances: List[Machine]):
    async def run_single(machine):
        await machine.run_diagnostics()

    diagnostic_tasks = [run_single(machine) for machine in machine_instances]
    await asyncio.gather(*diagnostic_tasks)

st.set_page_config(layout="wide")
st.title("Remote Diagnostics Automation Tool")

st.sidebar.header("1. Upload Configuration")
uploaded_file = st.sidebar.file_uploader("Choose a machine configuration JSON file", type=["json"])

if 'diagnostic_machines' not in st.session_state:
    st.session_state.diagnostic_machines = None
if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""

if uploaded_file is not None:
    try:
        file_content = uploaded_file.getvalue().decode("utf-8")
        raw_json_data = json.loads(file_content)

        with open("temp_config.json", "w", encoding="utf-8") as f:
            f.write(file_content)

        raw_configs = parse_machine_configs_from_file("temp_config.json")
        st.session_state.error_message = ""

        machines_to_diagnose: List[Machine] = []
        for conf in raw_configs:
            try:
                machine_instance = create_machine(conf)
                machines_to_diagnose.append(machine_instance)
            except ValueError as e_create:
                st.sidebar.error(f"Error creating machine from config: {conf.get('name', 'N/A')}: {e_create}")

        st.session_state.diagnostic_machines = machines_to_diagnose
        st.sidebar.success(f"Successfully loaded and parsed {len(machines_to_diagnose)} machine configurations.")
        st.sidebar.markdown("---")

    except json.JSONDecodeError as e:
        st.session_state.error_message = f"Error decoding JSON: {e}"
        st.session_state.diagnostic_machines = None
    except ConfigParseError as e:
        st.session_state.error_message = f"Configuration Parse Error: {e}"
        st.session_state.diagnostic_machines = None
    except FileNotFoundError as e:
        st.session_state.error_message = f"File Error: {e}"
        st.session_state.diagnostic_machines = None
    except Exception as e:
        st.session_state.error_message = f"An unexpected error occurred loading config: {e}"
        st.session_state.diagnostic_machines = None

if st.session_state.error_message:
    st.error(st.session_state.error_message)

if st.session_state.diagnostic_machines:
    st.sidebar.header("2. Run Diagnostics")
    if st.sidebar.button("Start Diagnostics"):
        if st.session_state.diagnostic_machines:
            with st.spinner("Running diagnostics on all machines... Please wait."):
                try:
                    asyncio.run(run_diagnostics_on_machines(st.session_state.diagnostic_machines))
                    st.session_state.results_df = results_to_dataframe(st.session_state.diagnostic_machines)
                    st.session_state.error_message = ""
                    st.success("Diagnostics complete!")
                except Exception as e_run:
                    st.session_state.error_message = f"Error during diagnostics run: {e_run}"
                    st.session_state.results_df = pd.DataFrame()
                    st.error(st.session_state.error_message)
        else:
            st.sidebar.warning("No machine configurations loaded to run diagnostics.")
    st.sidebar.markdown("---")

if not st.session_state.results_df.empty:
    st.header("Diagnostic Results")
    st.dataframe(st.session_state.results_df, use_container_width=True)

    st.header("Export Results")
    csv_data = st.session_state.results_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Results as CSV",
        data=csv_data,
        file_name="diagnostics_report_streamlit.csv",
        mime="text/csv",
    )
elif st.session_state.diagnostic_machines and not st.session_state.error_message:
    st.info("Diagnostics results will appear here after running the checks.")
elif not st.session_state.diagnostic_machines and not uploaded_file and not st.session_state.error_message:
    st.info("Please upload a machine configuration JSON file using the sidebar to begin.")
