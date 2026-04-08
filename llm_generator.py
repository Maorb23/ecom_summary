import time
import re

import pandas as pd
from openai import OpenAI
from tqdm.auto import tqdm

from llm_client import with_retry
from llm_config import GEN_MODEL, GEN_SYSTEM_PROMPT, OUTPUT_COLUMNS, REQUIRED_INPUT_COLUMNS


def _extract_rating_from_attributes(attributes: str) -> str | None:
    match = re.search(r"\b\d(?:\.\d)?/5\b", attributes or "")
    return match.group(0) if match else None


def _ensure_rating_mentioned(description: str, row: pd.Series) -> str:
    rating = _extract_rating_from_attributes(str(row.get("Product_attribute_list", "")))
    if not rating:
        return description
    if rating in description:
        return description

    suffix = f" Rated {rating} by customers."
    trimmed = description.rstrip()
    if not trimmed:
        return f"Rated {rating} by customers."
    return f"{trimmed}{suffix}"


def build_generation_user_prompt(row: pd.Series) -> str:
    """Build the user prompt for generation based on the input row."""
    rating = _extract_rating_from_attributes(str(row.get("Product_attribute_list", "")))
    rating_line = (
        f"\nImportant: include this exact rating token in your description: {rating}"
        if rating
        else ""
    )
    return (
        f"Product name: {row['product_name']}\n"
        f"Attributes: {row['Product_attribute_list']}\n"
        f"Material: {row['material']}\n"
        f"Warranty: {row['warranty']}"
        f"{rating_line}"
    )


def generate_one(client: OpenAI, row: pd.Series) -> dict:
    start = time.perf_counter()

    def _call():
        return client.chat.completions.create(
            model=GEN_MODEL,
            temperature=0.7,
            max_tokens=200,
            messages=[
                {"role": "system", "content": GEN_SYSTEM_PROMPT},
                {"role": "user", "content": build_generation_user_prompt(row)},
            ],
        )

    response = with_retry(_call, max_retries=3, base_delay=1.0)
    latency_ms = int((time.perf_counter() - start) * 1000)

    usage = response.usage
    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

    generated_description = (response.choices[0].message.content or "").strip()
    generated_description = _ensure_rating_mentioned(generated_description, row)
    return {
        "generated_description": generated_description,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def run_generation(client: OpenAI, df: pd.DataFrame, excel_path: str) -> pd.DataFrame:
    rows_out = []
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Task 2: Generating"):
        base = {col: row[col] for col in REQUIRED_INPUT_COLUMNS}
        base.update(generate_one(client, row))
        base.update(
            {
                "fluency": "",
                "grammar": "",
                "tone": "",
                "length": "",
                "grounding": "",
                "latency_rating": "",
                "cost_rating": "",
                "final_score": "",
            }
        )
        rows_out.append(base)

    results_df = pd.DataFrame(rows_out, columns=OUTPUT_COLUMNS)
    results_df.to_excel(excel_path, index=False)
    return results_df
