import unittest
import asyncio
from unittest.mock import patch, AsyncMock

from diagnostics.machine import Machine, LiveMachine, DevMachine, TestMachine
from diagnostics.enums import MachineType
from diagnostics.decorators import DEFAULT_RETRY_DELAY_SECONDS

class TestDiagnosticChecks(unittest.TestCase):

    def setUp(self):
        self.base_machine = TestMachine( 
            name="test-machine",
            ip_address="127.0.0.1",
            expected_software=["python3==3.9.0", "nginx"]
        )
        self.live_machine_for_clock_test = LiveMachine( 
            name="live-clock-test",
            ip_address="127.0.0.2",
            expected_software=[]
        )

    @patch('diagnostics.machine.random.uniform')
    @patch('diagnostics.machine.random.random')
    @patch('diagnostics.machine.asyncio.sleep', new_callable=AsyncMock)
    @patch('diagnostics.decorators.asyncio.sleep', new_callable=AsyncMock)
    def test_ping_check_passed(self, mock_decorator_asyncio_sleep, mock_machine_asyncio_sleep, mock_random_random, mock_random_uniform):
        mock_random_uniform.return_value = 50.0
        mock_random_random.return_value = 0.5 

        result = asyncio.run(self.base_machine.ping_check())

        self.assertEqual(result['status'], "passed")
        self.assertIn("Latency 50.00ms", result['details'])
        self.assertEqual(result['check'], "ping_check")
        mock_machine_asyncio_sleep.assert_called_once_with(50.0 / 1000.0)
        mock_decorator_asyncio_sleep.assert_not_called()

@patch('diagnostics.machine.random.uniform')
@patch('diagnostics.machine.random.random')
@patch('diagnostics.machine.asyncio.sleep', new_callable=AsyncMock)
@patch('diagnostics.decorators.asyncio.sleep', new_callable=AsyncMock)
def test_ping_check_failed_high_latency(self, mock_decorator_retry_sleep, mock_ping_check_internal_sleep, mock_random_random, mock_random_uniform):
    self.assertIsNot(mock_ping_check_internal_sleep, mock_decorator_retry_sleep, "Mocks for asyncio.sleep are the same object!")
    
    uniform_call_count = 0
    def mock_uniform_func(a, b):
        nonlocal uniform_call_count
        uniform_call_count += 1
        return 250.0 + uniform_call_count
    
    mock_random_uniform.side_effect = mock_uniform_func
    mock_random_random.return_value = 0.5
    
    result = asyncio.run(TestMachine(
        name="test-machine",
        ip_address="127.0.0.1",
        expected_software=["python3==3.9.0", "nginx"]).ping_check())
    
    assert result['status'] == "failed"
    assert "exceeded threshold" in result['details']
    
    assert mock_ping_check_internal_sleep.call_count >= 1
    
    if mock_decorator_retry_sleep.call_count > 0:
        mock_decorator_retry_sleep.assert_called_with(DEFAULT_RETRY_DELAY_SECONDS)

@patch('diagnostics.machine.random.uniform')
@patch('diagnostics.machine.random.random')
@patch('diagnostics.machine.asyncio.sleep', new_callable=AsyncMock)
@patch('diagnostics.decorators.asyncio.sleep', new_callable=AsyncMock)
def test_ping_check_failed_packet_loss(self, mock_decorator_asyncio_sleep, mock_machine_asyncio_sleep, mock_random_random, mock_random_uniform):
    mock_random_uniform.return_value = 50.0
    mock_random_random.return_value = 0.05
    
    result = asyncio.run(TestMachine(
        name="test-machine",
        ip_address="127.0.0.1",
        expected_software=["python3==3.9.0", "nginx"]).ping_check())
    
    assert result['status'] == "failed"
    assert "Packet loss simulated" in result['details']
    assert "50.00ms" in result['details']
    
    assert mock_machine_asyncio_sleep.call_count >= 1
    
    if mock_decorator_asyncio_sleep.call_count > 0:
        mock_decorator_asyncio_sleep.assert_called_with(DEFAULT_RETRY_DELAY_SECONDS)

@patch('diagnostics.machine.time.sleep')
@patch('diagnostics.decorators.time.sleep')
@patch('diagnostics.machine.random.uniform')
def test_clock_sync_check_failed_high_drift(self, mock_rand_uniform_in_machine, mock_sleep_in_decorator, mock_sleep_in_machine):
    local_live_machine = LiveMachine(
        name="local-live-clock-test",
        ip_address="127.0.0.3",
        expected_software=[]
    )
    
    uniform_call_count = 0
    def mock_uniform_func(a, b):
        nonlocal uniform_call_count
        uniform_call_count += 1
        if uniform_call_count % 2 == 1:
            return 0.05
        else:
            return -2.5
    
    mock_rand_uniform_in_machine.side_effect = mock_uniform_func
    
    result = local_live_machine.clock_sync_check()
    
    assert result['status'] == "failed"
    assert "Drift -2.50s" in result['details']
    assert f"threshold {local_live_machine.CLOCK_DRIFT_THRESHOLD_SECONDS}s" in result['details']
    
    assert mock_sleep_in_machine.call_count >= 1
    
    if mock_sleep_in_decorator.call_count > 0:
        mock_sleep_in_decorator.assert_called_with(DEFAULT_RETRY_DELAY_SECONDS)

@patch('diagnostics.machine.time.sleep')
@patch('diagnostics.decorators.time.sleep')
@patch('diagnostics.machine.random.uniform')
def test_clock_sync_check_drift_override_testmachine(self, mock_rand_uniform_in_machine, mock_sleep_in_decorator, mock_sleep_in_machine):
    test_m = TestMachine(
        name="test-machine",
        ip_address="127.0.0.1",
        expected_software=["python3==3.9.0", "nginx"]
    )
    
    uniform_call_count = 0
    def mock_uniform_func(a, b):
        nonlocal uniform_call_count
        uniform_call_count += 1
        if uniform_call_count % 2 == 1:
            return 0.05
        else:
            return 10.0 + (uniform_call_count // 2)
    
    mock_rand_uniform_in_machine.side_effect = mock_uniform_func
    
    result = test_m.clock_sync_check()
    
    assert result['status'] == "failed"
    assert "Drift" in result['details']
    assert f"threshold {test_m.CLOCK_DRIFT_THRESHOLD_SECONDS}s" in result['details']
    
    assert mock_sleep_in_machine.call_count >= 1
    
    if mock_sleep_in_decorator.call_count > 0:
        mock_sleep_in_decorator.assert_called_with(DEFAULT_RETRY_DELAY_SECONDS)

@patch('diagnostics.machine.time.sleep')
@patch('diagnostics.decorators.time.sleep')
@patch('diagnostics.machine.random.uniform')
def test_clock_sync_check_failed_high_drift_force_retry(self, mock_rand_uniform_in_machine, mock_sleep_in_decorator, mock_sleep_in_machine):
    local_live_machine = LiveMachine(
        name="local-live-clock-test",
        ip_address="127.0.0.3",
        expected_software=[]
    )
    
    uniform_call_count = 0
    def mock_uniform_func(a, b):
        nonlocal uniform_call_count
        uniform_call_count += 1
        if uniform_call_count % 2 == 1:
            return 0.05
        else:
            attempt_num = (uniform_call_count // 2)
            return -2.5 - (attempt_num * 0.1)
    
    mock_rand_uniform_in_machine.side_effect = mock_uniform_func
    
    result = local_live_machine.clock_sync_check()
    
    assert result['status'] == "failed"
    assert "Drift" in result['details']

@patch('diagnostics.machine.random.uniform')
@patch('diagnostics.machine.random.random')
@patch('diagnostics.machine.asyncio.sleep', new_callable=AsyncMock)
@patch('diagnostics.decorators.asyncio.sleep', new_callable=AsyncMock)
def test_ping_check_failed_high_latency_simplified(self, mock_decorator_retry_sleep, mock_ping_check_internal_sleep, mock_random_random, mock_random_uniform):
    mock_random_uniform.return_value = 250.0
    mock_random_random.return_value = 0.5
    
    result = asyncio.run(TestMachine(
        name="test-machine",
        ip_address="127.0.0.1",
        expected_software=["python3==3.9.0", "nginx"]).ping_check())
    
    assert result['status'] == "failed"
    assert "exceeded threshold" in result['details']
    assert "250.00ms" in result['details']
    
    assert mock_ping_check_internal_sleep.call_count > 0

if __name__ == '__main__':
    unittest.main()
