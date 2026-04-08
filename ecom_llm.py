import pandas as pd

from llm_client import get_client
from llm_config import REQUIRED_INPUT_COLUMNS
from llm_generator import run_generation
from llm_judge import run_judge
from llm_scoring import build_summary


def validate_input_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        raise ValueError("Input DataFrame is None.")
    missing_cols = [col for col in REQUIRED_INPUT_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input DataFrame is missing required columns: {missing_cols}")
    return df[REQUIRED_INPUT_COLUMNS].copy()


def load_input_df(data_path: str = "data/Assignment_01_product_dataset.csv") -> pd.DataFrame:
    df = pd.read_csv(data_path)
    return validate_input_df(df)


def run_assignment(
    df: pd.DataFrame | None = None,
    excel_path: str = "assignment_01.xlsx",
    data_path: str = "data/Assignment_01_product_dataset.csv",
):
    validated_df = validate_input_df(df) if df is not None else load_input_df(data_path)
    client = get_client()

    results_df = run_generation(client=client, df=validated_df, excel_path=excel_path)
    results_df, full_df = run_judge(results_df=results_df, client=client, excel_path=excel_path)
    summary_overview, summary_distribution = build_summary(results_df)

    return results_df, full_df, summary_overview, summary_distribution
