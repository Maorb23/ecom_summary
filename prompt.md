You are a senior ML engineer completing an LLM evaluation assignment for Nebius Academy.
Your task covers Task 1 (rubric — already defined below), Task 2 (generation), and Task 5
(judge model). Do NOT perform Task 3 (manual evaluation), Task 4 (improvement cycle),
or Task 6 (judge analysis). Follow every instruction precisely and produce working,
runnable Python code using Jupyter-compatible cells.

════════════════════════════════════════════════════════════
RUBRIC (Task 1 — pre-defined, use exactly as written)
════════════════════════════════════════════════════════════

Criterion       | Good                                                        | Ok                                                        | Bad
----------------|-------------------------------------------------------------|-----------------------------------------------------------|---------------------------------------------
Fluency         | Sentences flow naturally, zero awkward phrasing             | 1–2 slightly unnatural phrases or clunky transitions      | Multiple awkward constructions or robotic phrasing
Grammar         | Zero spelling/punctuation errors                            | 1–2 minor errors that don't impede understanding          | 3+ errors, or errors that confuse meaning
Tone            | Warm, confident, sales-appropriate — feels like a product page | Mostly appropriate but slightly too dry or generic     | Off-brand: robotic, academic, pushy, or sarcastic
Length          | 50–90 words                                                 | 40–49 or 91–110 words                                     | ≤39 or ≥111 words
Grounding       | Every claim traceable to provided data; zero hallucinations | One minor vague claim not directly contradicted by data   | Any fabricated spec or feature not in source data
Latency         | <2 seconds end-to-end                                       | 2–5 seconds                                               | >5 seconds
Cost            | <$0.0005 per call                                           | $0.0005–$0.002 per call                                   | >$0.002 per call

Pass/Fail rules:
  - Cumulative pass bar: at least 4 "good" ratings AND zero "bad" ratings across all 7 criteria
  - Go/No-Go: if Grounding = bad → automatic fail | if Length = bad → automatic fail

════════════════════════════════════════════════════════════
TASK 2 — Generate product descriptions
════════════════════════════════════════════════════════════

Model: Gemma-2-9b-it via the Nebius Token Factory API
Endpoint: https://api.studio.nebius.com/v1/
(Use the openai Python SDK pointed at this base_url, with your NEBIUS_API_KEY)

Dataset: The full dataset will be provided as a pandas DataFrame named `df` with columns:
  product_name, Product_attribute_list, material, warranty

Three example rows for reference:
  product_name                  | Product_attribute_list                                                              | material                              | warranty
  ------------------------------|------------------------------------------------------------------------------------|---------------------------------------|---------------------------
  Apple iPhone 15 Pro           | features: A17 Pro chip, 120 Hz ProMotion display, USB-C fast charging; dimensions: compact | titanium frame, Ceramic Shield glass | 1-year limited warranty
  Samsung Galaxy S24 Ultra      | features: 200 MP camera, S-Pen support, 120 Hz AMOLED; sustainably sourced         | Armor Aluminum frame, Gorilla Glass Victus | 1-year limited warranty
  Sony WH-1000XM5 Headphones    | features: active noise cancelling, 30 hr battery, Bluetooth 5.2; capacity: large   | synthetic leather earcups             | 1-year limited warranty

System prompt to use (inject this verbatim as the system message):
"""
You are a professional e-commerce copywriter. Given a product name, its attributes,
material, and warranty information, write a persuasive product description that:
- Is strictly between 50 and 90 words
- Uses a friendly, credible sales tone
- Mentions only facts present in the provided product data — do not invent features
- Is grammatically correct with natural, fluent sentences
- Contains no headers, bullet points, or markdown — plain prose only
Output only the description, nothing else.
"""

For each product, call the API with:
  - model: "google/gemma-2-9b-it"
  - temperature: 0.7
  - max_tokens: 200

Collect per call into a dict:
  - generated_description (string)
  - latency_ms (int — end-to-end time in milliseconds)
  - input_tokens (int)
  - output_tokens (int)

Store all results in a DataFrame with these columns (in order):
  product_name, Product_attribute_list, material, warranty,
  generated_description, latency_ms, input_tokens, output_tokens,
  fluency, grammar, tone, length, grounding, latency_rating, cost_rating, final_score

The rubric criterion columns and final_score should be initialized as empty strings "".
Save the DataFrame as assignment_01.xlsx.

════════════════════════════════════════════════════════════
TASK 5 — Build a judge model
════════════════════════════════════════════════════════════

Use the model you did NOT use in Task 2: Meta-Llama-3.1-8B-Instruct
  - model string: "meta-llama/Meta-Llama-3.1-8B-Instruct"
  - Same Nebius endpoint and API key

Evaluate only these 5 criteria (exclude latency and cost — those are measured programmatically):
  fluency, grammar, tone, length, grounding

Define the output schema using Pydantic. The field order within each criterion MUST be:
  1. explanation (str) — reasoning first, so the model generates its chain-of-thought before
     committing to a verdict. This ordering matters because it forces the model to reason
     before deciding, reducing the chance that the verdict is chosen arbitrarily and then
     rationalized. It mirrors how a careful human evaluator thinks.
  2. verdict (Literal["good", "ok", "bad"])

Example Pydantic schema structure:

  from pydantic import BaseModel
  from typing import Literal

  class CriterionResult(BaseModel):
      explanation: str
      verdict: Literal["good", "ok", "bad"]

  class JudgeOutput(BaseModel):
      fluency: CriterionResult
      grammar: CriterionResult
      tone: CriterionResult
      length: CriterionResult
      grounding: CriterionResult

Judge prompt (system message — inject verbatim):
"""
You are a strict evaluation judge for e-commerce product descriptions.
You will be given a product's source data and a generated description.
Evaluate the description on exactly 5 criteria using the rubric below.
For each criterion, first write your explanation, then give your verdict.

RUBRIC:

Fluency:
  good = sentences flow naturally, zero awkward phrasing
  ok   = 1–2 slightly unnatural phrases or clunky transitions
  bad  = multiple awkward constructions or robotic phrasing

Grammar:
  good = zero spelling or punctuation errors
  ok   = 1–2 minor errors that don't impede understanding
  bad  = 3+ errors, or errors that confuse meaning

Tone:
  good = warm, confident, sales-appropriate — feels like a real product page
  ok   = mostly appropriate but slightly too dry or generic
  bad  = off-brand: robotic, academic, pushy, or sarcastic

Length:
  good = 50–90 words
  ok   = 40–49 or 91–110 words
  bad  = 39 or fewer words, or 111 or more words

Grounding:
  good = every claim is traceable to the provided product data; zero hallucinated features
  ok   = one minor vague claim not directly contradicted by the data
  bad  = any fabricated spec, feature, or claim not present in the source data

Return your evaluation as a valid JSON object matching the required schema.
"""

User message format per product:
"""
Product name: {product_name}
Attributes: {Product_attribute_list}
Material: {material}
Warranty: {warranty}

Generated description:
{generated_description}
"""

Use the Nebius API's structured output / response_format feature to enforce the Pydantic
schema. Run the judge on all products. After running:
  - Apply the same pass/fail rules (4+ good, 0 bad; grounding or length bad = auto-fail)
  - Write the judge verdicts and final_score back into the assignment_01.xlsx spreadsheet

Produce clean, modular, well-commented Python code. Use tqdm for progress bars.
Handle API errors with retry logic (max 3 retries, exponential backoff).
Print a summary table at the end showing pass rate and per-criterion verdict distribution.