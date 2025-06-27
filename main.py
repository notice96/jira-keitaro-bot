from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

KEITARO_API_KEY = os.environ["KEITARO_API_KEY"]
KEITARO_API_URL = os.environ["KEITARO_API_URL"]

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()
    issue = data.get("issue", {})
    summary = issue.get("fields", {}).get("summary", "No title")
    description = issue.get("fields", {}).get("description", "")

    links = [line.strip() for line in description.splitlines() if line.startswith("http")]

    for link in links:
        create_offer(summary, link, description)

    return {"status": "success", "offers_created": len(links)}

def create_offer(name, url, notes):
    headers = {
        "Api-Key": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "url": url,
        "notes": notes,
        "group_id": None
    }
    r = requests.post(f"{KEITARO_API_URL}/admin_api/v1/offers", json=data, headers=headers)
    print(f"Keitaro offer response: {r.status_code} — {r.text}")
