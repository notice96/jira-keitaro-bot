from fastapi import FastAPI, Request
import httpx
import re
import os

app = FastAPI()

KEITARO_API_URL = "https://your-keitaro-domain/admin_api/v1/offers"
KEITARO_API_KEY = "0ed98ed7f659004f3f7e68e68984b2fa"

def parse_offer_data(description: str, title: str):
    data = {
        "title": title,
        "notes": description
    }

    product_match = re.search(r"Продукт: (.+)", description)
    geo_match = re.search(r"Гео: (.+)", description)
    payout_match = re.search(r"Ставка: (.+)", description)
    currency_match = re.search(r"Валюта: (.+)", description)
    cap_match = re.search(r"Капа: (.+)", description)
    source_match = re.search(r"Сорс: (.+)", description)
    buyer_match = re.search(r"Баер: (.+)", description)
    pp_match = re.search(r"ПП:(.+)", description)
    reg_link_match = re.search(r"Reg\.Form\s*(https?://\S+)", description)
    wheel_link_match = re.search(r"Wheel Girls\s*(https?://\S+)", description)

    if product_match:
        data["product"] = product_match.group(1).strip()
    if geo_match:
        data["geo"] = geo_match.group(1).strip()
    if payout_match:
        data["payout"] = payout_match.group(1).strip()
    if currency_match:
        data["currency"] = currency_match.group(1).strip()
    if cap_match:
        data["cap"] = cap_match.group(1).strip()
    if source_match:
        data["source"] = source_match.group(1).strip()
    if buyer_match:
        data["buyer"] = buyer_match.group(1).strip()
    if pp_match:
        data["pp"] = pp_match.group(1).strip()
    if reg_link_match:
        data["reg_link"] = reg_link_match.group(1).strip()
    if wheel_link_match:
        data["wheel_link"] = wheel_link_match.group(1).strip()

    return data

@app.get("/")
async def root():
    return {"message": "Hello from Railway"}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    payload = await request.json()
    issue = payload.get("issue", {})
    title = issue.get("fields", {}).get("summary", "")
    description = issue.get("fields", {}).get("description", "")

    offer_data = parse_offer_data(description, title)

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {KEITARO_API_KEY}"}
        response = await client.post(KEITARO_API_URL, json=offer_data, headers=headers)

    return {"status": "sent", "response_status": response.status_code}