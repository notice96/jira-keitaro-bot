
import os
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_API_URL = os.getenv("KEITARO_API_URL")

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()

    description = data.get("issue", {}).get("fields", {}).get("description", "")
    if isinstance(description, dict):
        description_blocks = description.get("content", [])
        description_text = ""
        for block in description_blocks:
            for inner in block.get("content", []):
                description_text += inner.get("text", "") + "\n"
    else:
        description_text = description

    print("\n=== Parsed Description Text ===\n", description_text)

    lines = [line.strip() for line in description_text.strip().splitlines() if line.strip()]
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

    for i, line in enumerate(lines):
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
        elif line.lower().startswith("http"):
            offer_data["links"].append({
                "title": lines[i - 1] if i > 0 else "Offer Link",
                "url": line
            })

    print("\n=== Parsed Offer Data ===", offer_data)

    headers = {
        "Api-Key": KEITARO_API_KEY,
        "Content-Type": "application/json"
    }

    for link in offer_data["links"]:
        name = f"{offer_data['id']} - Продукт: {offer_data['product']} Гео: {offer_data['geo']} Ставка: {offer_data['payout']} Валюта: {offer_data['currency']} Капа: {offer_data['cap']} Сорс: {offer_data['source']} Баер: {offer_data['buyer']} - {link['title']}"
        payload = {
            "name": name,
            "url": link["url"],
            "group": offer_data["pp"]
        }
        response = requests.post(f"{KEITARO_API_URL}/offers", json=payload, headers=headers)
        print(f"== Keitaro API response ({name}):", response.status_code, response.text)

    return JSONResponse(content={"status": "success"})
