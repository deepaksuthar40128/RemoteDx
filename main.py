import sys
import asyncio
import csv 
from pathlib import Path
from typing import List, Dict, Any, Union

from diagnostics.config_parser import parse_machine_configs_from_file, ConfigParseError
from diagnostics.machine import Machine, create_machine

async def run_single_machine_diagnostics(machine: Machine):
    print(f"\n--- Diagnostics for {machine.name} ({machine.ip_address}) ---")
    await machine.run_diagnostics()


def generate_summary_report(machines: List[Machine]) -> str:
    report_lines = ["\n--- Final Diagnostics Summary Report ---"]
    overall_total_checks = 0
    overall_total_passed = 0
    overall_total_failed = 0

    for machine in machines:
        total_checks = len(machine.diagnostic_results)
        passed_checks = sum(1 for r in machine.diagnostic_results if r['status'] == 'passed')
        failed_checks = total_checks - passed_checks

        overall_total_checks += total_checks
        overall_total_passed += passed_checks
        overall_total_failed += failed_checks

        report_lines.append(f"\nMachine: {machine.name} ({machine.ip_address}) - Type: {machine.machine_type}")
        report_lines.append(f"  Total Checks: {total_checks}")
        report_lines.append(f"  Passed: {passed_checks}")
        report_lines.append(f"  Failed: {failed_checks}")
        if failed_checks > 0:
            report_lines.append("  Failed Check Details:")
            for result in machine.diagnostic_results:
                if result['status'] != 'passed':
                    report_lines.append(
                        f"    - {result['check']}: {result['status']} ({result['details']}) "
                        f"[Attempts: {result.get('attempts', 1)}]"
                    )
    
    report_lines.append("\n--- Overall Summary ---")
    report_lines.append(f"Total Machines Processed: {len(machines)}")
    report_lines.append(f"Overall Total Checks Performed: {overall_total_checks}")
    report_lines.append(f"Overall Checks Passed: {overall_total_passed}")
    report_lines.append(f"Overall Checks Failed (or Errored): {overall_total_failed}")
    
    if overall_total_checks > 0:
        pass_rate = (overall_total_passed / overall_total_checks) * 100
        report_lines.append(f"Overall Pass Rate: {pass_rate:.2f}%")

    return "\n".join(report_lines)


def export_results_to_csv(machines: List[Machine], filepath: Union[str, Path]):
    path_obj = Path(filepath)
    detailed_results: List[Dict[str, Any]] = []

    for machine in machines:
        for check_result in machine.diagnostic_results:
            # Flatten the result for CSV, adding machine info
            row = {
                "machine_name": machine.name,
                "machine_ip": machine.ip_address,
                "machine_type": str(machine.machine_type), # Convert enum to string
                "check_name": check_result.get('check'),
                "status": check_result.get('status'),
                "duration_sec": check_result.get('duration_sec'),
                "details": check_result.get('details'),
                "commands_run": ", ".join(check_result.get('commands_run', [])), # Join list to string
                "attempts": check_result.get('attempts')
            }
            detailed_results.append(row)

    if not detailed_results:
        print("No detailed results to export to CSV.")
        return

    headers = [
        "machine_name", "machine_ip", "machine_type", "check_name", 
        "status", "duration_sec", "details", "commands_run", "attempts"
    ]
    
    try:
        with open(path_obj, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(detailed_results)
        print(f"\nSuccessfully exported detailed results to: {path_obj.resolve()}")
    except IOError as e:
        print(f"Error exporting results to CSV '{path_obj}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV export: {e}")


async def main_async():
    project_root = Path(__file__).parent
    config_file = project_root / "machines.json"
    csv_output_file = project_root / "diagnostics_report.csv"

    print("--- Remote Diagnostics Automation (Async) ---")
    print(f"\nLoading configurations from: {config_file}...")
    try:
        raw_configs = parse_machine_configs_from_file(config_file)
        print(f"Successfully parsed {len(raw_configs)} machine configurations.")
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at '{config_file}'. Exiting.")
        sys.exit(1)
    except ConfigParseError as e:
        print(f"ERROR: Could not parse configuration file: {e}. Exiting.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during parsing: {e}. Exiting.")
        sys.exit(1)

    if not raw_configs:
        print("No machine configurations found. Nothing to do. Exiting.")
        sys.exit(0)


    machines: list[Machine] = []
    for i, conf in enumerate(raw_configs):
        try:
            machine_instance = create_machine(conf)
            machines.append(machine_instance)
            print(f"  Initialized: {machine_instance.name} ({type(machine_instance).__name__})")
        except ValueError as e:
            print(f"  ERROR creating machine from config {i+1} ({conf.get('name', 'N/A')}): {e}. Skipping.")
        except Exception as e:
            print(f"  UNEXPECTED ERROR creating machine from config {i+1} ({conf.get('name', 'N/A')}): {e}. Skipping.")

    if not machines:
        print("No machine instances were successfully created. Exiting.")
        sys.exit(0)


    print("\nRunning diagnostics concurrently (intermediate output may be interleaved)...")
    diagnostic_tasks = [run_single_machine_diagnostics(machine) for machine in machines]
    await asyncio.gather(*diagnostic_tasks)
    print("\n--- All Individual Machine Diagnostics Complete ---")

    summary_output = generate_summary_report(machines)
    print(summary_output)

    export_results_to_csv(machines, csv_output_file)

    print("\n--- Diagnostics Run Fully Complete ---")


if __name__ == "__main__":
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nDiagnostics run interrupted by user.")
    except Exception as e:
        print(f"An unexpected critical error occurred in the async event loop: {e}")