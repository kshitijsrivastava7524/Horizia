import os
import json
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../data/history")


# ---------- LOAD HISTORY ----------
def load_history(site):
    site_path = os.path.join(DATA_DIR, site)

    if not os.path.exists(site_path):
        return []

    files = sorted([f for f in os.listdir(site_path) if f.endswith(".json")])

    history = []
    for f in files:
        with open(os.path.join(site_path, f)) as fp:
            data = json.load(fp)

            # handle nested or flat format
            area = data.get("lake_area_km2") or data.get("metrics", {}).get("lake_area_km2")
            coverage = data.get("lake_coverage_percent") or data.get("metrics", {}).get("lake_coverage_percent")

            if area is not None:
                history.append({
                    "area": area,
                    "coverage": coverage
                })

    return history


# ---------- RISK COMPUTATION ----------
def compute_risk(site):
    history = load_history(site)

    if len(history) < 3:
        return {"level": "LOW", "score": 0, "reason": "Not enough data"}

    areas = np.array([h["area"] for h in history])

    current = areas[-1]

    # ---------- Z-SCORE ----------
    mean = np.mean(areas)
    std = np.std(areas) if np.std(areas) > 1e-6 else 1e-6
    z = (current - mean) / std

    # ---------- TREND (SLOPE) ----------
    t = np.arange(len(areas))
    slope = np.polyfit(t, areas, 1)[0]

    # ---------- GROWTH ----------
    growth = areas[-1] - areas[-2]

    # ---------- ACCELERATION ----------
    if len(areas) >= 3:
        prev_growth = areas[-2] - areas[-3]
        acceleration = growth - prev_growth
    else:
        acceleration = 0

    # ---------- RELATIVE SIZE ----------
    max_area = np.max(areas)
    relative_size = current / max_area if max_area > 0 else 0

    # ---------- SCORE ----------
    score = (
        0.3 * abs(z) +
        0.2 * slope +
        0.2 * growth +
        0.2 * acceleration +
        0.1 * relative_size
    )

    # ---------- LEVEL ----------
    if score >= 3:
        level = "HIGH"
    elif score >= 1.5:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": float(score),
        "z": float(z),
        "slope": float(slope),
        "growth": float(growth),
        "acceleration": float(acceleration),
        "relative_size": float(relative_size)
    }