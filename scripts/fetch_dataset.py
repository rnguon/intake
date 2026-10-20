"""Download the Bitext customer-support dataset and prepare Intake's seed data.

Run from the root of your intake repo:
    uv run --with datasets --with pandas python scripts/fetch_dataset.py

Creates:
    data/raw/bitext_full.csv          every row (~27,000), for load tests and seeding
    data/raw/sample_requests.csv      a balanced sample (~8 per intent) for the app
    evals/seed_labels.csv             50 rows with empty label columns to fill by hand
"""

from pathlib import Path

import pandas as pd
from datasets import load_dataset

REPO = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"
RAW_DIR = Path("data/raw")
EVAL_DIR = Path("evals")
PER_INTENT = 8      # about 27 intents x 8 = ~216 sample requests
LABEL_ROWS = 50     # rows you label by hand in Lesson 1
SEED = 42           # fixed seed so the sample is reproducible


def main() -> None:
    df: pd.DataFrame = load_dataset(REPO, split="train").to_pandas()
    print(f"Downloaded {len(df):,} rows with columns: {list(df.columns)}")

    required = {"instruction", "category", "intent"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Dataset columns changed; missing {missing}")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(RAW_DIR / "bitext_full.csv", index=False)

    # Balanced sample: the same number of requests from every intent, then shuffled.
    sample = (
        df.groupby("intent")
        .sample(n=PER_INTENT, random_state=SEED)
        .sample(frac=1, random_state=SEED)
        .reset_index(drop=True)
    )
    sample.insert(0, "id", [f"req-{i:04d}" for i in range(1, len(sample) + 1)])
    sample[["id", "instruction", "category", "intent"]].to_csv(
        RAW_DIR / "sample_requests.csv", index=False
    )

    # Labeling sheet: your own categories and priorities, not Bitext's intents.
    labels = sample.loc[: LABEL_ROWS - 1, ["id", "instruction"]].copy()
    labels["category"] = ""
    labels["priority"] = ""
    labels["notes"] = ""
    labels.to_csv(EVAL_DIR / "seed_labels.csv", index=False)

    print(f"Wrote {len(sample)} sample requests to {RAW_DIR / 'sample_requests.csv'}")
    print(f"Wrote {len(labels)} rows to label in {EVAL_DIR / 'seed_labels.csv'}")


if __name__ == "__main__":
    main()
