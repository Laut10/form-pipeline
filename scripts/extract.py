import json
import os
import pandas as pd


def extract(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    print(f"[extract] Loaded {len(df)} records from {os.path.basename(path)}")
    return df
