# ecom_llm

Lightweight utilities and examples for working with LLMs on an e-commerce dataset.

Contents
- `assignment_01_pipeline.py` - Example pipeline runner for Assignment 01.
- `assignment_01.ipynb` - Notebook for exploration and experiments.
- `llm_client.py`, `llm_generator.py`, `llm_scoring.py`, `llm_judge.py` - core modules for interacting with and evaluating LLM outputs.
- `prompt.md` - prompt(s) used by the project.
- `data/Assignment_01_product_dataset.csv` - sample dataset for experiments.
- `secrets/NEBIUS_API_KEY.txt` - (not tracked) example secret used by some utilities.

Quick start

1. (Recommended) Use the provided virtual environment `venve/` or create your own.

Windows PowerShell (use provided `venve` or create new):
```powershell
# If you want to use the included environment (venve), activate it:
.\venve\Scripts\Activate.ps1

# Or create a fresh venv and activate it:
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

POSIX (WSL / macOS / Linux):
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the pipeline or script
```bash
python assignment_01_pipeline.py
# or open and run the notebook: assignment_01.ipynb
```

Environment / secrets
- The project may expect API keys or secrets. You can place them in `secrets/` (not committed) or export env vars.
- Example: set `NEBIUS_API_KEY` from the contents of `secrets/NEBIUS_API_KEY.txt`.

Notes
- The repository includes `venve/` which contains a local virtual environment — use it only if you trust the included packages.
- `requirements.txt` lists the Python dependencies used by scripts and notebooks.

Development
- Edit or extend `llm_generator.py` and `llm_scoring.py` to change generation or evaluation behaviour.
- Use `assignment_01.ipynb` to experiment interactively with the dataset.

License & Contributing
- This repo does not include a license file. Add one if you plan to share publicly.
- Contributions: open an issue or submit a PR with changes.

---
Created for local experiments with LLMs on e-commerce data.
