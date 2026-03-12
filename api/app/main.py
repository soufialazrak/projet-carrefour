from fastapi import FastAPI
from app.routers import (
    clients,
    transactions,
    foyers,
    transaction_items,
    loyalty_cards,
    analytics,
    gold
)

app = FastAPI(
    title="DataMarket Carrefour API",
    description="API REST pour exposer les données PostgreSQL du projet Carrefour",
    version="1.0.0"
)

app.include_router(clients.router, tags=["Clients"])
app.include_router(transactions.router, tags=["Transactions"])
app.include_router(foyers.router, tags=["Foyers"])
app.include_router(transaction_items.router, tags=["Transaction Items"])
app.include_router(loyalty_cards.router, tags=["Loyalty Cards"])
app.include_router(analytics.router, tags=["Analytics"])
app.include_router(gold.router, tags=["Gold"])


@app.get("/")
def read_root():
    return {"message": "API DataMarket Carrefour OK"}