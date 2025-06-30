import os
import re
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_BASE_URL = os.getenv("KEITARO_BASE_URL")


def convert_country(geo):
    iso_map = {
        "PK": "Pakistan",
        "IN": "India",
        "ID": "Indonesia",
        "VN": "Vietnam",
        "BD": "Bangladesh"
    }
    return iso_map.get(geo.upper(), geo)


def extract_offers_from_description(description):
    pattern = re.compile(r"(?P<name>.+?)\n(?P<url>https?://[\w\-._~:/?#\[\]@!$&'()*+,;=%]+)", re.MULTILINE)
    return pattern.findall(description)


def parse_task_description(description):
    pattern = re.compile(
        r"id_prod\{(?P<id>\d+)} - Продукт:\s*(?P<product>.*?)\s*Гео:\s*(?P<geo>\w{2})\s*Ставка:\s*(?P<payout>\d+(\.\d+)?)\s*Валюта:\s*(?P<currency>\$|€|₽|USD|EUR|RUB)\s*Капа:\s*(?P<cap>\d+).*?Сорс:\s*(?P<source>.*?)\s*Баер:\s*(?P<buyer>@\w+)",
        re.DOTALL
    )
    match = pattern.search(description)
    if not match:
        return None, []

    groups = match.groupdict()
    offers = extract_offers_from_description(description)
    return groups, offers


async def create_keitaro_offer(offer_data):
    url = f"{KEITARO_BASE_URL}/offers"
    headers = {
        "API-KEY": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=offer_data)
        response.raise_for_status()
        return response.json()


@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    payload = await request.json()
    description = payload.get("issue", {}).get("fields", {}).get("description", "")
    groups, offers = parse_task_description(description)

    if not groups or not offers:
        return {"error": "Invalid task format or no offers found"}

    results = []

    for name, url in offers:
        offer_data = {
            "name": f"id_prod{{{groups['id']}}} - Продукт: {groups['product']} Гео: {groups['geo']} Ставка: {groups['payout']} Валюта: {groups['currency']} Капа: {groups['cap']} Сорс: {groups['source']} Баер: {groups['buyer']} - {name}",
            "action_type": "http",
            "action_payload": url,
            "offer_type": "external",
            "country": [convert_country(groups["geo"].strip())],
            "state": "active"
        }

        try:
            result = await create_keitaro_offer(offer_data)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e)})

    return {"results": results}
