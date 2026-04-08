import os
import time
from typing import Callable

from openai import OpenAI

from llm_config import BASE_URL


def get_client() -> OpenAI:
    api_key = os.getenv("NEBIUS_API_KEY")
    if not api_key:
        raise ValueError(
            "NEBIUS_API_KEY is missing or empty. "
            "If you ran `export NEBIUS_API_KEY=`, that sets an empty value. "
            "On Windows PowerShell use: `$env:NEBIUS_API_KEY=\"<your_key>\"` and start Jupyter from the same shell, "
            "or set inside the notebook before running: `import os; os.environ['NEBIUS_API_KEY']='<your_key>'`."
        )
    return OpenAI(base_url=BASE_URL, api_key=api_key)


def with_retry(func: Callable, max_retries: int = 3, base_delay: float = 1.0):
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return func()
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries:
                break
            time.sleep(base_delay * (2 ** (attempt - 1)))
    raise RuntimeError(f"API call failed after {max_retries} retries") from last_exc
