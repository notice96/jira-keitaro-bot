from fastapi import FastAPI, Request
from pydantic import BaseModel
import httpx
import re

app = FastAPI()

KEITARO_API_KEY = "0ed98ed7f659004f3f7e68e68984b2fa"
KEITARO_BASE_URL = "http://77.221.155.15/admin_api/v1"

class JiraWebhookPayload(BaseModel):
    issue: dict

def extract_offer_data(description: str):
    patterns = {
        "product": r"Продукт:\s*(.+)",
        "geo": r"Гео:\s*(.+)",
        "payout": r"Ставка:\s*(.+)",
        "currency": r"Валюта:\s*(.+)",
        "cap": r"Капа:\s*(.+)",
        "source": r"Сорс:\s*(.+)",
        "buyer": r"Баер:\s*(.+)",
        "pp": r"ПП:\s*(.+)",
    }
    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, description)
        if match:
            extracted[key] = match.group(1).strip()
    return extracted

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    data = await request.json()
    issue = data.get("issue", {})
    title = issue.get("fields", {}).get("summary", "")
    description = issue.get("fields", {}).get("description", "")
    print("=== JIRA Summary ===", title)
    print("=== JIRA Description ===", description)

    offer_data = extract_offer_data(description)
    print("=== Parsed Offer Data ===", offer_data)

    if not offer_data:
        return {"status": "error", "detail": "No valid data extracted from Jira description"}

    headers = {"Api-Key": KEITARO_API_KEY}
    payload = {
        "name": title,
        "notes": description,
        "country": offer_data.get("geo", ""),
        "payout_value": offer_data.get("payout", ""),
        "currency": offer_data.get("currency", "$"),
        "status": "active"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{KEITARO_BASE_URL}/offers", json=payload, headers=headers)
            print("=== Keitaro Response ===", response.status_code, response.text)
            response.raise_for_status()
            return {"status": "success", "response": response.json()}
    except Exception as e:
        print("=== ERROR while sending to Keitaro ===", str(e))
        return {"status": "error", "detail": str(e)}