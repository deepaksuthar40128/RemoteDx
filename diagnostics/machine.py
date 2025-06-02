import asyncio
import random
import time
from typing import List, Dict, Any, Tuple, Optional

from .enums import MachineType
from .decorators import diagnostic_test

CheckResult = Dict[str, Any]

def _parse_version_string(version_str: str) -> Tuple[int, ...]:
    try:
        return tuple(map(int, version_str.split('.')))
    except ValueError:
        return (0,)

def _compare_versions(installed_version_str: str, expected_version_str: str) -> bool:
    installed_v = _parse_version_string(installed_version_str)
    expected_v = _parse_version_string(expected_version_str)
    return installed_v >= expected_v

def _parse_software_string(software_entry: str) -> Tuple[str, Optional[str]]:
    if '==' in software_entry:
        name, version = software_entry.split('==', 1)
        return name.strip(), version.strip()
    return software_entry.strip(), None

class Machine:
    PING_LATENCY_MIN_MS = 0
    PING_LATENCY_MAX_MS = 300
    PING_LATENCY_THRESHOLD_MS = 200
    PING_PACKET_LOSS_CHANCE = 0.1
    CLOCK_DRIFT_THRESHOLD_SECONDS = 1.5
    DEFAULT_CLOCK_DRIFT_MIN_SECONDS = -5.0
    DEFAULT_CLOCK_DRIFT_MAX_SECONDS = 5.0
    SIMULATED_INSTALLED_SOFTWARE_POOL = {
        "nginx": ["1.18.0", "1.20.1", "1.21.0"],
        "python3": ["3.7.9", "3.8.5", "3.9.7", "3.10.4"],
        "curl": ["7.68.0", "7.74.0"],
        "docker": ["20.10.7", "20.10.12"],
        "gcc": ["9.3.0", "10.2.0"],
        "node": ["14.17.0", "16.13.0", "17.0.1"],
        "java11": ["11.0.10", "11.0.12"], 
        "postgres": ["12.5", "13.1", "14.0"],
        "my_custom_app": ["1.0.0", "1.2.0", "1.2.3"]
    }

    def __init__(self, name: str, ip_address: str, machine_type: MachineType, expected_software: List[str]):
        if not name or not isinstance(name, str):
            raise ValueError("Machine name must be a non-empty string.")
        if not ip_address or not isinstance(ip_address, str): 
            raise ValueError("Machine IP address must be a non-empty string.")
        if not isinstance(machine_type, MachineType):
            raise ValueError("Machine type must be an instance of MachineType enum.")
        if not isinstance(expected_software, list) or not all(isinstance(s, str) for s in expected_software):
            raise ValueError("Expected software must be a list of strings.")

        self.name: str = name
        self.ip_address: str = ip_address
        self.machine_type: MachineType = machine_type
        self.expected_software: List[str] = expected_software
        self.diagnostic_results: List[CheckResult] = []
        self._simulated_installed_sw: Dict[str, str] = self._get_simulated_installed_software()

    def __str__(self) -> str:
        return (f"Machine(name='{self.name}', ip='{self.ip_address}', "
                f"type='{str(self.machine_type)}', expected_sw_count={len(self.expected_software)})")
    
    def __repr__(self) -> str:
        return (f"Machine(name={self.name!r}, ip_address={self.ip_address!r}, "
                f"machine_type={self.machine_type!r}, expected_software={self.expected_software!r})")

    def _get_simulated_installed_software(self) -> Dict[str, str]:
        installed = {}
        for sw_name, available_versions in self.SIMULATED_INSTALLED_SOFTWARE_POOL.items():
            if random.random() < 0.8: 
                if available_versions:
                    installed[sw_name] = random.choice(available_versions)
        return installed

    @diagnostic_test(check_name="ping_check", retry_on_failure=True)
    async def ping_check(self) -> Dict[str, Any]:
        response_time_ms = random.uniform(self.PING_LATENCY_MIN_MS, self.PING_LATENCY_MAX_MS)
        await asyncio.sleep(response_time_ms / 1000.0)
        commands_run = [f"ping -c 1 {self.ip_address}"]
        if random.random() < self.PING_PACKET_LOSS_CHANCE:
            return {
                "status": "failed",
                "details": f"Packet loss simulated. (Attempted latency: {response_time_ms:.2f}ms)",
                "commands_run": commands_run
            }
        if response_time_ms > self.PING_LATENCY_THRESHOLD_MS:
            return {
                "status": "failed",
                "details": f"Latency {response_time_ms:.2f}ms exceeded threshold of {self.PING_LATENCY_THRESHOLD_MS}ms.",
                "commands_run": commands_run
            }
        return {
            "status": "passed",
            "details": f"Latency {response_time_ms:.2f}ms.",
            "commands_run": commands_run
        }

    @diagnostic_test(check_name="software_version_check", retry_on_failure=False)
    def software_version_check(self) -> Dict[str, Any]:
        commands_run = ["dpkg-query -W -f='${Package}==${Version}\\n'"]
        issues_found: List[str] = []
        time.sleep(random.uniform(0.05, 0.2))

        if not self.expected_software:
            return {"status": "passed", "details": "No expected software.", "commands_run": commands_run}

        for expected_entry in self.expected_software:
            expected_name, expected_version = _parse_software_string(expected_entry)
            if expected_name not in self._simulated_installed_sw:
                issues_found.append(f"Missing: '{expected_name}'")
                continue
            installed_version_str = self._simulated_installed_sw[expected_name]
            if expected_version and not _compare_versions(installed_version_str, expected_version):
                issues_found.append(
                    f"Version Mismatch for '{expected_name}': Expected >='{expected_version}', Found '{installed_version_str}'."
                )
        
        if issues_found:
            return {"status": "failed", "details": "; ".join(issues_found), "commands_run": commands_run}
        return {"status": "passed", "details": "All expected software OK.", "commands_run": commands_run}

    def _get_drift_parameters(self) -> Tuple[float, float]:
        return self.DEFAULT_CLOCK_DRIFT_MIN_SECONDS, self.DEFAULT_CLOCK_DRIFT_MAX_SECONDS

    @diagnostic_test(check_name="clock_sync_check", retry_on_failure=True)
    def clock_sync_check(self) -> Dict[str, Any]:
        commands_run = ["date +%s", "ntpdate -q pool.ntp.org"]
        time.sleep(random.uniform(0.02, 0.1))

        drift_min, drift_max = self._get_drift_parameters()
        simulated_drift_seconds = random.uniform(drift_min, drift_max)
        abs_drift = abs(simulated_drift_seconds)

        if abs_drift > self.CLOCK_DRIFT_THRESHOLD_SECONDS:
            return {
                "status": "failed",
                "details": (f"Drift {simulated_drift_seconds:.2f}s (abs: {abs_drift:.2f}s) "
                            f"> threshold {self.CLOCK_DRIFT_THRESHOLD_SECONDS}s."),
                "commands_run": commands_run
            }
        
        return {
            "status": "passed",
            "details": f"Drift {simulated_drift_seconds:.2f}s (within threshold).",
            "commands_run": commands_run
        }

    async def run_diagnostics(self):
        print(f"Running generic diagnostics for {self.name} ({self.machine_type})...")
        self.diagnostic_results = []
        self.diagnostic_results.append(await self.ping_check())
        self.diagnostic_results.append(self.software_version_check())
        self.diagnostic_results.append(self.clock_sync_check())

class LiveMachine(Machine):
    def __init__(self, name: str, ip_address: str, expected_software: List[str]):
        super().__init__(name, ip_address, MachineType.LIVE, expected_software)

    async def run_diagnostics(self):
        print(f"Running LIVE-specific diagnostics for {self.name}...")
        await super().run_diagnostics()

class DevMachine(Machine):
    DEV_CLOCK_DRIFT_MIN_SECONDS = -7.0
    DEV_CLOCK_DRIFT_MAX_SECONDS = 7.0
    def __init__(self, name: str, ip_address: str, expected_software: List[str]):
        super().__init__(name, ip_address, MachineType.DEV, expected_software)
    def _get_drift_parameters(self) -> Tuple[float, float]:
        return self.DEV_CLOCK_DRIFT_MIN_SECONDS, self.DEV_CLOCK_DRIFT_MAX_SECONDS
    async def run_diagnostics(self):
        print(f"Running DEV-specific diagnostics for {self.name}...")
        await super().run_diagnostics()

class TestMachine(Machine):
    TEST_CLOCK_DRIFT_MIN_SECONDS = -15.0
    TEST_CLOCK_DRIFT_MAX_SECONDS = 15.0
    def __init__(self, name: str, ip_address: str, expected_software: List[str]):
        super().__init__(name, ip_address, MachineType.TEST, expected_software)
    def _get_drift_parameters(self) -> Tuple[float, float]:
        return self.TEST_CLOCK_DRIFT_MIN_SECONDS, self.TEST_CLOCK_DRIFT_MAX_SECONDS
    async def run_diagnostics(self):
        print(f"Running TEST-specific diagnostics for {self.name}...")
        await super().run_diagnostics()

def create_machine(config: Dict[str, Any]) -> Machine:
    name = config.get("name")
    ip_address = config.get("ip_address")
    machine_type_enum = config.get("machine_type")
    expected_software = config.get("expected_software")
    if not all([name, ip_address, isinstance(machine_type_enum, MachineType), isinstance(expected_software, list)]):
        raise ValueError(f"Invalid configuration provided to create_machine: {config}")
    if machine_type_enum == MachineType.LIVE:
        return LiveMachine(name, ip_address, expected_software)
    elif machine_type_enum == MachineType.DEV:
        return DevMachine(name, ip_address, expected_software)
    elif machine_type_enum == MachineType.TEST:
        return TestMachine(name, ip_address, expected_software)
    else:
        raise ValueError(f"Unknown machine type: {machine_type_enum}")
