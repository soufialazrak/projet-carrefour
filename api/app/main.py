from fastapi import FastAPI
from app.routers import gold, streaming

app = FastAPI(
    title="DataMarket Carrefour API",
    description="API REST pour exposer les données PostgreSQL du projet Carrefour",
    version="1.0.0"
)

# Endpoints historiques DataMarket
app.include_router(gold.router, tags=["Gold"])

# Endpoints Kafka streaming E7
app.include_router(streaming.router)


@app.get("/")
def read_root():
    return {"message": "API DataMarket Carrefour OK"}