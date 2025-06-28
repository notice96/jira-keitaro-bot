from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Приложение успешно запущено на Railway!"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
