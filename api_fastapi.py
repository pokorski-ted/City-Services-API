from fastapi import FastAPI

app = FastAPI(title="City Services API")

@app.get("/health")
def health():
    return {"status": "ok"}
