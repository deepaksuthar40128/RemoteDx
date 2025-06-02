import asyncio
import time
import functools
from typing import Callable, Any, Dict

CheckResult = Dict[str, Any]
DEFAULT_RETRY_DELAY_SECONDS = 0.5

def diagnostic_test(check_name: str, retry_on_failure: bool = True, retry_delay: float = DEFAULT_RETRY_DELAY_SECONDS):
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async_func = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(self_or_cls, *args, **kwargs) -> CheckResult:
            attempts = 0
            max_attempts = 2 if retry_on_failure else 1
            last_attempt_status = "failed"
            last_attempt_details = ""
            last_attempt_commands_run = []
            last_attempt_duration_sec = 0
            last_exception_occurred = None

            while attempts < max_attempts:
                attempts += 1
                start_time = time.perf_counter()
                current_run_status = "failed"
                current_run_details = ""
                current_run_commands = []
                current_run_exception = None

                try:
                    raw_check_output = await func(self_or_cls, *args, **kwargs)
                    current_run_status = raw_check_output.get("status", "failed")
                    current_run_details = raw_check_output.get("details", "Check function did not provide details.")
                    current_run_commands = raw_check_output.get("commands_run", [])
                except Exception as e:
                    current_run_exception = e
                    current_run_details = f"Error during {check_name} (attempt {attempts}): {type(e).__name__} - {e}"
                    current_run_status = "error"
                
                current_attempt_duration = time.perf_counter() - start_time
                last_attempt_status = current_run_status
                last_attempt_details = current_run_details
                last_attempt_commands_run = current_run_commands
                last_attempt_duration_sec = current_attempt_duration
                last_exception_occurred = current_run_exception

                if last_attempt_status == "passed":
                    break 
                if retry_on_failure and attempts < max_attempts:
                    await asyncio.sleep(retry_delay)
                else:
                    break 
            
            if last_exception_occurred and last_attempt_status == "error":
                last_attempt_details = (f"Error during {check_name} after {attempts} attempt(s): "
                                        f"{type(last_exception_occurred).__name__} - {last_exception_occurred}")

            return {
                "check": check_name,
                "status": last_attempt_status,
                "duration_sec": round(last_attempt_duration_sec, 3),
                "details": last_attempt_details,
                "commands_run": last_attempt_commands_run,
                "attempts": attempts
            }

        @functools.wraps(func)
        def sync_wrapper(self_or_cls, *args, **kwargs) -> CheckResult:
            actual_attempts_made = 0
            max_permitted_attempts = 2 if retry_on_failure else 1

            final_status = "error"
            final_details = "Decorator failed to execute the check properly."
            final_commands_run = []
            final_duration_sec = 0
            final_exception_occurred = None

            for current_attempt_number in range(1, max_permitted_attempts + 1):
                actual_attempts_made = current_attempt_number
                start_time = time.perf_counter()

                current_run_status = "failed"
                current_run_details = ""
                current_run_commands = []
                current_run_exception = None

                try:
                    raw_check_output = func(self_or_cls, *args, **kwargs)
                    current_run_status = raw_check_output.get("status", "failed")
                    current_run_details = raw_check_output.get("details", "Check function did not provide details.")
                    current_run_commands = raw_check_output.get("commands_run", [])
                except Exception as e:
                    current_run_exception = e
                    current_run_details = f"Error during {check_name} (attempt {current_attempt_number}): {type(e).__name__} - {e}"
                    current_run_status = "error"
                
                current_attempt_duration = time.perf_counter() - start_time

                final_status = current_run_status
                final_details = current_run_details
                final_commands_run = current_run_commands
                final_duration_sec = current_attempt_duration
                final_exception_occurred = current_run_exception

                if final_status == "passed":
                    break 
                
                if current_attempt_number < max_permitted_attempts and retry_on_failure:
                    time.sleep(retry_delay)
            
            if final_exception_occurred and final_status == "error":
                final_details = (f"Error during {check_name} after {actual_attempts_made} attempt(s): "
                                 f"{type(final_exception_occurred).__name__} - {final_exception_occurred}")
            
            return {
                "check": check_name,
                "status": final_status,
                "duration_sec": round(final_duration_sec, 3),
                "details": final_details,
                "commands_run": final_commands_run,
                "attempts": actual_attempts_made
            }

        return async_wrapper if is_async_func else sync_wrapper

    return decorator
