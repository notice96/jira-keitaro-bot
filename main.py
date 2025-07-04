import os
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fastapi import FastAPI, Request

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")

AFFILIATE_NETWORKS = {
    "TSL": 55,
    "ExGaming": 54,
    "Sparta": 53,
    "Riddick’s Partners": 52,
    "Godlike Partners": 51,
    "1Win": 50,
    "21stGold": 49,
    "TRAFFLAB2": 48,
    "Glory Partners": 14,
    "4RA PARTNER": 17
    
}

OFFER_GROUPS = {
    "@alihmaaff": 26,
    "@berrnard": 36,
    "@d_traffq": 41,
    "@dzho666": 28,
    "@iliia_xteam": 30,
    "@julikjar": 33,
    "@sequencezz": 40,
    "@toni7977": 29
}

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    body = await request.json()
    issue = body.get("issue", {})
    fields = issue.get("fields", {})
    parsed_data = parse_offer_fields(fields)

    if not parsed_data:
        return {"message": "No valid offer data found in Jira issue."}

    created_offers = []
    for offer in parsed_data:
        response = await create_keitaro_offer(offer)
        created_offers.append(response)

    return {"message": "Offers processed.", "results": created_offers}

def parse_offer_fields(fields):
    try:
        offer_data = {
            "id": fields.get("summary", "").replace("id_prod{", "").replace("}", ""),
            "product": fields.get("customfield_10158", ""),
            "geo": fields.get("customfield_10157", "").upper(),
            "payout": fields.get("customfield_10190", ""),
            "currency": fields.get("customfield_10160", ""),
            "cap": fields.get("customfield_10161", ""),
            "source": fields.get("customfield_10162", ""),
            "buyer": fields.get("customfield_10163", ""),
            "pp": fields.get("customfield_10138", {}).get("value", ""),
            "links": fields.get("customfield_10165", "")
        }

        print("\n🧾 Спаршенные данные:")
        for k, v in offer_data.items():
            print(f"{k}: {v}")

        # Разбор ссылок
        links_text = offer_data["links"]
        lines = [line.strip() for line in links_text.splitlines() if line.strip()]
        print("\n🔗 Все строки из ссылок:")
        for idx, l in enumerate(lines):
            print(f"{idx + 1}: {l}")

        offers = []
        i = 1
        while i < len(lines):
            line = lines[i]
            if "http" in line:
                label = lines[i - 1]
                raw_url = line.strip("[]")
                if "|" in raw_url:
                    raw_url = raw_url.split("|")[0]
                clean_url = unquote(
                    raw_url.replace("⊂sub_id", "&sub_id").replace("⊂_id", "&sub_id")
                )

                try:
                    payout_value = float(offer_data["payout"])
                except (ValueError, TypeError):
                    print(f"⚠️ Ставка не число: {offer_data['payout']}, ставим 0")
                    payout_value = 0

                offer = {
                    "name": f"id_prod{{{offer_data['id']}}} - Продукт: {offer_data['product']} Гео: {offer_data['geo']} "
                            f"Ставка: {offer_data['payout']} Валюта: {offer_data['currency']} Капа: {offer_data['cap']} "
                            f"Сорс: {offer_data['source']}" + (f" Баер: {offer_data['buyer']}" if offer_data['buyer'] else '') + f" - {label}",
                    "action_payload": clean_url,
                    "country": [offer_data["geo"]],
                    "notes": "",
                    "action_type": "http",
                    "offer_type": "external",
                    "conversion_cap_enabled": False,
                    "daily_cap": 0,
                    "conversion_timezone": "UTC",
                    "alternative_offer_id": 0,
                    "values": "",
                    "payout_auto": True,  # ✅ Включаем параметр 'payout'
                    "payout_value": 0,    # ⬅️ Выплата не проставляется
                    "payout_currency": "",  # ⬅️ Валюта не проставляется
                    "payout_type": "cpa",   # ✅ Тип выплат = CPA
                    "payout_upsell": True,
                    "affiliate_network_id": AFFILIATE_NETWORKS.get(offer_data["pp"], 0),
                    "group_id": OFFER_GROUPS.get(offer_data["buyer"], 0)
                }
                print(f"\n✅ Оффер добавлен: {offer['name']}")
                offers.append(offer)
            i += 1

        if not offers:
            print("❌ Не найдено ни одного валидного оффера.")
        return offers

    except Exception as e:
        print("❌ Ошибка при парсинге Jira:", str(e))
        return []

async def create_keitaro_offer(offer_data):
    url = KEITARO_BASE_URL
    headers = {
        "API-KEY": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=offer_data)
            print("📦 Ответ от Keitaro:", response.status_code, response.text)
            return {
                "status_code": response.status_code,
                "response": response.text
            }
    except Exception as e:
        print("❌ Ошибка при отправке оффера в Keitaro:", str(e))
        return {
            "status_code": 500,
            "response": f"Ошибка при отправке оффера: {str(e)}"
        }
