from fastapi import FastAPI, Request
import requests
import os
import re

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    data = await request.json()
    description = data.get("issue", {}).get("fields", {}).get("description", "")
    if not description:
        return {"error": "No description found in the issue"}

    offer_id_match = re.search(r"id_prod\{(\d+)\}", description)
    product_match = re.search(r"Продукт:\s*(.*)", description)
    geo_match = re.search(r"Гео:\s*(.*)", description)
    payout_match = re.search(r"Ставка:\s*(.*)", description)
    currency_match = re.search(r"Валюта:\s*(.*)", description)
    cap_match = re.search(r"Капа:\s*(.*)", description)
    source_match = re.search(r"Сорс:\s*(.*)", description)
    buyer_match = re.search(r"Баер:\s*(.*)", description)
    network_match = re.search(r"ПП:\s*(.*)", description)
    links = re.findall(r"(https?://[^\s]+)", description)

    if not (offer_id_match and product_match and geo_match and payout_match and currency_match and links):
        return {"error": "Missing required fields in description"}

    offer_id = offer_id_match.group(1)
    product = product_match.group(1).strip()
    geo = geo_match.group(1).strip()
    payout = float(payout_match.group(1).strip())
    currency = currency_match.group(1).strip()
    cap = cap_match.group(1).strip() if cap_match else ""
    source = source_match.group(1).strip() if source_match else ""
    buyer = buyer_match.group(1).strip() if buyer_match else ""
    network = network_match.group(1).strip() if network_match else ""

    results = []
    for link in links:
        prefix_match = re.search(r"https?://[^\s]+\n(.*)", description)
        prefix = prefix_match.group(1).strip() if prefix_match else ""
        name = f"id_prod{{{offer_id}}} - Продукт: {product} Гео: {geo} Ставка: {payout} Валюта: {currency} Капа: {cap} Сорс: {source} Баер: {buyer} - {prefix}"

        payload = {
            "name": name,
            "affiliate_network": network,
            "action_type": "http",
            "action_payload": link,
            "payout_value": payout,
            "payout_currency": currency,
            "payout_type": "fixed",
            "country": [geo],
            "state": "active",
            "offer_type": "external",
        }

        headers = {
            "API-KEY": os.getenv("KEITARO_API_KEY"),
            "Content-Type": "application/json"
        }

        response = requests.post(os.getenv("KEITARO_API_URL"), json=payload, headers=headers)
        results.append(response.json())

    return {"status": "done", "results": results}