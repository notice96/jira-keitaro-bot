from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

KEITARO_API_URL = os.getenv("KEITARO_API_URL")
KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()

    # Получаем описание как строку
    description = data.get("issue", {}).get("fields", {}).get("description", "")
    lines = description.splitlines()

    # Парсим строки
    offer_data = {
        "id": "",
        "product": "",
        "geo": "",
        "payout": "",
        "currency": "",
        "cap": "",
        "source": "",
        "buyer": "",
        "pp": "",
        "links": []
    }

    current_link_name = ""
    for line in lines:
        line = line.strip()
        if line.startswith("id_prod"):
            offer_data["id"] = line
        elif line.lower().startswith("продукт:"):
            offer_data["product"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("гео:"):
            offer_data["geo"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("ставка:"):
            offer_data["payout"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("валюта:"):
            offer_data["currency"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("капа:"):
            offer_data["cap"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("сорс:"):
            offer_data["source"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("баер:"):
            offer_data["buyer"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("пп:"):
            offer_data["pp"] = line.split(":", 1)[1].strip()
        elif line.startswith("http"):
            if current_link_name:
                offer_data["links"].append((current_link_name, line))
                current_link_name = ""
        elif line != "":
            current_link_name = line

    print("
=== Parsed Offer Data ===", offer_data)

    # Отправляем офферы в Keitaro
    headers = {
        "Api-Key": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    for link_name, link_url in offer_data["links"]:
        campaign_name = f'{offer_data["id"]} - Продукт: {offer_data["product"]} Гео: {offer_data["geo"]} Ставка: {offer_data["payout"]} Валюта: {offer_data["currency"]} Капа: {offer_data["cap"]} Сорс: {offer_data["source"]} Баер: {offer_data["buyer"]} - {link_name}'
        payload = {
            "name": campaign_name,
            "traffic_source_id": 1,
            "cost_value": offer_data["payout"],
            "cost_model": "CPA",
            "redirects": [{"url": link_url}]
        }
        try:
            response = requests.post(f"{KEITARO_API_URL}/campaigns", json=payload, headers=headers)
            print(f"
Keitaro API response: {response.status_code} {response.text}")
        except Exception as e:
            print(f"
Keitaro API exception: {str(e)}")

    return {"status": "done"}
