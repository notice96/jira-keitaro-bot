
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>Server is up and running.</h1>"

@app.post("/generate_offer")
async def generate_offer(request: Request):
    data = await request.json()
    input_text = data.get("text", "")
    if not input_text:
        return {"error": "No input text provided."}
    
    # Имитация генерации оффера
    offer = f"🎯 {input_text[:80]}... — Специальное предложение уже ждет вас!"
    return {"offer": offer}
