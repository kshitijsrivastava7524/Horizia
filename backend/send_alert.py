import os
import requests
from dotenv import load_dotenv
import sys
import json

load_dotenv()

API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER = os.getenv("SENDER_EMAIL")

# split into list
RECEIVERS = os.getenv("RECEIVER_EMAILS", "").split(",")


def send_email(subject, message):
    if not API_KEY:
        raise ValueError("Missing SENDGRID_API_KEY")

    url = "https://api.sendgrid.com/v3/mail/send"

    payload = {
        "personalizations": [
            {
                "to": [{"email": SENDER}],
                "bcc": [{"email": email.strip()} for email in RECEIVERS if email.strip()]
            }
        ],
        "from": {"email": SENDER},
        "subject": subject,
        "content": [
            {
                "type": "text/plain",
                "value": message
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json=payload)

    
if __name__ == "__main__":
    try:
        site = sys.argv[1]
        level = sys.argv[2]

        send_email(
            subject=f"Horizia ALERT: {site} {level}",
            message=f"""
                Site: {site}
                Risk Level: {level}
                """
        )

        print(json.dumps({"status": "success"}))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))
        sys.exit(1)