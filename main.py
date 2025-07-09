import os
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fastapi import FastAPI, Request

app = FastAPI()

# ✅ Данные для Keitaro
KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")

# ✅ Данные для Telegram
TELEGRAM_BOT_TOKEN = "8164983384:AAEwkdYx-tdmc5oqj4KL6MtR7pfkY0e0qMw"
TELEGRAM_CHAT_ID = "-1002430721164"

def log_field(field_name, value):
    print(f"🔍 {field_name}: {value if value else '[ПУСТО]'}")

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
    fields = body.get("issue", {}).get("fields", {})

    parsed_data = parse_offer_fields(fields)

    if not parsed_data:
        return {"message": "No valid offer data found in Jira issue."}

    created_offers = []
    for offer in parsed_data:
        response = await create_keitaro_offer(offer)
        created_offers.append(response)
        await send_telegram_message(parsed_data, offer)

    return {"message": "Offers processed.", "results": created_offers}

def parse_offer_fields(fields):
    try:
        offer_data = {
            "id": (fields.get("summary") or "").split("{")[-1].split("}")[0],
            "product": (fields.get("customfield_10158") or "").strip(),  # ✅ Продукт из ПП
            "geo": (fields.get("customfield_10157") or "").strip().upper(),
            "payout": str(fields.get("customfield_10190") or "").strip(),
            "currency": (fields.get("customfield_10160") or "").strip(),
            "cap": (fields.get("customfield_10161") or "").strip(),
            "source": (fields.get("customfield_10162") or "").strip(),
            "buyer": (fields.get("customfield_10163", {}) or {}).get("value", "").strip(),
            "pp": (fields.get("customfield_10138", {}) or {}).get("value", "").strip()
        }

        print("\n🧾 Спаршенные данные:")
        for k, v in offer_data.items():
            log_field(k, v)

        soup = BeautifulSoup(fields.get("customfield_10165", ""), "html.parser")
        lines = [line.strip() for line in soup.get_text().splitlines() if line.strip()]

        print("\n🌐 Все строки из ссылок:")
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

                clean_url = unquote(raw_url.replace("⊂_id", "&sub_id"))

                if i + 1 < len(lines) and ("sub_id" in lines[i + 1] or "⊂" in lines[i + 1]):
                    param_line = lines[i + 1].strip("[]")
                    if "|" in param_line:
                        param_line = param_line.split("|")[0]
                    decoded = unquote(param_line.replace("⊂_id", "&sub_id"))
                    clean_url += "&" + decoded if not decoded.startswith("&") else decoded
                    i += 1

                buyer_part = f" 👤 Баер: {offer_data['buyer']}" if offer_data["buyer"] else ""

                offer = {
                    "name": f"id_prod{{{offer_data['id']}}} - Продукт: {offer_data['product']} Гео: {offer_data['geo']} "
                            f"Ставка: {offer_data['payout']} Валюта: {offer_data['currency']} Капа: {offer_data['cap']} "
                            f"Сорс: {offer_data['source']}{buyer_part} - {label}",
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
                    "payout_value": 0,
                    "payout_currency": "",
                    "payout_auto": True,
                    "payout_upsell": True,
                    "payout_type": "CPA",
                    "affiliate_network_id": AFFILIATE_NETWORKS.get(offer_data["pp"], 0),
                    "group_id": OFFER_GROUPS.get(offer_data["buyer"], 0) if offer_data["buyer"] else 0
                }
                print(f"\n✅ Оффер добавлен: {offer['name']}")
                offers.append(offer)
            i += 1

        if not offers:
            print("❌ Не найдено ни одного валидного оффера.")
        return offers

    except Exception as e:
        print("❌ Ошибка при обработке полей:", str(e))
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
            return response.json()
    except Exception as e:
        print("❌ Ошибка при отправке оффера в Keitaro:", str(e))
        return {"error": str(e)}


async def send_telegram_message(parsed_info, offer):
    id_str = parsed_info["id"]
    product = parsed_info["product"]
    geo = parsed_info["geo"]
    payout = parsed_info["payout"]
    currency = parsed_info["currency"]
    cap = parsed_info["cap"]
    source = parsed_info["source"]
    buyer = parsed_info["buyer"]

    buyer_part = f"\n👤 Баер: {buyer}" if buyer else ""

    message_text = (
        f"🎯 Новый оффер успешно создан в Keitaro:\n\n"
        f"📌 id_prod{{{id_str}}}\n"
        f"🤝 Продукт: {product}\n"
        f"🌍 Гео: {geo}\n"
        f"💰 Ставка: {payout} {currency}\n"
        f"📈 Капа: {cap}\n"
        f"📲 Сорс: {source}"
        f"{buyer_part}"
    )

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(TELEGRAM_API_URL, json=payload)
            print("📤 Результат отправки:", response.json())
    except Exception as e:
        print("❌ Ошибка при отправке сообщения в Telegram:", str(e))
