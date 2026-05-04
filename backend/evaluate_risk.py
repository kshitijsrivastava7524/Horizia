import sys
from risk_engine import compute_risk
from send_alert import send_email
import json


def main(site):
    risk = compute_risk(site)

    print(json.dumps({
        "status": "success",
        "level": risk["level"],
        "score": round(risk["score"], 2)
    }))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Site argument required")

    site = sys.argv[1]
    main(site)