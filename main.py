
import re
import httpx
from fastapi import FastAPI, Request

app = FastAPI()

API_URL = "http://77.221.155.15/admin_api/v1/offers"
API_KEY = "0ed98ed7f659004f3f7e68e68984b2fa"

def parse_offer_data(summary: str, description: str):
    product = re.search(r"Продукт:\s*(.+)", description)
    geo = re.search(r"Гео:\s*(.+)", description)
    payout = re.search(r"Ставка:\s*(.+)", description)
    cap = re.search(r"Капа:\s*(.+)", description)
    source = re.search(r"Сорс:\s*(.+)", description)
    buyer = re.search(r"Баер:\s*(.+)", description)
    pp = re.search(r"ПП:\s*(.+)", description)

    # Поддержка Jira markdown ссылок: [текст|ссылка]
    markdown_links = re.findall(r"\[(.*?)\|(https?://[\w\.-/?=&%]+)\]", description)
    # Плюс — прямые обычные ссылки без markdown
    plain_links = re.findall(r"(https?://[\w\.-/?=&%]+)", description)

    # Преобразуем markdown ссылки в (название, ссылка)
    links = [(title.strip(), url.strip()) for title, url in markdown_links]

    # Если нет markdown, используем plain ссылки
    if not links and plain_links:
        links = [(f"Link {i+1}", url) for i, url in enumerate(plain_links)]

    return {
        "id": summary.strip(),
        "product": product.group(1).strip() if product else "",
        "geo": geo.group(1).strip() if geo else "",
        "payout": payout.group(1).strip() if payout else "",
        "cap": cap.group(1).strip() if cap else "",
        "source": source.group(1).strip() if source else "",
        "buyer": buyer.group(1).strip() if buyer else "",
        "pp": pp.group(1).strip() if pp else "",
        "links": links
    }

@app.post("/jira-to-keitaro")
async def jira_webhook(request: Request):
    payload = await request.json()
    summary = payload.get("issue", {}).get("fields", {}).get("summary", "")
    description = payload.get("issue", {}).get("fields", {}).get("description", "")

    print("=== JIRA Summary ===", summary)
    print("=== JIRA Description ===", description)

    parsed = parse_offer_data(summary, description)
    print("=== Parsed Offer Data ===", parsed)

    headers = {
        "Api-Key": API_KEY,
        "Content-Type": "application/json"
    }

    created = 0
    for link_title, link_url in parsed["links"]:
        offer_name = f"{parsed['id']} - {link_title}"
        notes = description

        data = {
            "name": offer_name,
            "url": link_url,
            "notes": notes,
            "group_name": parsed["buyer"],
            "affiliate_network_name": parsed["pp"]
        }

        try:
            response = httpx.post(API_URL, headers=headers, json=data, timeout=10)
            print(f"=== Keitaro Response [{link_title}] ===", response.status_code, response.text)
            if response.status_code == 200:
                created += 1
        except Exception as e:
            print("=== ERROR while sending to Keitaro ===", str(e))

    return {"status": "completed", "offers_created": created}
