from fastapi import FastAPI, Request
import os
import requests
import re

app = FastAPI()

def extract_links(description: str):
    # Сначала парсим markdown-ссылки [url|url]
    matches = re.findall(r'\[(https?://[^|\]]+)\|https?://[^\]]+\]', description)
    if not matches:
        # Затем парсим обычные ссылки
        matches = re.findall(r'https?://[^\s\]]+', description)
    return matches

def parse_description(text: str):
    data = {}
    lines = text.splitlines()
    for line in lines:
        if "id_prod" in line:
            data["id"] = line.strip()
        elif line.lower().startswith("продукт:"):
            data["product"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("гео:"):
            data["geo"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("ставка:"):
            data["payout"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("валюта:"):
            data["currency"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("капа:"):
            data["cap"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("сорс:"):
            data["source"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("баер:"):
            data["buyer"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("пп:"):
            data["pp"] = line.split(":", 1)[1].strip()

    data["links"] = extract_links(text)
    print("\n=== Parsed Offer Data ===", data)
    return data

@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    body = await request.json()
    print("\n=== Raw Webhook Data ===\n", body)
    try:
        description = body["issue"]["fields"]["description"]
        print("\n=== Parsed Description Text ===\n", description)
        offer_data = parse_description(description)
        # можно добавить push в keitaro здесь
    except Exception as e:
        print(f"Error: {e}")
    return {"ok": True}