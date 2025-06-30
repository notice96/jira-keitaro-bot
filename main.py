import os
import re
import httpx
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")


class WebhookPayload(BaseModel):
    issue: dict


def extract_offer_data_from_description(description: str):
    offer_list = []
    lines = description.splitlines()

    current_name = None
    urls = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("http"):
            urls.append(line)
        else:
            if current_name and urls:
                offer_list.append((current_name, urls))
                urls = []
            current_name = line
    if current_name and urls:
        offer_list.append((current_name, urls))

    return offer_list


def build_offer_payload(summary: str, description: str, url: str, suffix: str = ""):
    offer_id_match = re.search(r'id_prod\{(\d+)\}', summary)
    offer_id = offer_id_match.group(1) if offer_id_match else "UNKNOWN"

    product_match = re.search(r'Продукт:\s+(.+?)\b', summary)
    product = product_match.group(1).strip() if product_match else ""

    geo_match = re.search(r'Гео:\s+([A-Z]{2})', summary)
    geo = geo_match.group(1).strip() if geo_match else ""

    payout_match = re.search(r'Ставка:\s+(\d+)', summary)
    payout = payout_match.group(1).strip() if payout_match else ""

    currency_match = re.search(r'Валюта:\s+(.+?)\b', summary)
    currency = currency_match.group(1).strip() if currency_match else ""

    cap_match = re.search(r'Капа:\s+(\d+)', summary)
    cap = cap_match.group(1).strip() if cap_match else ""

    name = f"id_prod{{{offer_id}}} - {summary.strip()} - {suffix}".strip()

    return {
        "name": name,
        "action_payload": url.split("|")[0].strip(),  # Удаляем часть с %7Bsubid%7D
        "country": [geo],
        "notes": description,
        "payout_value": int(payout) if payout.isdigit() else 0,
        "payout_currency": currency,
        "daily_cap": int(cap) if cap.isdigit() else 0,
        "state": "active",
        "payout_auto": False,
        "payout_upsell": False,
        "action_type": "http",
        "offer_type": "external",
        "conversion_cap_enabled": False,
        "conversion_timezone": "UTC",
    }


async def create_keitaro_offer(offer_data):
    url = f"{KEITARO_BASE_URL}/offers"
    headers = {
        "API-KEY": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=offer_data)
        return response.status_code, response.text


@app.get("/")
async def root():
    return {"message": "Server is running."}


@app.post("/jira-to-keitaro")
async def jira_to_keitaro(payload: WebhookPayload):
    summary = payload.issue["fields"]["summary"]
    description = payload.issue["fields"]["description"]

    offers = extract_offer_data_from_description(description)

    results = []
    for suffix, (label, urls) in enumerate(offers, 1):
        for url in urls:
            offer_data = build_offer_payload(summary, description, url, f"{label}")
            status, response = await create_keitaro_offer(offer_data)
            results.append({
                "label": label,
                "url": url,
                "status": status,
                "response": response
            })

    return {"created": results}