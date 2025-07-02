import os
import re
import httpx
from fastapi import FastAPI, Request
from bs4 import BeautifulSoup

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
    pattern = (
        r"id_prod\{(?P<id>\d+)}.*?Продукт:\s*(?P<product>.+?)\n"
        r"Гео:\s*(?P<geo>.+?)\nСтавка:\s*(?P<payout>.+?)\n"
        r"Валюта:\s*(?P<currency>.+?)\nКапа:\s*(?P<cap>.+?)\n"
        r"Сорс:\s*(?P<source>.+?)\nБаер:\s(?P<buyer>.+?)\nПП:(?P<pp>.+?)\n"
        r"ЛЕНД:\n(?P<links_text>.+)"
    )

    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return

    groups = match.groupdict()
    links_text = groups["links_text"].strip()

    # Подготовка текста как HTML для BeautifulSoup
    html = ""
    for line in links_text.split("\n"):
        if line.strip().startswith("http"):
            html += f'<a href="{line.strip()}">link</a>\n'
        else:
            html += f'<p>{line.strip()}</p>\n'

    soup = BeautifulSoup(html, "html.parser")
    descriptions = soup.find_all("p")
    links = soup.find_all("a")

    offers = []
    for desc, a in zip(descriptions, links):
        clean_url = a['href'].split("|")[0].strip()
        label = desc.get_text().strip()

        offer = {
            "name": f"id_prod{{{groups['id']}}} - Продукт: {groups['product']} Гео: {groups['geo']} "
                    f"Ставка: {groups['payout']} Валюта: {groups['currency']} Капа: {groups['cap']} "
                    f"Сорс: {groups['source']} Баер: {groups['buyer']} - {label}",
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
        }
        offers.append(offer)

    return offers


async def create_keitaro_offer(offer_data):
    url = KEITARO_BASE_URL
    headers = {
        "API-KEY": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=offer_data)
        return {
            "status_code": response.status_code,
            "response": response.text
        }
