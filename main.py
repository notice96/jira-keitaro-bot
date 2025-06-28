import re
import requests
from fastapi import FastAPI, Request

app = FastAPI()

KEITARO_API_URL = "http://77.221.155.15/admin_api/v1/offers"
API_KEY = "0ed98ed7f659004f3f7e68e68984b2fa"


@app.post("/jira-to-keitaro")
async def webhook(request: Request):
    data = await request.json()

    summary = data.get("issue", {}).get("fields", {}).get("summary", "")
    description_blocks = data.get("issue", {}).get("fields", {}).get("description", "")

    if isinstance(description_blocks, dict):
        description_blocks = description_blocks.get("content", [])
    else:
        description_blocks = []

    desc_text = ""
    for block in description_blocks:
        if isinstance(block, dict):
            for inner in block.get("content", []):
                if isinstance(inner, dict):
                    desc_text += inner.get("text", "") + "\n"

    print("=== JIRA Summary ===", summary)
    print("=== JIRA Description ===", desc_text)

    parsed = parse_description(desc_text)
    parsed["id"] = summary.strip()

    print("=== Parsed Offer Data ===", parsed)

    for title, link in parsed.get("links", []):
        payload = {
            "name": f"{parsed['id']} - Продукт: {parsed['product']} Гео: {parsed['geo']} Ставка: {parsed['payout']} Валюта: {parsed.get('currency', '')} Капа: {parsed['cap']} Сорс: {parsed['source']} Баер: {parsed['buyer']} - {title}",
            "url": link,
            "group_id": 1,
            "status": "active"
        }

        headers = {
            "Api-Key": API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(KEITARO_API_URL, json=payload, headers=headers)
        print(f"=== Keitaro Response [{link}] ===", response.status_code, response.text)

    return {"ok": True}


def parse_description(text):
    offer = {
        "product": extract(r"Продукт:\s*(.+)", text),
        "geo": extract(r"Гео:\s*(.+)", text),
        "payout": extract(r"Ставка:\s*(.+)", text),
        "currency": extract(r"Валюта:\s*(.+)", text),
        "cap": extract(r"Капа:\s*(.+)", text),
        "source": extract(r"Сорс:\s*(.+)", text),
        "buyer": extract(r"Баер:\s*(.+)", text),
        "pp": extract(r"ПП:\s*(.+)", text),
        "links": extract_links(text)
    }
    return offer


def extract(pattern, text):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def extract_links(text):
    lines = text.splitlines()
    links = []
    current_title = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not line.startswith("http") and not line.startswith("[http"):
            current_title = line
        elif line.startswith("[http") and "|" in line:
            match = re.search(r"\[(http[^|]+)\|", line)
            if match:
                url = match.group(1)
                links.append((current_title, url))
        elif line.startswith("http"):
            links.append((current_title, line))
    return links
