import os
import json
import httpx
from bs4 import BeautifulSoup
from urllib.parse import unquote
from fastapi import FastAPI, Request

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")

TELEGRAM_BOT_TOKEN = "7529472112:AAHtTIBHuv320tPGkU7632m7lKLVhEK4fdQ"  # твой токен
TELEGRAM_CHAT_ID = "-1002430721164"  # id твоего канала
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

AFFILIATE_NETWORKS = {
    "Fonbet Partners": 58,
    "Elon Casino": 57,
    "Fame.space": 56,
    "TSL": 55,
    "ExGaming": 54,
    "Sparta": 53,
    "Riddick’s Partners": 52,
    "Godlike Partners": 51,
    "1Win": 50,
    "21stGold": 49,
    "TRAFFLAB2": 48,
    "Nexus": 47,
    "convert-it": 46,
    "Royal Partners": 45,
    "Traffic Cake": 44,
    "PMaffiliates": 43,
    "PD partners": 42,
    "Bananza": 41,
    "ClickLead": 40,
    "Betoholic": 39,
    "Lotoclub": 38,
    "Yesplay": 37,
    "AffAvenue": 36,
    "1Xbet": 35,
    "paripesa": 34,
    "3Snet": 33,
    "Jim partners": 32,
    "MelBet": 31,
    "Mostbet Partners": 30,
    "CoolAffs": 29,
    "KeyAffiliates": 28,
    "YYY": 27,
    "Dugika": 26,
    "INSIDE": 25,
    "Spinarium": 24,
    "Wilddicecasino": 23,
    "Wewe media": 22,
    "MB.Partners": 21,
    "Space Partners": 20,
    "Unoaffiliates": 19,
    "LEON": 18,
    "4RA PARTNER": 17,
    "Monta partners": 16,
    "Growe Partners": 15,
    "Glory Partners": 14,
    "Chilli partners": 13,
    "Betmen": 12,
    "Q-affs": 11,
    "Wow Partners": 10,
    "Profitov.Partners": 8,
    "Cell.expert": 7,
    "Con-fluence.agency": 6,
    "Gamefun": 5,
    "Advertise.net": 4,
    "trafflab": 3,
    "Q3.network": 2,
    "Gagarin.partners": 1
}

OFFER_GROUPS = {
    "@dimapizzaeater69": 48,
    "@g13lv": 45,
    "@swh1t3": 43,
    "@sam1_337": 44,
    "@alihmaaff": 26,
    "@berrnard": 36,
    "@d_traffq": 41,
    "@dzho666": 28,
    "@iliia_xteam": 30,
    "@julikjar": 33,
    "@sequencezz": 40
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
    sent_ids = set()  # 🟣 Чтобы не отправлять повторно

    for offer in parsed_data:
        response = await create_keitaro_offer(offer)
        created_offers.append(response)

        offer_id = fields.get("summary", "").split("{")[-1].split("}")[0]
        if offer_id not in sent_ids:
            sent_ids.add(offer_id)
            print("📨 Отправляем уведомление в Telegram...")
            await send_telegram_message(fields)

    return {"message": "Offers processed.", "results": created_offers}

def parse_offer_fields(fields):
    try:
        offer_data = {
            "id": fields.get("summary", "").split("{")[-1].split("}")[0],
            "product": fields.get("customfield_10158", "").strip(),
            "geo": fields.get("customfield_10157", "").strip().upper(),
            "payout": str(fields.get("customfield_10190", "")).strip(),
            "currency": fields.get("customfield_10160", "").strip(),
            "cap": fields.get("customfield_10161", "").strip(),
            "source": fields.get("customfield_10162", "").strip(),
            "buyer": ((fields.get("customfield_10163") or {}).get("value", "")),
            "pp": fields.get("customfield_10138", {}).get("value", "").strip()
        }

        print("\n🧾 Спаршенные данные:")
        for k, v in offer_data.items():
            print(f"{k}: {v}")

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
                    if decoded.startswith("&"):
                        clean_url += decoded
                    else:
                        clean_url += "&" + decoded
                    i += 1

                buyer_part = f" Баер: {offer_data['buyer']}" if offer_data["buyer"] else ""

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


async def send_telegram_message(parsed_info):
    try:
        message_text = (
            f"🎯 Новый оффер успешно создан в Keitaro:\n\n"
            f"📌 id_prod{{{parsed_info['summary'].split('{')[-1].split('}')[0]}}}\n"
            f"🤝 Продукт: {parsed_info.get('customfield_10158', '[ПУСТО]')}\n"
            f"🌍 Гео: {parsed_info.get('customfield_10157', '[ПУСТО]')}\n"
            f"💰 Ставка: {parsed_info.get('customfield_10190', '[ПУСТО]')} {parsed_info.get('customfield_10160', '[ПУСТО]')}\n"
            f"📈 Капа: {parsed_info.get('customfield_10161', '[ПУСТО]')}\n"
            f"📲 Сорс: {parsed_info.get('customfield_10162', '[ПУСТО]')}\n"
            f"👤 Баер: {((parsed_info.get('customfield_10163') or {}).get('value', '[ПУСТО]'))}"
        )

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message_text,
            "parse_mode": "HTML"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(TELEGRAM_API_URL, json=payload)
            print("📤 Telegram ответ:", response.status_code, response.text)

    except Exception as e:
        print(f"❌ Ошибка при отправке сообщения в Telegram: {e}")
