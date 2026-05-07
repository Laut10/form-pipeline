from __future__ import annotations

import pandas as pd

REQUIRED_FIELDS = ["form_id", "name", "email", "country", "created_at", "source"]
CRITICAL_FIELDS = ["form_id", "name"]   # records missing these are dropped in clean
MAX_MISSING_RATE = 0.80                 # abort if >80% of records lack a critical field


class ValidationError(Exception):
    pass


def validate(df: pd.DataFrame) -> dict:
    """
    Checks schema completeness and field-level null rates.
    Returns a report dict. Raises ValidationError if data is too degraded to process.
    """
    report = {
        "total_records": len(df),
        "missing_fields": [],
        "null_rates": {},
        "will_be_dropped": 0,
        "passed": True,
    }

    # 1. Schema check — all expected columns must be present
    missing = [f for f in REQUIRED_FIELDS if f not in df.columns]
    if missing:
        raise ValidationError(f"[validate] Missing columns in source data: {missing}")
    report["missing_fields"] = missing

    # 2. Null rate per field
    for field in REQUIRED_FIELDS:
        null_count = int(df[field].isna().sum())
        rate = null_count / len(df) if len(df) > 0 else 0
        report["null_rates"][field] = {"null_count": null_count, "null_rate": round(rate, 3)}

    # 3. Records that will be dropped (missing critical fields)
    will_drop = df[CRITICAL_FIELDS].isna().any(axis=1).sum()
    report["will_be_dropped"] = int(will_drop)

    # 4. Hard stop if critical fields are almost entirely missing
    for field in CRITICAL_FIELDS:
        rate = report["null_rates"][field]["null_rate"]
        if rate > MAX_MISSING_RATE:
            report["passed"] = False
            raise ValidationError(
                f"[validate] Critical field '{field}' is {rate:.0%} null — aborting pipeline."
            )

    # 5. Duplicate check
    dupe_count = int(df.duplicated(subset=["form_id"]).sum())
    report["duplicate_form_ids"] = dupe_count

    _print_report(report)
    return report


def _print_report(report: dict):
    total = report["total_records"]
    print(f"[validate] Total records       : {total}")
    print(f"[validate] Duplicate form_ids  : {report['duplicate_form_ids']}")
    print(f"[validate] Records to drop     : {report['will_be_dropped']}  (missing form_id or name)")
    print(f"[validate] Null rates per field:")
    for field, stats in report["null_rates"].items():
        bar = "⚠" if stats["null_rate"] > 0.10 else " "
        print(f"           {bar}  {field:<15} {stats['null_count']:>3} nulls  ({stats['null_rate']:.1%})")
    print(f"[validate] Validation PASSED ✓")
