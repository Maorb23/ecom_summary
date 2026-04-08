import re
from typing import Literal

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel
from tqdm.auto import tqdm

from llm_client import with_retry
from llm_config import (
    JUDGE_FLUENCY_PROMPT,
    JUDGE_GRAMMAR_PROMPT,
    JUDGE_GROUNDING_PROMPT,
    JUDGE_MODEL,
    JUDGE_SYSTEM_PROMPT,
    JUDGE_TONE_PROMPT,
    OUTPUT_COLUMNS,
)
from llm_scoring import estimate_cost_usd, final_pass_fail, rate_cost, rate_latency


MetricName = Literal["fluency", "grammar", "tone", "grounding"]


METRIC_PROMPTS: dict[MetricName, str] = {
    "fluency": JUDGE_FLUENCY_PROMPT,
    "grammar": JUDGE_GRAMMAR_PROMPT,
    "tone": JUDGE_TONE_PROMPT,
    "grounding": JUDGE_GROUNDING_PROMPT,
}


class CriterionResult(BaseModel):
    explanation: str
    verdict: Literal["good", "ok", "bad"]


class JudgeOutput(BaseModel):
    fluency: CriterionResult
    grammar: CriterionResult
    tone: CriterionResult
    length: CriterionResult
    grounding: CriterionResult


def build_judge_user_prompt(row: pd.Series) -> str:
    return (
        f"Product name: {row['product_name']}\n"
        f"Attributes: {row['Product_attribute_list']}\n"
        f"Material: {row['material']}\n"
        f"Warranty: {row['warranty']}\n\n"
        f"Generated description:\n{row['generated_description']}"
    )


def _extract_required_rating(source_text: str) -> str | None:
    match = re.search(r"\b\d(?:\.\d)?/5\b", source_text or "")
    return match.group(0) if match else None


def _enforce_grounding_rating_guard(row: pd.Series, grounding: CriterionResult) -> CriterionResult:
    source_text = str(row.get("Product_attribute_list", ""))
    description = str(row.get("generated_description", ""))
    required_rating = _extract_required_rating(source_text)

    if required_rating and required_rating not in description:
        return CriterionResult(
            explanation=(
                f"{grounding.explanation} | Deterministic guard: rating '{required_rating}' "
                "appears in source but is missing from description, so grounding is bad."
            ),
            verdict="bad",
        )
    return grounding


def judge_one(client: OpenAI, row: pd.Series) -> JudgeOutput:
    def _call():
        return client.chat.completions.parse(
            model=JUDGE_MODEL,
            temperature=0.0,
            max_tokens=3000,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": build_judge_user_prompt(row)},
            ],
            response_format=JudgeOutput,
        )

    response = with_retry(_call, max_retries=3, base_delay=1.0)
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raw_content = response.choices[0].message.content or "{}"
        parsed = JudgeOutput.model_validate_json(raw_content)
    return parsed


def judge_one_metric(client: OpenAI, row: pd.Series, metric: MetricName) -> CriterionResult:
    metric_prompt = METRIC_PROMPTS[metric]

    def _call():
        return client.chat.completions.parse(
            model=JUDGE_MODEL,
            temperature=0.0,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": metric_prompt},
                {"role": "user", "content": build_judge_user_prompt(row)},
            ],
            response_format=CriterionResult,
        )

    response = with_retry(_call, max_retries=3, base_delay=1.0)
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raw_content = response.choices[0].message.content or "{}"
        parsed = CriterionResult.model_validate_json(raw_content)
    if metric == "grounding":
        return _enforce_grounding_rating_guard(row, parsed)
    return parsed


def run_judge(results_df: pd.DataFrame, client: OpenAI, excel_path: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    for idx, row in tqdm(results_df.iterrows(), total=len(results_df), desc="Task 5: Judging"):
        judge = judge_one(client, row)
        judge.grounding = _enforce_grounding_rating_guard(row, judge.grounding)

        results_df.at[idx, "fluency"] = judge.fluency.verdict
        results_df.at[idx, "grammar"] = judge.grammar.verdict
        results_df.at[idx, "tone"] = judge.tone.verdict
        results_df.at[idx, "length"] = judge.length.verdict
        results_df.at[idx, "grounding"] = judge.grounding.verdict
        results_df.at[idx, "fluency_explanation"] = judge.fluency.explanation
        results_df.at[idx, "grammar_explanation"] = judge.grammar.explanation
        results_df.at[idx, "tone_explanation"] = judge.tone.explanation
        results_df.at[idx, "length_explanation"] = judge.length.explanation
        results_df.at[idx, "grounding_explanation"] = judge.grounding.explanation


        latency_rating = rate_latency(int(row["latency_ms"]))
        call_cost = estimate_cost_usd(int(row["input_tokens"]), int(row["output_tokens"]))
        cost_rating = rate_cost(call_cost)

        results_df.at[idx, "latency_rating"] = latency_rating
        results_df.at[idx, "cost_rating"] = cost_rating

        results_df.at[idx, "final_score"] = final_pass_fail(
            fluency=judge.fluency.verdict,
            grammar=judge.grammar.verdict,
            tone=judge.tone.verdict,
            length=judge.length.verdict,
            grounding=judge.grounding.verdict,
            latency_rating=latency_rating,
            cost_rating=cost_rating,
        )

    full_df = results_df.copy()
    results_df = results_df[OUTPUT_COLUMNS]
    results_df.to_excel(excel_path, index=False)
    return results_df, full_df
