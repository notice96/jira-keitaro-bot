
import os
import json
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")


def parse_links_from_description(description):
    lines = description.splitlines()
    result = []
    current_title = ""
    for line in lines:
        if line.startswith("http"):
            result.append((current_title.strip(), line.strip()))
            current_title = ""
        else:
            current_title = line.strip()
    return result


def extract_fields(description):
    fields = {
        "product": "",
        "geo": "",
        "payout": "",
        "currency": "",
        "cap": "",
        "fd": "",
        "source": "",
        "buyer": ""
    }
    for line in description.splitlines():
        if "Продукт:" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part.startswith("Продукт:"):
                    fields["product"] = parts[i + 1] if i + 1 < len(parts) else ""
                if part.startswith("Гео:"):
                    fields["geo"] = parts[i + 1] if i + 1 < len(parts) else ""
                if part.startswith("Ставка:"):
                    fields["payout"] = parts[i + 1] if i + 1 < len(parts) else ""
                if part.startswith("Валюта:"):
                    fields["currency"] = parts[i + 1] if i + 1 < len(parts) else ""
                if part.startswith("Капа:"):
                    fields["cap"] = parts[i + 1] if i + 1 < len(parts) else ""
                if part.startswith("fd"):
                    fields["fd"] = part
                if part.startswith("Сорс:"):
                    fields["source"] = parts[i + 1] if i + 1 < len(parts) else ""
                if part.startswith("Баер:"):
                    fields["buyer"] = parts[i + 1] if i + 1 < len(parts) else ""
    return fields


def convert_country(geo):
    return geo.upper()


async def create_keitaro_offer(offer_data):
    url = f"{KEITARO_BASE_URL}/offers"
    headers = {
        "API-KEY": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=offer_data)
        return response.status_code, response.text


@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    payload = await request.json()
    issue = payload.get("issue", {})
    description = issue.get("fields", {}).get("description", "")
    issue_key = issue.get("key", "UNKNOWN")

    fields = extract_fields(description)
    links = parse_links_from_description(description)

    responses = []
    for idx, (title, link) in enumerate(links):
        name = f"id_prod{{{issue_key}}} - Продукт: {fields['product']} Гео: {fields['geo']} Ставка: {fields['payout']} Валюта: {fields['currency']} Капа: {fields['cap']} {fields['fd']} Сорс: {fields['source']} Баер: {fields['buyer']} - {title}"
        offer_data = {
            "name": name,
            "action_type": "http",
            "action_payload": link,
            "country": [convert_country(fields["geo"])],
            "offer_type": "external"
        }
        status, text = await create_keitaro_offer(offer_data)
        responses.append({"status": status, "response": text})

    return {"results": responses}
