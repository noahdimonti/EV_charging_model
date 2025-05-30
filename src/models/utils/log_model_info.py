import time
from src.config import params
from typing import Callable, Any, Tuple


def log_with_runtime(label: str, finished_label: str, func: Callable, *args, **kwargs) -> Tuple[Any, float]:
    """
    Executes a function with timing and logs its runtime.

    Parameters:
        label (str): Descriptive text to print before running the function.
        finished_label (str): Text to print at the end to specify that optimisation or simulation finished running.
        func (Callable): Function to execute.
        *args, **kwargs: Arguments to pass to the function.

    Returns:
        Tuple: (result of the function, runtime in seconds)
    """
    print(f'\n=============================================================\n'
          f'{label} ...'
          f'\n=============================================================\n')

    start_time = time.time()

    result = func(*args, **kwargs)

    end_time = time.time()
    runtime = end_time - start_time

    # Format the runtime
    if (runtime % 60) < 1:
        print(f'\n{params.GREEN}{finished_label} in {runtime:.3f} seconds{params.RESET}')
    else:
        minutes = int(runtime // 60)
        remaining_seconds = runtime % 60
        print(f'\n{params.GREEN}{finished_label} in {minutes} minutes {remaining_seconds:.3f} seconds{params.RESET}')

    print(f'\n-------------------------------------------------------------\n')
    return result, runtime
