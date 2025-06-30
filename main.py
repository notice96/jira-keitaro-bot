import os
import logging
from fastapi import FastAPI, Request
import requests

app = FastAPI()
logging.basicConfig(level=logging.INFO)

API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

@app.post("/")
async def handle_webhook(request: Request):
    data = await request.json()
    logging.info(f"Received data: {data}")

    description = data.get("issue", {}).get("fields", {}).get("description", "")
    if not description:
        logging.warning("No description found.")
        return {"status": "no description"}

    lines = description.splitlines()
    base_name = None
    product = geo = payout = currency = cap = source = buyer = pp = ""
    links = []
    current_label = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("id_prod"):
            base_name = line
        elif line.startswith("Продукт:"):
            product = line.split(":", 1)[1].strip()
        elif line.startswith("Гео:"):
            geo = line.split(":", 1)[1].strip()
        elif line.startswith("Ставка:"):
            payout = line.split(":", 1)[1].strip()
        elif line.startswith("Валюта:"):
            currency = line.split(":", 1)[1].strip()
        elif line.startswith("Капа:"):
            cap = line.split(":", 1)[1].strip()
        elif line.startswith("Сорс:"):
            source = line.split(":", 1)[1].strip()
        elif line.startswith("Баер:"):
            buyer = line.split(":", 1)[1].strip()
        elif line.startswith("ПП:"):
            pp = line.split(":", 1)[1].strip()
        elif line.endswith(":"):
            current_label = line[:-1]
        elif line.startswith("http") and current_label:
            links.append((current_label, line))
            current_label = ""

    if not base_name or not links:
        logging.warning("Missing base name or links.")
        return {"status": "insufficient data"}

    for label, url in links:
        offer_name = f"{base_name} - Продукт: {product} Гео: {geo} Ставка: {payout} Валюта: {currency} Капа: {cap} Сорс: {source} Баер: {buyer} - {label}"
        payload = {
            "name": offer_name,
            "affiliate_network_id": 0,
            "country": [geo],
            "state": "active",
            "action_type": "http",
            "action_payload": url,
            "offer_type": "external"
        }

        headers = {
            "API-KEY": API_KEY,
            "Content-Type": "application/json"
        }

        logging.info(f"Sending offer: {offer_name}")
        response = requests.post(API_URL, json=payload, headers=headers)
        logging.info(f"Response: {response.status_code} - {response.text}")

    return {"status": "processed", "offers_created": len(links)}