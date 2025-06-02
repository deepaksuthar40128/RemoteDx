import unittest
from typing import List, Dict, Any

from diagnostics.machine import Machine, LiveMachine, DevMachine, TestMachine, create_machine
from diagnostics.enums import MachineType
from diagnostics.config_parser import ValidatedMachineConfig

class TestMachineClasses(unittest.TestCase):

    def test_machine_creation_valid(self):
        machine = Machine(
            name="test-host",
            ip_address="192.168.1.10",
            machine_type=MachineType.TEST,
            expected_software=["app1", "app2==1.0"]
        )
        self.assertEqual(machine.name, "test-host")
        self.assertEqual(machine.ip_address, "192.168.1.10")
        self.assertEqual(machine.machine_type, MachineType.TEST)
        self.assertEqual(machine.expected_software, ["app1", "app2==1.0"])
        self.assertIsInstance(machine.diagnostic_results, list)
        self.assertEqual(len(machine.diagnostic_results), 0)
        self.assertTrue(hasattr(machine, '_simulated_installed_sw'))
        self.assertIsInstance(machine._simulated_installed_sw, dict)

    def test_machine_creation_invalid_inputs(self):
        with self.assertRaisesRegex(ValueError, "Machine name must be a non-empty string"):
            Machine("", "1.1.1.1", MachineType.LIVE, [])
        with self.assertRaisesRegex(ValueError, "Machine IP address must be a non-empty string"):
            Machine("host", "", MachineType.LIVE, [])
        with self.assertRaisesRegex(ValueError, "Machine type must be an instance of MachineType enum"):
            Machine("host", "1.1.1.1", "live", []) # type: ignore
        with self.assertRaisesRegex(ValueError, "Expected software must be a list of strings"):
            Machine("host", "1.1.1.1", MachineType.LIVE, "not_a_list") # type: ignore
        with self.assertRaisesRegex(ValueError, "Expected software must be a list of strings"):
            Machine("host", "1.1.1.1", MachineType.LIVE, [123]) # type: ignore

    def test_live_machine_creation(self):
        live_machine = LiveMachine(name="live-srv", ip_address="10.0.0.1", expected_software=["nginx"])
        self.assertIsInstance(live_machine, LiveMachine)
        self.assertIsInstance(live_machine, Machine)
        self.assertEqual(live_machine.name, "live-srv")
        self.assertEqual(live_machine.machine_type, MachineType.LIVE)

    def test_dev_machine_creation(self):
        dev_machine = DevMachine(name="dev-box", ip_address="10.0.1.1", expected_software=["docker"])
        self.assertIsInstance(dev_machine, DevMachine)
        self.assertEqual(dev_machine.name, "dev-box")
        self.assertEqual(dev_machine.machine_type, MachineType.DEV)
        self.assertEqual(dev_machine.DEV_CLOCK_DRIFT_MIN_SECONDS, -7.0)

    def test_test_machine_creation(self):
        test_machine = TestMachine(name="test-rig", ip_address="10.0.2.1", expected_software=["my_app"])
        self.assertIsInstance(test_machine, TestMachine)
        self.assertEqual(test_machine.name, "test-rig")
        self.assertEqual(test_machine.machine_type, MachineType.TEST)
        self.assertEqual(test_machine.TEST_CLOCK_DRIFT_MIN_SECONDS, -15.0)

    def test_create_machine_factory_valid(self):
        live_config: ValidatedMachineConfig = {
            "name": "factory-live", "ip_address": "3.3.3.1",
            "machine_type": MachineType.LIVE, "expected_software": ["sw_a"]
        }
        dev_config: ValidatedMachineConfig = {
            "name": "factory-dev", "ip_address": "3.3.3.2",
            "machine_type": MachineType.DEV, "expected_software": ["sw_b"]
        }
        test_config: ValidatedMachineConfig = {
            "name": "factory-test", "ip_address": "3.3.3.3",
            "machine_type": MachineType.TEST, "expected_software": ["sw_c"]
        }

        live_instance = create_machine(live_config)
        self.assertIsInstance(live_instance, LiveMachine)
        self.assertEqual(live_instance.name, "factory-live")

        dev_instance = create_machine(dev_config)
        self.assertIsInstance(dev_instance, DevMachine)
        self.assertEqual(dev_instance.name, "factory-dev")

        test_instance = create_machine(test_config)
        self.assertIsInstance(test_instance, TestMachine)
        self.assertEqual(test_instance.name, "factory-test")

    def test_create_machine_factory_invalid_config(self):
        invalid_config1: Dict[str, Any] = {
            "ip_address": "4.4.4.1", "machine_type": MachineType.LIVE, "expected_software": []
        }
        with self.assertRaisesRegex(ValueError, "Invalid configuration provided to create_machine"):
            create_machine(invalid_config1)

        invalid_config2: Dict[str, Any] = {
            "name": "factory-badtype", "ip_address": "4.4.4.2",
            "machine_type": "superlive", "expected_software": [] # type: ignore
        }
        with self.assertRaisesRegex(ValueError, "Invalid configuration provided to create_machine"):
            create_machine(invalid_config2)

    def test_machine_str_repr(self):
        machine = Machine("repr-test", "5.5.5.5", MachineType.TEST, ["tool"])
        actual_string_output = str(machine)
        self.assertIn("Machine(name='repr-test'", actual_string_output)
        self.assertIn("Machine(name='repr-test'", str(machine))
        self.assertIn("ip='5.5.5.5'", str(machine))
        self.assertIn("type='test'", str(machine))
        self.assertIn("expected_sw_count=1", str(machine))

        expected_repr = "Machine(name='repr-test', ip_address='5.5.5.5', machine_type=<MachineType.TEST: 'test'>, expected_software=['tool'])"
        actual_repr = repr(machine)
        self.assertTrue(actual_repr.startswith("Machine(name='repr-test'"))
        self.assertIn("machine_type=MachineType.TEST", actual_repr.replace("<MachineType.TEST: 'test'>", "MachineType.TEST"))


if __name__ == '__main__':
    unittest.main()
