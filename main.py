
import os
import json
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_URL = os.getenv("KEITARO_URL")

def extract_offer_blocks(description):
    lines = description.splitlines()
    title_line = lines[0]
    attributes = {
        "id": title_line.strip(),
        "product": "", "geo": "", "payout": "", "currency": "",
        "cap": "", "source": "", "buyer": "", "pp": "", "links": []
    }

    current_label = None
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(label) for label in ["Продукт:", "Гео:", "Ставка:", "Валюта:", "Капа:", "Сорс:", "Баер:", "ПП:"]):
            key, value = line.split(":", 1)
            attributes[key.lower().strip()] = value.strip()
        elif line.startswith("http") or "http" in line:
            if "](" in line or "|" in line:
                parts = line.split("|")
                if len(parts) == 2:
                    attributes["links"].append((current_label or "NoName", parts[1].strip("]")))
            else:
                attributes["links"].append((current_label or "NoName", line.strip()))
        else:
            current_label = line.strip()

    return attributes

@app.post("/jira-to-keitaro")
async def jira_webhook(request: Request):
    payload = await request.json()
    issue = payload.get("issue", {})
    fields = issue.get("fields", {})
    description = fields.get("description", "")
    if not description:
        return {"error": "No description"}

    offer_data = extract_offer_blocks(description)
    responses = []

    for label, link in offer_data["links"]:
        offer_name = f"{offer_data['id']} - Продукт: {offer_data.get('продукт')} Гео: {offer_data.get('гео')} Ставка: {offer_data.get('ставка')} Валюта: {offer_data.get('валюта')} Капа: {offer_data.get('капа')} Сорс: {offer_data.get('сорс')} Баер: {offer_data.get('баер')} - {label}"
        country_code = offer_data.get("гео")
        data = {
            "name": offer_name,
            "action_payload": link,
            "country": [country_code] if country_code else [],
            "notes": f"PP: {offer_data.get('пп', '')}",
            "offer_type": "external",
            "action_type": "http"
        }

        headers = {
            "API-KEY": KEITARO_API_KEY,
            "Content-Type": "application/json"
        }

        try:
            r = httpx.post(f"{KEITARO_URL}/admin_api/v1/offers", headers=headers, json=data, timeout=10)
            responses.append({"status": r.status_code, "body": r.text})
        except Exception as e:
            responses.append({"error": str(e)})

    return {"results": responses}
