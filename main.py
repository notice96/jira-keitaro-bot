
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post("/jira-to-keitaro")
async def handle_webhook(request: Request):
    data = await request.json()
    print("Webhook received:", data)
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
