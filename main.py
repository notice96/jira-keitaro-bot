
import os
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Server is running."}

@app.post("/jira-to-keitaro")
async def jira_to_keitaro(request: Request):
    data = await request.json()
    print("Received JIRA Webhook:", data)
    return {"status": "received"}
