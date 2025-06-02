import json
from typing import List, Dict, Any, Union
from pathlib import Path
from .enums import MachineType

ValidatedMachineConfig = Dict[str, Union[str, MachineType, List[str]]]


class ConfigParseError(ValueError):
    pass


def _validate_machine_entry(entry: Dict[str, Any], index: int) -> ValidatedMachineConfig:
    if not isinstance(entry, dict):
        raise ConfigParseError(f"Machine entry at index {index} is not a dictionary.")

    name = entry.get("name")
    if not name or not isinstance(name, str) or not name.strip():
        raise ConfigParseError(
            f"Machine entry at index {index}: 'name' is missing, not a string, or empty."
        )
    name = name.strip()

    ip_address = entry.get("ip_address")
    if not ip_address or not isinstance(ip_address, str) or not ip_address.strip():
        raise ConfigParseError(
            f"Machine '{name}' (index {index}): 'ip_address' is missing, not a string, or empty."
        )
    ip_address = ip_address.strip()

    machine_type_str = entry.get("machine_type")
    if not machine_type_str or not isinstance(machine_type_str, str) or not machine_type_str.strip():
        raise ConfigParseError(
            f"Machine '{name}' (index {index}): 'machine_type' is missing, not a string, or empty."
        )
    try:
        machine_type_enum = MachineType.from_string(machine_type_str.strip())
    except ValueError as e:
        raise ConfigParseError(f"Machine '{name}' (index {index}): Invalid 'machine_type'. {e}")

    expected_software = entry.get("expected_software")
    if expected_software is None or not isinstance(expected_software, list):
        raise ConfigParseError(
            f"Machine '{name}' (index {index}): 'expected_software' is missing or not a list."
        )
    if not all(isinstance(s, str) for s in expected_software):
        raise ConfigParseError(
            f"Machine '{name}' (index {index}): All items in 'expected_software' must be strings."
        )

    return {
        "name": name,
        "ip_address": ip_address,
        "machine_type": machine_type_enum,
        "expected_software": expected_software
    }


def parse_machine_configs_from_file(filepath: Union[str, Path]) -> List[ValidatedMachineConfig]:
    path_obj = Path(filepath)
    if not path_obj.is_file():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")

    try:
        with open(path_obj, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigParseError(f"Invalid JSON in configuration file '{filepath}': {e}")
    except Exception as e:
        raise ConfigParseError(f"Could not read configuration file '{filepath}': {e}")

    if not isinstance(data, list):
        raise ConfigParseError(
            f"Configuration file '{filepath}' content must be a JSON list of machine objects."
        )

    validated_configs = []
    for i, entry_data in enumerate(data):
        try:
            validated_entry = _validate_machine_entry(entry_data, i)
            validated_configs.append(validated_entry)
        except ConfigParseError as e:
            raise ConfigParseError(f"Error parsing entry at index {i} in '{filepath}': {e}")

    return validated_configs
