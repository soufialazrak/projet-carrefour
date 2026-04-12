from fastapi import FastAPI
from app.routers import gold

app = FastAPI(
    title="DataMarket Carrefour API",
    description="API REST pour exposer les données PostgreSQL du projet Carrefour",
    version="1.0.0"
)

# On garde uniquement les endpoints utiles à l'app Streamlit
app.include_router(gold.router, tags=["Gold"])


@app.get("/")
def read_root():
    return {"message": "API DataMarket Carrefour OK"}