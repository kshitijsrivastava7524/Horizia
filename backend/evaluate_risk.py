import sys
from risk_engine import compute_risk
from send_alert import send_email


def main(site):
    risk = compute_risk(site)

    print(f"[RISK] {site} -> {risk['level']} (score={risk['score']:.2f})")

    if risk["level"] == "HIGH":
        send_email(
            subject=f"Horizia ALERT: {site} HIGH RISK",
            message=f"""
Site: {site}
Risk Level: {risk['level']}
Score: {risk['score']:.2f}

Details:
Z-score: {risk['z']:.2f}
Growth: {risk['growth']:.4f}
Acceleration: {risk['acceleration']:.4f}
"""
        )
        print("[ALERT SENT]")
    else:
        print("[NO ALERT]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Site argument required")

    site = sys.argv[1]
    main(site)