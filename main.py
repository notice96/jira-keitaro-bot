from fastapi import FastAPI, Request
import httpx
import re
import os

app = FastAPI()

API_KEY = os.getenv("KEITARO_API_KEY")
KEITARO_URL = os.getenv("KEITARO_API_URL") + "/offers"


def parse_offer(summary, description):
    offer_id = summary.strip()
    fields = {
        "id": offer_id,
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

    lines = description.splitlines()
    for line in lines:
        if "Продукт:" in line:
            fields["product"] = line.split(":", 1)[-1].strip()
        elif "Гео:" in line:
            fields["geo"] = line.split(":", 1)[-1].strip()
        elif "Ставка:" in line:
            fields["payout"] = line.split(":", 1)[-1].strip()
        elif "Валюта:" in line:
            fields["currency"] = line.split(":", 1)[-1].strip()
        elif "Капа:" in line:
            fields["cap"] = line.split(":", 1)[-1].strip()
        elif "Сорс:" in line:
            fields["source"] = line.split(":", 1)[-1].strip()
        elif "Баер:" in line:
            fields["buyer"] = line.split(":", 1)[-1].strip()
        elif "ПП:" in line:
            fields["pp"] = line.split(":", 1)[-1].strip()

    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("http://") or line.startswith("https://"):
            label = lines[i - 1].strip() if i > 0 else ""
            fields["links"].append((label, line))

    return fields


@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()
    summary = data.get("issue", {}).get("fields", {}).get("summary", "")
    description = data.get("issue", {}).get("fields", {}).get("description", "")

    desc_text = ""
    for block in description_blocks:
        for inner in block.get("content", []):
            desc_text += inner.get("text", "") + "\n"

    parsed = parse_offer(summary, desc_text)
    print("=== Parsed Offer Data ===", parsed)

    headers = {"Api-Key": API_KEY}
    for label, url in parsed["links"]:
        offer_name = (
            f'{parsed["id"]} - Продукт: {parsed["product"]} Гео: {parsed["geo"]} '
            f'Ставка: {parsed["payout"]} Валюта: {parsed["currency"]} Капа: {parsed["cap"]} '
            f'Сорс: {parsed["source"]} Баер: {parsed["buyer"]} - {label}'
        )
        offer_data = {
            "name": offer_name,
            "url": url,
            "group_id": 1,
            "campaign_uniqueness": "campaign"
        }
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(KEITARO_URL, headers=headers, json=offer_data)
                print(f"=== Keitaro Response [{url}] ===", res.status_code, res.text)
        except Exception as e:
            print("=== ERROR while sending to Keitaro ===", str(e))

    return {"message": "Received"}
