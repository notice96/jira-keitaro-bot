from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "FastAPI is working"}

@app.post("/jira-to-keitaro")
def test():
    return {"status": "received"}
