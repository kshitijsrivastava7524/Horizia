import os
import requests
from dotenv import load_dotenv

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

    print("Status:", response.status_code)
    if response.status_code != 202:
        print("Error:", response.text)


# ---------- Example usage ----------
if __name__ == "__main__":
    send_email(
        subject="Horizia: ALERT!!",
        message="Test Email :)"
    )