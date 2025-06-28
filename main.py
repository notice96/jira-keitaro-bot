
import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()
    print("\n=== Raw Webhook Data ===")
    print(data)

    try:
        issue = data.get("issue", {})
        fields = issue.get("fields", {})
        description_raw = fields.get("description", {})

        # Проверяем, является ли description строкой
        if isinstance(description_raw, str):
            description_text = description_raw
        else:
            description_text = ""
            for block in description_raw.get("content", []):
                for inner in block.get("content", []):
                    if inner.get("type") == "text":
                        description_text += inner.get("text", "") + "\n"

        print("\n=== Parsed Description Text ===\n", description_text)

        lines = description_text.strip().splitlines()
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

        current_link_title = ""
        for line in lines:
            line = line.strip()
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
            elif line.startswith("http"):
                if current_link_title:
                    offer_data["links"].append((current_link_title, line))
                    current_link_title = ""
            elif line:
                current_link_title = line

        print("\n=== Parsed Offer Data ===", offer_data)

        keitaro_api_url = os.getenv("KEITARO_API_URL")
        keitaro_api_key = os.getenv("KEITARO_API_KEY")

        headers = {
            "Api-Key": keitaro_api_key,
            "Content-Type": "application/json"
        }

        for title, url in offer_data["links"]:
            payload = {
                "name": f"{offer_data['id']} - Продукт: {offer_data['product']} Гео: {offer_data['geo']} Ставка: {offer_data['payout']} Валюта: {offer_data['currency']} Капа: {offer_data['cap']} Сорс: {offer_data['source']} Баер: {offer_data['buyer']} - {title}",
                "url": url,
                "group_id": None,
                "notes": f"PP: {offer_data['pp']}"
            }
            response = requests.post(f"{keitaro_api_url}/offers", json=payload, headers=headers)
            print("\n=== Keitaro Response ===")
            print("Status Code:", response.status_code)
            print("Response Body:", response.text)

        return {"status": "success"}
    except Exception as e:
        print("Exception occurred:", str(e))
        return {"status": "error", "details": str(e)}
