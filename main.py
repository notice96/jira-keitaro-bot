
from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    data = await request.json()
    issue = data.get("issue", {})
    fields = issue.get("fields", {})
    description = fields.get("description", "")
    if not description:
        return {"error": "No description found."}

    lines = description.splitlines()
    base_fields = {
        "id": "", "product": "", "geo": "", "payout": "", "currency": "",
        "cap": "", "source": "", "buyer": "", "pp": ""
    }
    offer_links = []
    current_label = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("id_prod"):
            base_fields["id"] = line.strip()
        elif line.startswith("Продукт:"):
            base_fields["product"] = line.replace("Продукт:", "").strip()
        elif line.startswith("Гео:"):
            base_fields["geo"] = line.replace("Гео:", "").strip()
        elif line.startswith("Ставка:"):
            base_fields["payout"] = line.replace("Ставка:", "").strip()
        elif line.startswith("Валюта:"):
            base_fields["currency"] = line.replace("Валюта:", "").strip()
        elif line.startswith("Капа:"):
            base_fields["cap"] = line.replace("Капа:", "").strip()
        elif line.startswith("Сорс:"):
            base_fields["source"] = line.replace("Сорс:", "").strip()
        elif line.startswith("Баер:"):
            base_fields["buyer"] = line.replace("Баер:", "").strip()
        elif line.startswith("ПП:"):
            base_fields["pp"] = line.replace("ПП:", "").strip()
        elif line.startswith("http"):
            offer_links.append((current_label or "Link"), line)
        else:
            current_label = line

    created_offers = []

    for label, link in offer_links:
        offer_name = f"{base_fields['id']} - Продукт: {base_fields['product']} Гео: {base_fields['geo']} Ставка: {base_fields['payout']} Валюта: {base_fields['currency']} Капа: {base_fields['cap']} Сорс: {base_fields['source']} Баер: {base_fields['buyer']} - {label}"
        payload = {
            "name": offer_name,
            "country": [base_fields["geo"]],
            "affiliate_network": base_fields["pp"],
            "payout_value": float(base_fields["payout"]) if base_fields["payout"] else 0,
            "payout_currency": base_fields["currency"],
            "notes": f"Источник: {base_fields['source']}, Баер: {base_fields['buyer']}",
            "action_type": "http",
            "offer_type": "external",
            "state": "active",
            "action_payload": link
        }

        headers = {
            "API-KEY": os.environ["KEITARO_API_KEY"],
            "Content-Type": "application/json"
        }

        keitaro_url = os.environ["KEITARO_API_URL"]
        response = requests.post(f"{keitaro_url}/admin_api/v1/offers", headers=headers, json=payload)
        created_offers.append({"name": offer_name, "status": response.status_code, "response": response.text})

    return {"created": created_offers}
