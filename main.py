from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class JiraPayload(BaseModel):
    issue: dict

@app.post("/jira-to-keitaro")
async def webhook(payload: JiraPayload):
    print(payload)
    return {"message": "Received"}
