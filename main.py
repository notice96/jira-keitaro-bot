from fastapi import FastAPI, Request
import httpx
import re

app = FastAPI()

API_KEY = "0ed98ed7f659004f3f7e68e68984b2fa"
KEITARO_URL = "http://77.221.155.15/admin_api/v1/offers"

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

    # Ссылки
    link_pattern = re.compile(r"^(\w[\w\s.]+)\n\n\[(https?://[^\s|]+)")
    name = ""
    for i, line in enumerate(lines):
        if re.match(r"^https?://", line.strip()):
            if i > 0:
                name = lines[i-1].strip()
            url = line.strip()
            fields["links"].append((name, url))

    return fields

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()
    summary = data.get("issue", {}).get("fields", {}).get("summary", "")
    description = data.get("issue", {}).get("fields", {}).get("description", {}).get("content", [])

    desc_text = ""
    for block in description:
        for inner in block.get("content", []):
            desc_text += inner.get("text", "") + "\n"

    parsed = parse_offer(summary, desc_text)
    print("=== Parsed Offer ===", parsed)

    headers = {"Api-Key": API_KEY}
    for label, url in parsed["links"]:
        offer_data = {
            "name": f'{parsed["id"]} - Продукт: {parsed["product"]} Гео: {parsed["geo"]} Ставка: {parsed["payout"]} Валюта: {parsed["currency"]} Капа: {parsed["cap"]} Сорс: {parsed["source"]} Баер: {parsed["buyer"]} - {label}',
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