from fastapi import FastAPI

app = FastAPI(title="Tunisia National Parks API")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
