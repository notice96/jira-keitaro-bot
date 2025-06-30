
import os
import uvicorn
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def handle_jira_webhook(request: Request):
    payload = await request.json()

    issue = payload.get("issue", {})
    fields = issue.get("fields", {})
    description = fields.get("description", "")
    summary = fields.get("summary", "")

    if not description or not summary:
        return {"error": "Missing description or summary"}

    try:
        offer_data = parse_offer_data(description, summary)
        results = []
        for offer in offer_data:
            res = await create_offer_in_keitaro(offer)
            results.append(res)
        return {"status": "done", "offers_created": results}
    except Exception as e:
        return {"error": str(e)}

def parse_offer_data(description: str, summary: str):
    lines = description.splitlines()
    data = {}
    links = []
    titles = []

    for i, line in enumerate(lines):
        if line.startswith("id_prod"):
            data["id"] = line.strip()
        elif "Продукт:" in line:
            data["product"] = line.split("Продукт:")[1].strip()
        elif "Гео:" in line:
            data["geo"] = line.split("Гео:")[1].strip()
        elif "Ставка:" in line:
            data["payout"] = line.split("Ставка:")[1].strip()
        elif "Валюта:" in line:
            data["currency"] = line.split("Валюта:")[1].strip()
        elif "Капа:" in line:
            data["cap"] = line.split("Капа:")[1].strip()
        elif "Сорс:" in line:
            data["source"] = line.split("Сорс:")[1].strip()
        elif "Баер:" in line:
            data["buyer"] = line.split("Баер:")[1].strip()
        elif "ПП:" in line:
            data["pp"] = line.split("ПП:")[1].strip()
        elif line.startswith("http"):
            links.append(line.strip())
            titles.append(lines[i-1].strip() if i > 0 else "Без названия")

    offers = []
    for i, link in enumerate(links):
        name = f"{data.get('id', '')} - Продукт: {data.get('product', '')} Гео: {data.get('geo', '')} Ставка: {data.get('payout', '')} Валюта: {data.get('currency', '')} Капа: {data.get('cap', '')} Сорс: {data.get('source', '')} Баер: {data.get('buyer', '')} - {titles[i]}"
        offers.append({
            "name": name,
            "action_payload": link,
            "affiliate_network": data.get("pp", ""),
            "country": [iso_country(data.get("geo", ""))],
            "notes": description,
            "action_type": "http",
            "offer_type": "external",
            "state": "active"
        })
    return offers

def iso_country(code):
    mapping = {
        "PK": "Pakistan", "IN": "India", "UA": "Ukraine", "US": "United States"
    }
    return mapping.get(code.upper(), code)

async def create_offer_in_keitaro(offer):
    api_key = os.getenv("KEITARO_API_KEY")
    url = os.getenv("KEITARO_API_URL")
    headers = {
        "API-KEY": api_key,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=offer)
        return {"status_code": response.status_code, "response": response.text}
