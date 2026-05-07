import json
import random
import os
from datetime import datetime, timedelta

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "raw_submissions.json")
NUM_RECORDS = 150
DUPLICATE_RATE = 0.12
NULL_FIELD_RATE = 0.05

# ---------------------------------------------------------------------------
# Data pools — intentionally messy to simulate real-world form submissions
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Juan", "Maria", "Carlos", "Ana", "Pedro", "Lucia", "Miguel", "Sofia",
    "Diego", "Elena", "Andres", "Isabel", "Roberto", "Laura", "Fernando",
    "Patricia", "Jorge", "Marta", "Sergio", "Carmen", "Alejandro", "Beatriz",
    "Raul", "Cristina", "Manuel", "Sandra", "Pablo", "Monica", "Alberto", "Rosa",
]

LAST_NAMES = [
    "Garcia", "Lopez", "Martinez", "Rodriguez", "Fernandez", "Gonzalez",
    "Hernandez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores",
    "Rivera", "Gomez", "Diaz", "Morales", "Jimenez", "Ruiz", "Vargas", "Castillo",
]

# Each entry is a pool of equivalent representations for the same country
COUNTRY_VARIANTS = {
    "España":  ["ES", "España", "spain", "SPAIN", "esp", "es", "Espana", "españa"],
    "México":  ["MX", "México", "mexico", "MEXICO", "mx", "Mexico", "mex"],
    "Argentina": ["AR", "Argentina", "argentina", "ARGENTINA", "arg", "ar"],
    "Colombia": ["CO", "Colombia", "colombia", "COLOMBIA", "col", "co"],
    "Chile":   ["CL", "Chile", "chile", "CHILE", "cl"],
    "Peru":    ["PE", "Peru", "peru", "PERU", "pe", "Perú"],
    "Ecuador": ["EC", "Ecuador", "ecuador", "ECUADOR", "ec"],
    "Bolivia": ["BO", "Bolivia", "bolivia", "BOLIVIA", "bo"],
    "USA":     ["US", "usa", "USA", "United States", "united states", "us"],
}

EMAIL_DOMAINS = [
    "gmail.com", "hotmail.com", "yahoo.com", "outlook.com",
    "icloud.com", "live.com", "protonmail.com",
]

# Defects applied to some emails
EMAIL_DEFECTS = [
    lambda e: e.replace(".", ","),          # juan@gmail,com
    lambda e: e.replace("@", ""),           # juangmail.com
    lambda e: e + "..",                     # juan@gmail.com..
    lambda e: e.replace("@", "@@"),         # juan@@gmail.com
    lambda e: e.upper(),                    # valid but noisy casing
]

SOURCES = [
    "landing_page", "Landing_Page", "LANDING_PAGE",
    "google_ads", "GOOGLE_ADS", "Google Ads",
    "facebook", "Facebook", "FACEBOOK",
    "organic", "Organic", "ORGANIC",
    "email_campaign", "Email Campaign", "email campaign",
    "referral",
]

# Multiple date format functions to simulate inconsistency
DATE_FORMATTERS = [
    lambda d: d.strftime("%d/%m/%y"),       # 05/04/25
    lambda d: d.strftime("%Y-%m-%d"),        # 2025-04-05
    lambda d: d.strftime("%m/%d/%Y"),        # 04/05/2025
    lambda d: d.strftime("%d-%m-%Y"),        # 05-04-2025
    lambda d: d.strftime("%B %d, %Y"),       # April 05, 2025
    lambda d: d.strftime("%d %b %Y"),        # 05 Apr 2025
]

NAME_CASE_TRANSFORMS = [
    lambda n: n,                            # Carlos Garcia  (normal)
    lambda n: n.upper(),                    # CARLOS GARCIA
    lambda n: n.lower(),                    # carlos garcia
    lambda n: n.split()[0].upper() + " " + n.split()[1],  # CARLOS Garcia
    lambda n: n.split()[0] + " " + n.split()[1].upper(),  # Carlos GARCIA
]


# ---------------------------------------------------------------------------
# Generators
# ---------------------------------------------------------------------------

def random_date(start_days_ago=365):
    base = datetime.now() - timedelta(days=start_days_ago)
    offset = random.randint(0, start_days_ago)
    return base + timedelta(days=offset)


def generate_email(first: str, last: str) -> str:
    patterns = [
        f"{first.lower()}.{last.lower()}",
        f"{first.lower()}{last.lower()}",
        f"{first[0].lower()}{last.lower()}",
        f"{first.lower()}{random.randint(1, 99)}",
    ]
    base = random.choice(patterns)
    domain = random.choice(EMAIL_DOMAINS)
    email = f"{base}@{domain}"

    # Introduce email defect with ~12% probability
    if random.random() < 0.12:
        email = random.choice(EMAIL_DEFECTS)(email)

    return email


def generate_record(form_id: int) -> dict:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    full_name = f"{first} {last}"

    # Apply random casing transform
    full_name = random.choice(NAME_CASE_TRANSFORMS)(full_name)

    email = generate_email(first, last)

    country_pool = random.choice(list(COUNTRY_VARIANTS.values()))
    country = random.choice(country_pool)

    date = random_date()
    formatter = random.choice(DATE_FORMATTERS)
    created_at = formatter(date)

    source = random.choice(SOURCES)

    record = {
        "name": full_name,
        "email": email,
        "country": country,
        "created_at": created_at,
        "form_id": str(form_id),
        "source": source,
    }

    # Randomly null out a non-critical field
    if random.random() < NULL_FIELD_RATE:
        nullable = random.choice(["source", "country"])
        record[nullable] = None

    return record


def inject_duplicates(records: list, rate: float) -> list:
    n_dupes = int(len(records) * rate)
    dupes = random.choices(records, k=n_dupes)
    all_records = records + dupes
    random.shuffle(all_records)
    return all_records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    records = [generate_record(i + 1) for i in range(NUM_RECORDS)]
    records = inject_duplicates(records, DUPLICATE_RATE)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(records)} records ({NUM_RECORDS} base + ~{len(records)-NUM_RECORDS} duplicates)")
    print(f"Output: {os.path.abspath(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
