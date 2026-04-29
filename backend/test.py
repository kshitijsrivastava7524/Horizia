import os
import json
import sys
from datetime import datetime, timedelta
from preprocess import normalize_stack
from fetch_data import fetch_data_fun
from run_model import main as run_unet
from visualize import generate_images

# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data/history")
STAGING_DIR = os.path.join(BASE_DIR, "../data/fetched_early")
STEP_DAYS = 14
FRESHNESS_THRESHOLD = 7
MAX_RECORDS = 15
SITES = ["site1", "site2", "site3", "site4"]


# ---------------- HELPERS ----------------

def get_last_date(site):
    path = os.path.join(DATA_DIR, site)
    if not os.path.exists(path):
        return None
    files = sorted([f for f in os.listdir(path) if f.endswith('.json')])
    if not files:
        return None
    return datetime.strptime(files[-1].replace(".json", ""), "%Y-%m-%d")


def save_data(site, date, result):
    site_path = os.path.join(DATA_DIR, site)
    os.makedirs(site_path, exist_ok=True)
    file_path = os.path.join(site_path, f"{date.strftime('%Y-%m-%d')}.json")

    with open(file_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[SAVE] {file_path}")
    cleanup(site)


def save_staging(site, date, metrics):
    path = os.path.join(STAGING_DIR, site)
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, f"{date.strftime('%Y-%m-%d')}.json")
    with open(file_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"[STAGING] {file_path}")


def cleanup(site):
    path = os.path.join(DATA_DIR, site)
    files = sorted([f for f in os.listdir(path) if f.endswith('.json')])
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

    # if not dates or dates[-1].date() != today.date():
    #     dates.append(today)

    return dates


# ---------------- PIPELINE ----------------

def run_model(processed_path, site, date):
    result = run_unet(
        stack_path=processed_path,
        site=site,
        date=date
    )
    return result

def fetch_and_process(site, date):
    print(f"[FETCH] {site} {date.date()}")

    raw_path = fetch_data_fun(site, date)

    if raw_path:
        processed_path = normalize_stack(raw_path, site, date)
        print(f"[PROCESSED] {processed_path}")
        return processed_path

    return None


def run_fetch_and_save(site, date):
    processed_path = fetch_and_process(site, date)

    if processed_path:
        result = run_model(processed_path, site, date)

        print(f"[OUTPUT] {result['prob_path']}")
        print(f"[OUTPUT] {result['binary_path']}")

        # Generate images
        generate_images(
            stack_path=processed_path,
            prob_path=result["prob_path"],
            binary_path=result["binary_path"],
            site=site,
            date=date
        )

        # Save metrics
        save_data(site, date, result["metrics"])

    else:
        print(f"[SKIP] No data saved for {site} on {date.date()}")


# ---------------- SYNC LOGIC ----------------

def sync_site(site):
    print(f"\n=== {site} ===")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    last_date = get_last_date(site)

    if last_date is None:
        print("First run — fetching historical data (15 dates, 14-day gaps)")
        for i in range(15):
            target_date = today - timedelta(days=i * 14)
            print(f"  Fetching for {target_date.date()}")
            run_fetch_and_save(site, target_date)
        return

    gap = (today - last_date).days
    print(f"Gap: {gap} days")

    if gap <= FRESHNESS_THRESHOLD:
        print("Fresh → skip")
        return

    elif gap < STEP_DAYS:
        print("Small gap → fetch to staging")
        processed_path = fetch_and_process(site, today)
        if processed_path:
            result = run_model(processed_path, site, today)
            generate_images(
                            stack_path=processed_path,
                            prob_path=result["prob_path"],
                            binary_path=result["binary_path"],
                            site=site,
                            date=today
                        )
            save_staging(site, today, result["metrics"])

    else:
        print("Large gap → backfill")
        dates = generate_dates(last_date, today)

        if len(dates) > MAX_RECORDS:
            print(f"[WARN] {len(dates)} dates generated, trimming to last {MAX_RECORDS}")
            dates = dates[-MAX_RECORDS:]

        for d in dates:
            run_fetch_and_save(site, d)

        if dates and dates[-1].date() != today.date():
            print("Remainder gap → staging today")
            processed_path = fetch_and_process(site, today)
            if processed_path:
                result = run_model(processed_path, site, today)
                generate_images(
                                stack_path=processed_path,
                                prob_path=result["prob_path"],
                                binary_path=result["binary_path"],
                                site=site,
                                date=today
                            )
                save_staging(site, today, result["metrics"])



def run_sync(sites):
    for site in sites:
        sync_site(site)


# ---------- ENTRY POINT ----------
if __name__ == "__main__":
    if len(sys.argv) > 1:
        requested = sys.argv[1]
        if requested not in SITES:
            print(f"[ERROR] Unknown site: {requested}. Valid sites: {SITES}")
            sys.exit(1)
        run_sync([requested])
    else:
        run_sync(SITES)