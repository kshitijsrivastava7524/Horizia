import os
import json
from datetime import datetime, timedelta
from preprocess import normalize_stack
from fetch_data import fetch_data

# ---------------- CONFIG ----------------
DATA_DIR = "../data/history"
STEP_DAYS = 14
FRESHNESS_THRESHOLD = 7
MAX_RECORDS = 15
SITES = ["site1", "site2", "site3", "site4"]


# ---------------- HELPERS ----------------

def get_last_date(site):
    path = os.path.join(DATA_DIR, site)
    if not os.path.exists(path):
        return None

    files = sorted(os.listdir(path))
    if not files:
        return None

    return datetime.strptime(files[-1].replace(".json", ""), "%Y-%m-%d")


def save_data(site, date, result):
    site_path = os.path.join(DATA_DIR, site)
    os.makedirs(site_path, exist_ok=True)

    file_path = os.path.join(site_path, f"{date.strftime('%Y-%m-%d')}.json")

    with open(file_path, "w") as f:
        json.dump(result, f)

    print(f"[SAVE] {file_path}")

    cleanup(site)


def cleanup(site):
    path = os.path.join(DATA_DIR, site)
    files = sorted(os.listdir(path))

    if len(files) <= MAX_RECORDS:
        return

    for f in files[:-MAX_RECORDS]:
        os.remove(os.path.join(path, f))
        print(f"[DELETE] {f}")


def generate_dates(last_date, today):
    dates = []
    current = last_date + timedelta(days=STEP_DAYS)

    while current <= today:
        dates.append(current)
        current += timedelta(days=STEP_DAYS)

    if not dates or dates[-1] != today:
        dates.append(today)

    return dates


# ---------------- MOCK PIPELINE ----------------
# Replace these with your real functions

def fetch_data(site, date):
    print(f"[FETCH] {site} {date.date()}")
    from preprocess import normalize_stack

def run_model():
    return {
        "lake_area_km2": 92.3,
        "coverage": 2.0
    }


# ---------------- SYNC LOGIC ----------------

def sync_site(site):
    print(f"\n=== {site} ===")

    today = datetime.now()
    last_date = get_last_date(site)

    if last_date is None:
        print("First run")
        fetch_data(site, today)
        result = run_model()
        save_data(site, today, result)
        return

    gap = (today - last_date).days
    print(f"Gap: {gap} days")

    if gap <= FRESHNESS_THRESHOLD:
        print("Fresh → skip")

    elif gap <= STEP_DAYS:
        print("Small gap → fetch today")
        fetch_data(site, today)
        result = run_model()
        save_data(site, today, result)

    else:
        print("Large gap → backfill")

        dates = generate_dates(last_date, today)

        if len(dates) > MAX_RECORDS:
            dates = dates[-MAX_RECORDS:]

        for d in dates:
            fetch_data(site, d)
            result = run_model()
            save_data(site, d, result)


def run_sync():
    for site in SITES:
        sync_site(site)


if __name__ == "__main__":
    run_sync()