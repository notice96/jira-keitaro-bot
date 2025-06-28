from fastapi import FastAPI, Request
import httpx
import re
from fastapi.responses import JSONResponse

app = FastAPI()

KEITARO_API_URL = "http://77.221.155.15/admin_api/v1/offers"
API_KEY = "0ed98ed7f659004f3f7e68e68984b2fa"

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    payload = await request.json()
    summary = payload.get("issue", {}).get("fields", {}).get("summary", "")
    description = payload.get("issue", {}).get("fields", {}).get("description", "")

    print("=== JIRA Summary ===", summary)
    print("=== JIRA Description ===", description)

    # Извлечение данных
    data = {
        "id": extract_value(summary, r"id_prod\{(.*?)\}"),
        "product": extract_value(description, r"Продукт:\s*(.*)"),
        "geo": extract_value(description, r"Гео:\s*(.*)"),
        "payout": extract_value(description, r"Ставка:\s*(.*)"),
        "currency": extract_value(description, r"Валюта:\s*(.*)"),
        "cap": extract_value(description, r"Капа:\s*(.*)"),
        "source": extract_value(description, r"Сорс:\s*(.*)"),
        "buyer": extract_value(description, r"Баер:\s*(.*)"),
        "pp": extract_value(description, r"ПП:\s*(.*)"),
        "links": extract_links(description)
    }

    print("=== Parsed Offer Data ===", data)

    results = []

    for label, url in data["links"]:
        offer_name = (
            f"id_prod{{{data['id']}}} - Продукт: {data['product']} Гео: {data['geo']} "
            f"Ставка: {data['payout']} Валюта: {data['currency']} Капа: {data['cap']} "
            f"Сорс: {data['source']} Баер: {data['buyer']} - {label}"
        )

        offer_payload = {
            "name": offer_name,
            "group": data["buyer"],
            "affiliate_network": data["pp"],
            "url": url,
            "redirect_type": "http",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    KEITARO_API_URL,
                    headers={"Api-Key": API_KEY},
                    json=offer_payload,
                    timeout=20
                )
                print(f"=== Keitaro Response [{url}] ===", response.status_code, response.text)
                results.append({
                    "url": url,
                    "status_code": response.status_code,
                    "response": response.text
                })
        except Exception as e:
            print(f"=== ERROR sending URL {url} ===", str(e))
            results.append({
                "url": url,
                "error": str(e)
            })

    return JSONResponse(content={"result": results})

def extract_value(text, pattern):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def extract_links(text):
    pattern = re.compile(r"([^
]+)
\[(https?://[^\s|]+)\|")
    return [(m[0].strip(), m[1].strip()) for m in pattern.findall(text)]