# ecom_llm

Lightweight, modular LLM pipeline for e-commerce description generation and evaluation.

The project supports two workflows:
1. Notebook-first exploration and experiments
2. Script/module execution outside notebooks

## What This Project Runs

Input dataset columns:
- product_name
- Product_attribute_list
- material
- warranty

Core flow:
1. Generate a description per row with the generation model.
2. Judge each generated description across 5 criteria.
3. Compute latency and cost ratings.
4. Compute final pass/fail score.
5. Save result sheets for analysis.

Pipeline outputs include:
- generated_description
- latency_ms, input_tokens, output_tokens
- fluency, grammar, tone, length, grounding
- latency_rating, cost_rating
- final_score

## Project Structure (Important Files)

- ecom_llm.py: high-level orchestrator with run_assignment().
- llm_generator.py: generation prompt builder + generation loop.
- llm_judge.py: judge prompt execution and structured rubric output.
- llm_scoring.py: latency/cost ratings + final pass/fail logic.
- llm_client.py: Nebius OpenAI-compatible client + retry wrapper.
- llm_config.py: model IDs and all generation/judging prompt variants.
- data/raw/ecommerce_dataset.csv: default dataset path.
- data/generated/: recommended output directory for Excel artifacts.

## Notebook Guide And Recommended Order

Use this order to understand the project evolution from baseline to improvements:

1. assignment_01_pt1.ipynb
- Baseline full pipeline run.
- Uses the modular code and runs end-to-end generation + judging.
- Good starting point to understand the default flow.

2. assignment_01_pt2_new_prompt.ipynb
- Prompt/guardrail iteration.
- Re-runs the same pipeline with updated prompts and additional checks.
- Use this to compare quality against pt1.

3. assignment_01_pt3_bigger_models.ipynb
- Same pipeline as pt2, but overrides models to larger ones.
- Useful for quality/cost/latency tradeoff experiments.

4. judging_llm_pt4.ipynb
- Judge-focused experimentation.
- Isolates judging modes (single row vs full dataframe).
- Includes criterion-by-criterion judging experiments.

## Prompts In llm_config.py

The file contains both active prompts and legacy versions used for comparison.

Generation prompts:
- GEN_SYSTEM_PROMPT: active generation prompt used by llm_generator.py.
- GEN_SYSTEM_PROMPT_LEGACY: earlier version kept for reference.
- GEN_SYSTEM_PROMPT_Legacy2: intermediate revision kept for reference.

Judge prompts:
- JUDGE_SYSTEM_PROMPT: active full-rubric judge prompt.
- JUDGE_SYSTEM_PROMPT_LEGACY: earlier full-rubric version.
- JUDGE_FLUENCY_PROMPT: metric-specific judge prompt.
- JUDGE_GRAMMAR_PROMPT: metric-specific judge prompt.
- JUDGE_TONE_PROMPT: metric-specific judge prompt.
- JUDGE_GROUNDING_PROMPT: metric-specific judge prompt.

Model config:
- GEN_MODEL: generation model ID.
- JUDGE_MODEL: judge model ID.
- BASE_URL: Nebius OpenAI-compatible API base URL.

If you want to test a different prompt, update the active constants in llm_config.py or override them at runtime before calling run_assignment().

## Setup

1. Create or activate a Python environment.

Windows PowerShell:

	.\venve\Scripts\Activate.ps1

or

	python -m venv .venv
	.venv\Scripts\Activate.ps1

POSIX:

	python -m venv .venv
	source .venv/bin/activate

2. Install dependencies:

	pip install -r requirements.txt

3. Set API key:

Windows PowerShell:

	$env:NEBIUS_API_KEY="<your_key>"

POSIX:

	export NEBIUS_API_KEY="<your_key>"

## Run Full Pipeline Without Notebook

Run the full flow directly from Python (generation + judging + summary):

	python -c "from ecom_llm import run_assignment; r,f,s1,s2 = run_assignment(data_path='data/raw/ecommerce_dataset.csv', excel_path='data/generated/ecommerce_sheet_cli.xlsx'); print(s1); print(s2)"

What this does:
1. Reads data/raw/ecommerce_dataset.csv.
2. Generates descriptions.
3. Runs judge on all rows.
4. Saves trimmed output to data/generated/ecommerce_sheet_cli.xlsx.
5. Returns in-memory DataFrames:
- r: trimmed output columns.
- f: full output with explanation columns.
- s1: overview summary.
- s2: verdict distribution summary.

## Run Judging Only Without Notebook

If you already have generated rows and want to re-run only judging:

	python -c "import pandas as pd; from llm_client import get_client; from llm_judge import run_judge; df = pd.read_excel('data/generated/ecommerce_sheet_new.xlsx'); judged_df, judged_full = run_judge(results_df=df, client=get_client(), excel_path='data/generated/ecommerce_sheet_new_judged_full.xlsx'); print(judged_df.head())"

## Notes

- The repository includes venve/ (local environment). Use only if you trust included packages.
- For consistent paths across notebooks and scripts, prefer:
  - Input: data/raw/ecommerce_dataset.csv
  - Outputs: data/generated/
- retry/backoff for API calls is implemented in llm_client.py via with_retry().

---
Created for local experiments with LLMs on e-commerce data.
