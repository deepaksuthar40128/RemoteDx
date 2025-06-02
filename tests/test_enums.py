import unittest
from diagnostics.enums import MachineType

class TestMachineTypeEnum(unittest.TestCase):

    def test_from_string_valid(self):
        self.assertEqual(MachineType.from_string("live"), MachineType.LIVE)
        self.assertEqual(MachineType.from_string("Live"), MachineType.LIVE) 
        self.assertEqual(MachineType.from_string("DEV"), MachineType.DEV)
        self.assertEqual(MachineType.from_string("test"), MachineType.TEST)

    def test_from_string_invalid(self):
        with self.assertRaises(ValueError) as cm:
            MachineType.from_string("unknown")
        self.assertIn("'unknown' is not a valid MachineType", str(cm.exception))
        self.assertIn("live, dev, test", str(cm.exception))

        with self.assertRaises(ValueError): 
            MachineType.from_string("")

        with self.assertRaises(TypeError): 
            MachineType.from_string(None) 

    def test_str_representation(self):
        self.assertEqual(str(MachineType.LIVE), "live")
        self.assertEqual(str(MachineType.DEV), "dev")
        self.assertEqual(str(MachineType.TEST), "test")

if __name__ == '__main__':
    unittest.main()