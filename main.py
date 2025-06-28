import os
import re
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

KEITARO_API_KEY = os.environ.get("KEITARO_API_KEY")
KEITARO_API_URL = os.environ.get("KEITARO_API_URL")


@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()

    summary = data.get("issue", {}).get("fields", {}).get("summary", "")
    description = data.get("issue", {}).get("fields", {}).get("description", "")

    offer = {
        "id": "",
        "product": "",
        "geo": "",
        "payout": "",
        "currency": "",
        "cap": "",
        "source": "",
        "buyer": "",
        "pp": "",
        "links": [],
    }

    offer["id"] = summary.strip()

    if isinstance(description, str):
        lines = description.splitlines()
    elif isinstance(description, dict):
        lines = []
        for block in description.get("content", []):
            if isinstance(block, dict) and block.get("type") == "paragraph":
                for inner in block.get("content", []):
                    if isinstance(inner, dict):
                        lines.append(inner.get("text", ""))
    else:
        lines = []

    for line in lines:
        if line.startswith("Продукт:"):
            offer["product"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Гео:"):
            offer["geo"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Ставка:"):
            offer["payout"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Валюта:"):
            offer["currency"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Капа:"):
            offer["cap"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Сорс:"):
            offer["source"] = line.split(":", 1)[-1].strip()
        elif line.startswith("Баер:"):
            offer["buyer"] = line.split(":", 1)[-1].strip()
        elif line.startswith("ПП:"):
            offer["pp"] = line.split(":", 1)[-1].strip()
        elif re.match(r"^https?://", line.strip()):
            name = "Link"
            offer["links"].append((name, line.strip()))
        elif re.match(r"^[A-Za-z0-9 ._-]+$", line.strip()) and len(offer["links"]) < 10:
            name = line.strip()
            offer["links"].append((name, ""))

    for name, url in offer["links"]:
        if not url:
            continue
        offer_name = f"{offer['id']} - Продукт: {offer['product']} Гео: {offer['geo']} Ставка: {offer['payout']} Валюта: {offer['currency']} Капа: {offer['cap']} Сорс: {offer['source']} Баер: {offer['buyer']} - {name}"
        payload = {
            "name": offer_name,
            "url": url,
            "group": offer["buyer"],
            "aff_network": offer["pp"],
            "redirect_type": "http"
        }
        headers = {
            "Api-Key": KEITARO_API_KEY,
            "Content-Type": "application/json"
        }
        requests.post(f"{KEITARO_API_URL}/admin_api/v1/offers", json=payload, headers=headers)

    return JSONResponse(content={"status": "completed"})