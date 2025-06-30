import os
import json
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_API_URL = os.getenv("KEITARO_API_URL")

class JiraUser(BaseModel):
    displayName: str

class JiraIssueFields(BaseModel):
    description: str
    summary: str

class JiraIssue(BaseModel):
    key: str
    fields: JiraIssueFields

class JiraWebhookPayload(BaseModel):
    issue: JiraIssue
    user: JiraUser

def parse_offer_description(text: str):
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    data = {}
    links = []
    current_label = ""

    for line in lines:
        if line.lower().startswith("id_prod"):
            data["id"] = line
        elif line.startswith("Продукт:"):
            data["product"] = line.split("Продукт:")[1].strip()
        elif line.startswith("Гео:"):
            data["geo"] = line.split("Гео:")[1].strip()
        elif line.startswith("Ставка:"):
            data["payout"] = line.split("Ставка:")[1].strip()
        elif line.startswith("Валюта:"):
            data["currency"] = line.split("Валюта:")[1].strip()
        elif line.startswith("Капа:"):
            data["cap"] = line.split("Капа:")[1].strip()
        elif line.startswith("Сорс:"):
            data["source"] = line.split("Сорс:")[1].strip()
        elif line.startswith("Баер:"):
            data["buyer"] = line.split("Баер:")[1].strip()
        elif line.startswith("ПП:"):
            data["pp"] = line.split("ПП:")[1].strip()
        elif line.startswith("http"):
            if current_label:
                links.append((current_label, line.strip()))
                current_label = ""
        else:
            current_label = line.strip()
    data["links"] = links
    return data

def make_offer_payload(offer_data: dict, label: str, url: str):
    name = f"{offer_data['id']} - Продукт: {offer_data['product']} Гео: {offer_data['geo']} Ставка: {offer_data['payout']} Валюта: {offer_data['currency']} Капа: {offer_data['cap']} Сорс: {offer_data['source']} Баер: {offer_data['buyer']} - {label}"
    return {
        "name": name,
        "country": [offer_data["geo"]],
        "affiliate_network_id": 0,
        "payout_value": float(offer_data["payout"]),
        "payout_currency": offer_data["currency"],
        "payout_type": "",
        "notes": "",
        "state": "active",
        "payout_auto": False,
        "payout_upsell": False,
        "action_type": "http",
        "action_payload": url,
        "offer_type": "external",
        "conversion_cap_enabled": False,
        "daily_cap": 0,
        "conversion_timezone": "UTC",
        "alternative_offer_id": 0,
        "values": ""
    }

@app.post("/jira-to-keitaro")
async def handle_webhook(request: Request):
    payload = await request.json()
    data = JiraWebhookPayload(**payload)
    description = data.issue.fields.description
    parsed = parse_offer_description(description)

    created = []
    async with httpx.AsyncClient() as client:
        for label, link in parsed.get("links", []):
            offer_payload = make_offer_payload(parsed, label, link)
            res = await client.post(
                f"{KEITARO_API_URL}/offers",
                headers={
                    "API-KEY": KEITARO_API_KEY,
                    "Content-Type": "application/json"
                },
                json=offer_payload
            )
            created.append((res.status_code, res.text))
    return {"created": created}
