from __future__ import annotations

import re
import pandas as pd
from datetime import datetime, date

# ---------------------------------------------------------------------------
# Country normalization map
# ---------------------------------------------------------------------------
COUNTRY_MAP = {
    # Spain
    "es": "España", "españa": "España", "espana": "España", "spain": "España", "esp": "España",
    # Mexico
    "mx": "México", "mexico": "México", "méxico": "México", "mex": "México",
    # Argentina
    "ar": "Argentina", "argentina": "Argentina", "arg": "Argentina",
    # Colombia
    "co": "Colombia", "colombia": "Colombia", "col": "Colombia",
    # Chile
    "cl": "Chile", "chile": "Chile",
    # Peru
    "pe": "Perú", "peru": "Perú", "perú": "Perú",
    # Ecuador
    "ec": "Ecuador", "ecuador": "Ecuador",
    # Bolivia
    "bo": "Bolivia", "bolivia": "Bolivia",
    # USA
    "us": "USA", "usa": "USA", "united states": "USA",
}

# Order matters: try unambiguous formats first
DATE_FORMATS = [
    "%Y-%m-%d",     # 2025-04-05  (unambiguous — try first)
    "%d %b %Y",     # 05 Apr 2025
    "%B %d, %Y",    # April 05, 2025
    "%d-%m-%Y",     # 05-04-2025
    "%d/%m/%y",     # 05/04/25    (European dd/mm — matches project context)
    "%m/%d/%Y",     # 04/05/2025  (US fallback)
]

SOURCE_ALIASES = {
    "landing page": "landing_page",
    "google ads":   "google_ads",
    "email campaign": "email_campaign",
}


# ---------------------------------------------------------------------------
# Field-level cleaners
# ---------------------------------------------------------------------------

def _clean_name(value) -> str | None:
    if pd.isna(value) or not str(value).strip():
        return None
    return str(value).strip().title()


def _clean_email(value) -> str | None:
    if pd.isna(value) or not str(value).strip():
        return None
    email = str(value).strip().lower()
    email = email.replace(",", ".")           # gmail,com → gmail.com
    email = re.sub(r"@{2,}", "@", email)      # @@ → @
    email = email.rstrip(".")                 # trailing dots
    # Basic structural validation: something@something.something
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return None
    return email


def _clean_country(value) -> str | None:
    if pd.isna(value) or not str(value).strip():
        return None
    key = str(value).strip().lower()
    return COUNTRY_MAP.get(key, str(value).strip())  # unknown → keep as-is


def _clean_date(value) -> date | None:
    if pd.isna(value) or not str(value).strip():
        return None
    raw = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None  # unparseable


def _clean_source(value) -> str | None:
    if pd.isna(value) or not str(value).strip():
        return None
    normalized = str(value).strip().lower().replace(" ", "_")
    return SOURCE_ALIASES.get(normalized.replace("_", " "), normalized)


# ---------------------------------------------------------------------------
# DataFrame-level pipeline
# ---------------------------------------------------------------------------

def clean(df: pd.DataFrame) -> pd.DataFrame:
    original_count = len(df)

    # 1. Remove exact duplicates by form_id (keep first occurrence)
    df = df.drop_duplicates(subset=["form_id"], keep="first")
    dupes_removed = original_count - len(df)

    # 2. Apply field cleaners
    df = df.copy()
    df["name"]       = df["name"].apply(_clean_name)
    df["email"]      = df["email"].apply(_clean_email)
    df["country"]    = df["country"].apply(_clean_country)
    df["created_at"] = df["created_at"].apply(_clean_date)
    df["source"]     = df["source"].apply(_clean_source)

    # 3. Collect stats before dropping invalids
    invalid_emails  = df["email"].isna().sum()
    invalid_dates   = df["created_at"].isna().sum()
    null_countries  = df["country"].isna().sum()

    # 4. Drop records missing business-critical fields
    df = df.dropna(subset=["form_id", "name"])

    print(f"[clean] Duplicates removed : {dupes_removed}")
    print(f"[clean] Invalid emails     : {invalid_emails}  (set to NULL)")
    print(f"[clean] Unparseable dates  : {invalid_dates}   (set to NULL)")
    print(f"[clean] Missing countries  : {null_countries}  (set to NULL)")
    print(f"[clean] Records after clean: {len(df)}")

    return df.reset_index(drop=True)
