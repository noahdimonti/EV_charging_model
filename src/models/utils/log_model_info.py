import time
from src.config import params
from typing import Callable, Any, Tuple


def log_with_runtime(label: str, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """ Executes a function with timing and logs its runtime. """
    print(f'\n=============================================================\n'
          f'{label} ...'
          f'\n=============================================================\n')

    start_time = time.time()

    result = func(*args, **kwargs)

    end_time = time.time()
    runtime = end_time - start_time

    return result, runtime


def print_runtime(finished_label: str, runtime: float):
    print(f'-------------------------------------------------------------\n')
    # Format the runtime
    if (runtime // 60) < 1:
        print(f'{params.YELLOW}{finished_label} in {runtime:.3f} seconds{params.RESET}\n')
    else:
        minutes = int(runtime // 60)
        remaining_seconds = runtime % 60
        print(f'{params.YELLOW}{finished_label} in {minutes} minutes {remaining_seconds:.3f} seconds{params.RESET}\n')


