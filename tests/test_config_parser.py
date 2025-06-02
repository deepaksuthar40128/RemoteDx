import unittest
import json
import tempfile
import os
from pathlib import Path
from typing import Any

from diagnostics.config_parser import parse_machine_configs_from_file, ConfigParseError
from diagnostics.enums import MachineType

class TestConfigParser(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

    def _create_temp_json_file(self, content: Any, filename_suffix: str = ".json") -> Path:
        temp_file_path = Path(self.test_dir.name) / f"test_config_{os.urandom(4).hex()}{filename_suffix}"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f)
        return temp_file_path

    def test_parse_valid_config(self):
        valid_data = [
            {
                "name": "alpha", "ip_address": "1.1.1.1", "machine_type": "live",
                "expected_software": ["nginx==1.0", "python"]
            },
            {
                "name": "beta", "ip_address": "2.2.2.2", "machine_type": "DEV",
                "expected_software": []
            }
        ]
        temp_file = self._create_temp_json_file(valid_data)
        configs = parse_machine_configs_from_file(temp_file)

        self.assertEqual(len(configs), 2)
        self.assertEqual(configs[0]["name"], "alpha")
        self.assertEqual(configs[0]["ip_address"], "1.1.1.1")
        self.assertEqual(configs[0]["machine_type"], MachineType.LIVE)
        self.assertEqual(configs[0]["expected_software"], ["nginx==1.0", "python"])
        self.assertEqual(configs[1]["machine_type"], MachineType.DEV)
        self.assertEqual(configs[1]["expected_software"], [])

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            parse_machine_configs_from_file("non_existent_file.json")

    def test_malformed_json(self):
        malformed_content = "[{'name': 'bad'}]"
        temp_file_path = Path(self.test_dir.name) / "malformed.json"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            f.write(malformed_content)
        with self.assertRaisesRegex(ConfigParseError, "Invalid JSON"):
            parse_machine_configs_from_file(temp_file_path)

    def test_not_a_list(self):
        data = {"name": "not_a_list"}
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "must be a JSON list"):
            parse_machine_configs_from_file(temp_file)

    def test_entry_not_a_dict(self):
        data = ["not_a_dict_entry"]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "not a dictionary"):
            parse_machine_configs_from_file(temp_file)

    def test_missing_name(self):
        data = [{"ip_address": "1.1.1.1", "machine_type": "live", "expected_software": []}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "'name' is missing"):
            parse_machine_configs_from_file(temp_file)

    def test_invalid_name_type(self):
        data = [{"name": 123, "ip_address": "1.1.1.1", "machine_type": "live", "expected_software": []}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "'name' is missing, not a string, or empty"):
            parse_machine_configs_from_file(temp_file)

    def test_missing_ip_address(self):
        data = [{"name": "alpha", "machine_type": "live", "expected_software": []}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "'ip_address' is missing"):
            parse_machine_configs_from_file(temp_file)

    def test_missing_machine_type(self):
        data = [{"name": "alpha", "ip_address": "1.1.1.1", "expected_software": []}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "'machine_type' is missing"):
            parse_machine_configs_from_file(temp_file)

    def test_invalid_machine_type_value(self):
        data = [{"name": "alpha", "ip_address": "1.1.1.1", "machine_type": "superlive", "expected_software": []}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "Invalid 'machine_type'.*not a valid MachineType"):
            parse_machine_configs_from_file(temp_file)

    def test_missing_expected_software(self):
        data = [{"name": "alpha", "ip_address": "1.1.1.1", "machine_type": "live"}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "'expected_software' is missing or not a list"):
            parse_machine_configs_from_file(temp_file)

    def test_invalid_expected_software_type(self):
        data = [{"name": "alpha", "ip_address": "1.1.1.1", "machine_type": "live", "expected_software": "not_a_list"}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "'expected_software' is missing or not a list"):
            parse_machine_configs_from_file(temp_file)

    def test_invalid_item_in_expected_software(self):
        data = [{"name": "alpha", "ip_address": "1.1.1.1", "machine_type": "live", "expected_software": ["valid_string", 123]}]
        temp_file = self._create_temp_json_file(data)
        with self.assertRaisesRegex(ConfigParseError, "items in 'expected_software' must be strings"):
            parse_machine_configs_from_file(temp_file)

    def test_empty_config_file(self):
        temp_file = self._create_temp_json_file([])
        configs = parse_machine_configs_from_file(temp_file)
        self.assertEqual(len(configs), 0)

if __name__ == '__main__':
    unittest.main()
