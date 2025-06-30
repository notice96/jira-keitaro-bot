from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    data = await request.json()

    description = data.get("issue", {}).get("fields", {}).get("description", "")
    if not description:
        return {"error": "No description found."}

    # Разбор ID
    import re
    match = re.search(r"id_prod\{(\d+)}", description)
    offer_id = match.group(1) if match else "000"

    # Парсинг данных
    def extract_value(label):
        match = re.search(rf"{label}:\s*(.+)", description)
        return match.group(1).strip() if match else ""

    product = extract_value("Продукт")
    geo = extract_value("Гео")
    payout = extract_value("Ставка")
    currency = extract_value("Валюта")
    cap = extract_value("Капа")
    source = extract_value("Сорс")
    buyer = extract_value("Баер")
    network = extract_value("ПП")

    # Все ссылки
    links = re.findall(r'(https?://[^\s]+)', description)
    offers = []

    for link in links:
        # Название из текста до ссылки
        name_match = re.search(r'([^\n]+)\n%s' % re.escape(link), description)
        suffix = name_match.group(1).strip() if name_match else ""

        offer_name = f"id_prod{{{offer_id}}} - Продукт: {product} Гео: {geo} Ставка: {payout} Валюта: {currency} Капа: {cap} Сорс: {source} Баер: {buyer} - {suffix}"

        offer_payload = {
            "name": offer_name,
            "country": [geo],
            "payout_value": float(payout),
            "payout_currency": currency,
            "payout_type": "",
            "state": "active",
            "payout_auto": False,
            "payout_upsell": False,
            "notes": "",
            "action_type": "http",
            "action_payload": link,
            "offer_type": "external",
            "affiliate_network": network
        }

        keitaro_url = os.getenv("KEITARO_API_URL")
        keitaro_key = os.getenv("KEITARO_API_KEY")

        headers = {
            "API-KEY": keitaro_key,
            "Content-Type": "application/json"
        }

        response = requests.post(keitaro_url, json=offer_payload, headers=headers)
        offers.append(response.json())

    return {"status": "created", "offers": offers}
