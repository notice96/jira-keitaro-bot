from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

KEITARO_API_KEY = os.environ["KEITARO_API_KEY"]
KEITARO_API_URL = os.environ["KEITARO_API_URL"]
CAMPAIGN_ID = os.environ["CAMPAIGN_ID"]

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()
    issue = data.get("issue", {})
    summary = issue.get("fields", {}).get("summary", "No title")
    description = issue.get("fields", {}).get("description", "")

    links = [line.strip() for line in description.splitlines() if line.startswith("http")]

    for link in links:
        create_stream(summary, link)

    return {"status": "success", "streams_created": len(links)}

def create_stream(name, url):
    headers = {
        "Api-Key": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "campaign_id": int(CAMPAIGN_ID),
        "name": name,
        "action": "redirect",
        "url": url
    }
    r = requests.post(f"{KEITARO_API_URL}/admin_api/v1/streams", json=data, headers=headers)
    print(f"Keitaro response: {r.status_code} — {r.text}")
