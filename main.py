
import os
import re
import requests
from fastapi import FastAPI, Request

app = FastAPI()

KEITARO_API_URL = os.getenv("KEITARO_API_URL")
KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")


def parse_offer(description: str):
    result = {
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

    lines = [line.strip() for line in description.strip().split("\n") if line.strip()]
    current_label = ""
    for line in lines:
        if line.startswith("id_prod{"):
            result["id"] = line
        elif line.startswith("Продукт:"):
            result["product"] = line.replace("Продукт:", "").strip()
        elif line.startswith("Гео:"):
            result["geo"] = line.replace("Гео:", "").strip()
        elif line.startswith("Ставка:"):
            result["payout"] = line.replace("Ставка:", "").strip()
        elif line.startswith("Валюта:"):
            result["currency"] = line.replace("Валюта:", "").strip()
        elif line.startswith("Капа:"):
            result["cap"] = line.replace("Капа:", "").strip()
        elif line.startswith("Сорс:"):
            result["source"] = line.replace("Сорс:", "").strip()
        elif line.startswith("Баер:"):
            result["buyer"] = line.replace("Баер:", "").strip()
        elif line.startswith("ПП:"):
            result["pp"] = line.replace("ПП:", "").strip()
        elif re.match(r"^(https?://)", line):
            result["links"].append((current_label, line))
        else:
            current_label = line

    return result


@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()

    description = data.get("issue", {}).get("fields", {}).get("description", "")
    if not isinstance(description, str):
        return {"error": "Invalid description format."}

    parsed = parse_offer(description)

    print("\n=== Parsed Offer Data ===", parsed)

    for label, url in parsed["links"]:
        offer_name = f"{parsed['id']} - Продукт: {parsed['product']} Гео: {parsed['geo']} Ставка: {parsed['payout']} Валюта: {parsed['currency']} Капа: {parsed['cap']} Сорс: {parsed['source']} Баер: {parsed['buyer']} - {label}"

        payload = {
            "name": offer_name,
            "url": url,
            "affiliate_network_name": parsed["pp"],
            "geo": [parsed["geo"]],
            "payout_value": parsed["payout"],
            "payout_currency": parsed["currency"],
            "notes": f"Buyer: {parsed['buyer']} | Cap: {parsed['cap']} | Source: {parsed['source']}"
        }

        headers = {
            "Api-Key": KEITARO_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(
            KEITARO_API_URL + "offers",
            json=payload,
            headers=headers
        )

        print(f"\n=== Keitaro Response [{url}] ===", response.status_code, response.text)

    return {"status": "completed"}
