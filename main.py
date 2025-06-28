from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from Railway"}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    data = await request.json()
    print("Получен запрос от JIRA:", data)
    # Здесь добавь отправку оффера в Keitaro при необходимости
    return {"status": "ok"}
