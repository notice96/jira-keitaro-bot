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
    "ExGaming": 54,
    "Glory Partners": 14,
    "4RA PARTNER": 17
}

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    body = await request.json()
    issue = body.get("issue", {})
    description = issue.get("fields", {}).get("description", "")
    parsed_data = parse_offer_description(description)

    if not parsed_data:
        return {"message": "No valid offer data found in Jira issue."}

    created_offers = []
    for offer in parsed_data:
        response = await create_keitaro_offer(offer)
        created_offers.append(response)

    return {"message": "Offers processed.", "results": created_offers}


def parse_offer_description(text):
    try:
        soup = BeautifulSoup(text, "html.parser")
        lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]

        print("📥 Все строки из задачи Jira:")
        for idx, l in enumerate(lines):
            print(f"{idx + 1}: {l}")

        offer_data = {
            "id": "", "product": "", "geo": "", "payout": "",
            "currency": "", "cap": "", "source": "", "buyer": "", "pp": ""
        }

        for line in lines:
            if line.startswith("id_prod{"):
                offer_data["id"] = line.split("{")[1].split("}")[0]
            elif line.startswith("Продукт:"):
                offer_data["product"] = line.replace("Продукт:", "").strip()
            elif line.startswith("Гео:"):
                offer_data["geo"] = line.replace("Гео:", "").strip().upper()
            elif line.startswith("Ставка:"):
                offer_data["payout"] = line.replace("Ставка:", "").strip()
            elif line.startswith("Валюта:"):
                offer_data["currency"] = line.replace("Валюта:", "").strip()
            elif line.startswith("Капа:"):
                offer_data["cap"] = line.replace("Капа:", "").strip()
            elif line.startswith("Сорс:"):
                offer_data["source"] = line.replace("Сорс:", "").strip()
            elif line.startswith("Баер:"):
                offer_data["buyer"] = line.replace("Баер:", "").strip()
            elif line.startswith("ПП:"):
                offer_data["pp"] = line.replace("ПП:", "").strip()

        print("\n🧾 Спаршенные данные:")
        for k, v in offer_data.items():
            print(f"{k}: {v}")

        offers = []
        for i in range(1, len(lines)):
            line = lines[i]
            if "http" in line:
                label = lines[i - 1]

                # ✅ Очистка и декодирование ссылки
                raw_url = line.strip("[]").split("|")[0]
                clean_url = unquote(
                    raw_url.replace("⊂_id", "&sub_id")  # 💡 фиксируем ломанные ссылки
                )

                try:
                    payout_value = float(offer_data["payout"])
                except ValueError:
                    print(f"❌ Ошибка: ставка ('Ставка') не число: {offer_data['payout']}")
                    continue

                offer = {
                    "name": f"id_prod{{{offer_data['id']}}} - Продукт: {offer_data['product']} Гео: {offer_data['geo']} "
                            f"Ставка: {offer_data['payout']} Валюта: {offer_data['currency']} Капа: {offer_data['cap']} "
                            f"Сорс: {offer_data['source']} Баер: {offer_data['buyer']} - {label}",
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
                    "payout_value": payout_value,
                    "payout_currency": offer_data["currency"],
                    "payout_type": "",
                    "payout_auto": False,
                    "payout_upsell": False,
                    "affiliate_network_id": AFFILIATE_NETWORKS.get(offer_data["pp"], 0),
                }
                print(f"\n✅ Оффер добавлен: {offer['name']}")
                offers.append(offer)

        if not offers:
            print("❌ Не найдено ни одного валидного оффера.")
        return offers

    except Exception as e:
        print("❌ Общая ошибка при парсинге задачи Jira:", str(e))
        print("📄 Содержимое задачи:\n", text)
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
