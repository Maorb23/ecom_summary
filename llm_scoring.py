import os
from typing import Tuple

import pandas as pd


def rate_latency(latency_ms: int) -> str:
    if latency_ms < 2000:
        return "good"
    if latency_ms <= 5000:
        return "ok"
    return "bad"


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    input_cost_per_1m = float(os.getenv("NEBIUS_INPUT_COST_PER_1M", "0"))
    output_cost_per_1m = float(os.getenv("NEBIUS_OUTPUT_COST_PER_1M", "0"))
    return (
        (input_tokens / 1_000_000) * input_cost_per_1m
        + (output_tokens / 1_000_000) * output_cost_per_1m
    )


def rate_cost(cost_usd: float) -> str:
    if cost_usd < 0.0005:
        return "good"
    if cost_usd <= 0.002:
        return "ok"
    return "bad"


def final_pass_fail(
    fluency: str,
    grammar: str,
    tone: str,
    length: str,
    grounding: str,
    latency_rating: str,
    cost_rating: str,
) -> str:   
    """Determines final pass/fail based on individual criteria ratings.
    We set a higher bar for grounding and length, where a "bad" rating in either results in an automatic fail,
    while for other criteria we allow some leniency as long as the majority are "good".
    """
    ratings = [fluency, grammar, tone, length, grounding, latency_rating, cost_rating]
    if grounding == "bad" or length == "bad":
        return "fail"
    if any(r == "bad" for r in ratings):
        return "fail"
    return "pass" if sum(r == "good" for r in ratings) >= 4 else "fail"


def build_summary(results_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    criteria_for_distribution = [
        "fluency",
        "grammar",
        "tone",
        "length",
        "grounding",
        "latency_rating",
        "cost_rating",
    ]

    pass_count = int((results_df["final_score"] == "pass").sum())
    total_count = len(results_df)
    pass_rate = (pass_count / total_count * 100) if total_count else 0.0

    distribution = {}
    for col in criteria_for_distribution:
        distribution[col] = results_df[col].value_counts().reindex(["good", "ok", "bad"], fill_value=0)

    summary_distribution = pd.DataFrame(distribution).T
    summary_distribution["total"] = summary_distribution[["good", "ok", "bad"]].sum(axis=1)

    summary_overview = pd.DataFrame(
        [
            {"metric": "pass_rate_percent", "value": round(pass_rate, 2)},
            {"metric": "pass_count", "value": pass_count},
            {"metric": "total_count", "value": total_count},
        ]
    )
    return summary_overview, summary_distribution
