import os
import re
import logging
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

KEITARO_API_URL = os.getenv("KEITARO_API_URL")
KEITARO_API_KEY = os.getenv("KEITARO_API_KEY")

def extract_links_and_labels(description_text: str):
    lines = description_text.splitlines()
    links = []
    current_label = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("http"):
            label = current_label if current_label else "No Label"
            links.append((label, line))
        else:
            current_label = line
    return links

def parse_offer(description: str):
    offer = {}
    offer["id"] = re.search(r"id_prod{(.*?)}", description).group(0)
    fields = ["Продукт", "Гео", "Ставка", "Валюта", "Капа", "Сорс", "Баер", "ПП"]
    for field in fields:
        match = re.search(rf"{field}:\s*(.*)", description)
        if match:
            offer[field.lower()] = match.group(1).strip()
    offer["links"] = extract_links_and_labels(description)
    return offer

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    payload = await request.json()
    try:
        description = payload.get("issue", {}).get("fields", {}).get("description", {}).get("content", [])
        full_text = ""

        for block in description:
            for content in block.get("content", []):
                if "text" in content:
                    full_text += content["text"] + "\n"
                elif content.get("type") == "inlineCard":
                    url = content.get("attrs", {}).get("url")
                    if url:
                        full_text += url + "\n"

        print("\n=== Parsed Description Text ===\n", full_text)
        offer = parse_offer(full_text)
        print("\n=== Parsed Offer Data ===", offer)

        headers = {"Api-Key": KEITARO_API_KEY, "Content-Type": "application/json"}
        for label, link in offer["links"]:
            data = {
                "name": f"{offer['id']} - {offer.get('продукт')} Гео: {offer.get('гео')} Ставка: {offer.get('ставка')} Валюта: {offer.get('валюта')} Капа: {offer.get('капа')} Сорс: {offer.get('сорс')} Баер: {offer.get('баер')} - {label}",
                "url": link,
                "group_id": 1,
                "type": "redirect",
                "status": "active"
            }
            async with httpx.AsyncClient() as client:
                r = await client.post(f"{KEITARO_API_URL}/offers", headers=headers, json=data)
                print("Keitaro response:", r.status_code, r.text)

        return {"status": "ok"}
    except Exception as e:
        logging.exception("Error processing webhook")
        return {"error": str(e)}
