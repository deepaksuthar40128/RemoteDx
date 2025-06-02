import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from diagnostics.decorators import diagnostic_test, DEFAULT_RETRY_DELAY_SECONDS
from diagnostics.machine import CheckResult

class TestDiagnosticDecorator(unittest.TestCase):

    def test_sync_func_pass_first_try(self):
        mock_sync_check_logic = Mock(return_value={"status": "passed", "details": "Sync OK"})
        
        @diagnostic_test(check_name="test_sync_pass", retry_on_failure=True)
        def decorated_sync_func(self_param):
            return mock_sync_check_logic()

        result = decorated_sync_func(None)

        self.assertEqual(result['check'], "test_sync_pass")
        self.assertEqual(result['status'], "passed")
        self.assertEqual(result['details'], "Sync OK")
        self.assertEqual(result['attempts'], 1)
        self.assertIsInstance(result['duration_sec'], float)
        self.assertGreaterEqual(result['duration_sec'], 0)
        mock_sync_check_logic.assert_called_once()

    @patch('diagnostics.decorators.time.sleep')
    def test_sync_func_fail_then_pass_on_retry(self, mock_decorator_sleep):
        mock_sync_check_logic = Mock(side_effect=[
            {"status": "failed", "details": "Sync failed initially"},
            {"status": "passed", "details": "Sync OK on retry"}
        ])

        @diagnostic_test(check_name="test_sync_retry_pass", retry_on_failure=True)
        def decorated_sync_func(self_param):
            return mock_sync_check_logic()

        result = decorated_sync_func(None)

        self.assertEqual(result['check'], "test_sync_retry_pass")
        self.assertEqual(result['status'], "passed")
        self.assertEqual(result['details'], "Sync OK on retry")
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(mock_sync_check_logic.call_count, 2)
        mock_decorator_sleep.assert_called_once_with(DEFAULT_RETRY_DELAY_SECONDS)

    @patch('diagnostics.decorators.time.sleep')
    def test_sync_func_fail_both_times_with_retry(self, mock_decorator_sleep):
        mock_sync_check_logic = Mock(return_value={"status": "failed", "details": "Sync always fails"})

        @diagnostic_test(check_name="test_sync_always_fail", retry_on_failure=True)
        def decorated_sync_func(self_param):
            return mock_sync_check_logic()

        result = decorated_sync_func(None)

        self.assertEqual(result['status'], "failed")
        self.assertEqual(result['details'], "Sync always fails")
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(mock_sync_check_logic.call_count, 2)
        mock_decorator_sleep.assert_called_once_with(DEFAULT_RETRY_DELAY_SECONDS)

    def test_sync_func_fail_no_retry_configured(self):
        mock_sync_check_logic = Mock(return_value={"status": "failed", "details": "Sync failed, no retry"})

        @diagnostic_test(check_name="test_sync_no_retry", retry_on_failure=False)
        def decorated_sync_func(self_param):
            return mock_sync_check_logic()

        result = decorated_sync_func(None)

        self.assertEqual(result['status'], "failed")
        self.assertEqual(result['attempts'], 1)
        mock_sync_check_logic.assert_called_once()

    def test_sync_func_raises_exception(self):
        mock_sync_check_logic = Mock(side_effect=ValueError("Sync Test Exception"))

        @diagnostic_test(check_name="test_sync_exception", retry_on_failure=False)
        def decorated_sync_func(self_param):
            return mock_sync_check_logic()

        result = decorated_sync_func(None)
        
        self.assertEqual(result['status'], "error")
        self.assertIn("ValueError", result['details'])
        self.assertIn("Sync Test Exception", result['details'])
        self.assertEqual(result['attempts'], 1)
        mock_sync_check_logic.assert_called_once()

    def test_async_func_pass_first_try(self):
        mock_async_check_logic = Mock(return_value={"status": "passed", "details": "Async OK"})

        @diagnostic_test(check_name="test_async_pass", retry_on_failure=True)
        async def decorated_async_func(self_param):
            return mock_async_check_logic()

        result = asyncio.run(decorated_async_func(None))

        self.assertEqual(result['check'], "test_async_pass")
        self.assertEqual(result['status'], "passed")
        self.assertEqual(result['details'], "Async OK")
        self.assertEqual(result['attempts'], 1)
        mock_async_check_logic.assert_called_once()

    @patch('diagnostics.decorators.asyncio.sleep', new_callable=AsyncMock)
    def test_async_func_fail_then_pass_on_retry(self, mock_decorator_async_sleep):
        mock_async_check_logic = Mock(side_effect=[
            {"status": "failed", "details": "Async failed initially"},
            {"status": "passed", "details": "Async OK on retry"}
        ])

        @diagnostic_test(check_name="test_async_retry_pass", retry_on_failure=True)
        async def decorated_async_func(self_param):
            return mock_async_check_logic()

        result = asyncio.run(decorated_async_func(None))

        self.assertEqual(result['status'], "passed")
        self.assertEqual(result['details'], "Async OK on retry")
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(mock_async_check_logic.call_count, 2)
        mock_decorator_async_sleep.assert_called_once_with(DEFAULT_RETRY_DELAY_SECONDS)

    @patch('diagnostics.decorators.asyncio.sleep', new_callable=AsyncMock)
    def test_async_func_raises_exception_with_retry(self, mock_decorator_async_sleep):
        mock_async_check_logic = Mock(side_effect=[
            RuntimeError("Async Test Exception Attempt 1"),
            RuntimeError("Async Test Exception Attempt 2")
        ])

        @diagnostic_test(check_name="test_async_exception_retry", retry_on_failure=True)
        async def decorated_async_func(self_param):
            return mock_async_check_logic()

        result = asyncio.run(decorated_async_func(None))
        
        self.assertEqual(result['status'], "error")
        self.assertIn("RuntimeError", result['details'])
        self.assertIn("Async Test Exception Attempt 2", result['details'])
        self.assertIn("after 2 attempt(s)", result['details'])
        self.assertEqual(result['attempts'], 2)
        self.assertEqual(mock_async_check_logic.call_count, 2)
        mock_decorator_async_sleep.assert_called_once_with(DEFAULT_RETRY_DELAY_SECONDS)


if __name__ == '__main__':
    unittest.main()
