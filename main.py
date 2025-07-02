import os
import json
import re
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")

AFFILIATE_NETWORKS = {
    "ExGaming": 54,
    "Glory Partners": 14,
    "4RA PARTNER": 17
}

GROUPS = {
    "@dzho666": 28,
    "@alihmaaff": 26,
    "@berrnard": 36,
    "@d_traffq": 41,
    "@toni7977": 29,
    "@sequencezz": 40,
    "@iliia_xteam": 30,
    "@julikjar": 33
}

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    body = await request.json()

    print("\n=== Получен JSON от Jira ===")
    print(json.dumps(body, indent=2))

    issue = body.get("issue", {})
    description = issue.get("fields", {}).get("description", "")

    print("\n=== Description (описание задачи): ===")
    print(description)

    parsed_data = parse_offer_description(description)

    print("\n=== Распарсенные офферы: ===")
    print(parsed_data)

    if not parsed_data:
        return {"message": "No valid offer data found in Jira issue."}

    created_offers = []
    for offer in parsed_data:
        response = await create_keitaro_offer(offer)
        created_offers.append(response)

    return {"message": "Offers processed.", "results": created_offers}


def parse_offer_description(text):
    pattern = (
        r"id_prod\{(?P<id>\d+)}.*?Продукт:\s*(?P<product>.+?)\n"
        r"Гео:\s*(?P<geo>.+?)\nСтавка:\s*(?P<payout>.+?)\n"
        r"Валюта:\s*(?P<currency>.+?)\nКапа:\s*(?P<cap>.+?)\n"
        r"Сорс:\s*(?P<source>.+?)\nБаер:\s(?P<buyer>.+?)\nПП:\s*(?P<pp>.+?)\n"
        r"(?P<links_text>(?:.*?https?://[^\s]+)+)"
    )

    match = re.search(pattern, text, re.DOTALL)
    if not match:
        print("\n!!! Не удалось найти совпадение по регулярному выражению.")
        return

    groups = match.groupdict()
    print("\n=== Распознанные поля: ===")
    print(groups)

    links_section = groups["links_text"]
    link_matches = re.findall(r"(.+?)\n(https?://[^\s]+)", links_section)

    print("\n=== Найденные ссылки: ===")
    print(link_matches)

    offers = []
    for label, url in link_matches:
        clean_url = url.strip().split("|")[0]

        offer = {
            "name": f"id_prod{{{groups['id']}}} - Продукт: {groups['product']} Гео: {groups['geo']} "
                    f"Ставка: {groups['payout']} Валюта: {groups['currency']} Капа: {groups['cap']} "
                    f"Сорс: {groups['source']} Баер: {groups['buyer']} - {label.strip()}",
            "action_payload": clean_url,
            "country": [groups["geo"].strip().upper()],
            "notes": "",
            "action_type": "http",
            "offer_type": "external",
            "conversion_cap_enabled": False,
            "daily_cap": 0,
            "conversion_timezone": "UTC",
            "alternative_offer_id": 0,
            "values": "",
            "payout_value": float(groups["payout"]),
            "payout_currency": groups["currency"].strip(),
            "payout_type": "",
            "payout_auto": False,
            "payout_upsell": False,
            "affiliate_network_id": AFFILIATE_NETWORKS.get(groups["pp"].strip(), 0),
            "group_id": GROUPS.get(groups["buyer"].strip(), 0),
        }
        offers.append(offer)

    return offers


async def create_keitaro_offer(offer_data):
    url = KEITARO_BASE_URL
    headers = {
        "API-KEY": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    print("\n=== Отправка оффера в Keitaro ===")
    print(json.dumps(offer_data, indent=2))

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=offer_data)
        print("\n=== Ответ от Keitaro ===")
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")
        return {
            "status_code": response.status_code,
            "response": response.text
        }
