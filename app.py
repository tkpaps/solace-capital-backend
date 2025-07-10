from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import yfinance as yf
from collections import defaultdict
from datetime import datetime

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
router = APIRouter()

@router.get("/price")
def get_price(symbol: str):
    ticker = yf.Ticker(symbol)
    price = ticker.info.get("regularMarketPrice", 0)
    return {"symbol": symbol.upper(), "price": price}


@router.post("/portfolio-history")
async def portfolio_history(request: Request):
    body = await request.json()

    grouped = defaultdict(list)
    for lot in body:
        grouped[lot["symbol"]].append({
            "quantity": float(lot["quantity"]),
            "purchaseDate": lot["purchaseDate"]
        })

    all_dates = set()
    portfolio_value_by_day = defaultdict(float)

    for symbol, lots in grouped.items():
        ticker = yf.Ticker(symbol)
        min_date = min(lot["purchaseDate"] for lot in lots)
        history = ticker.history(start=min_date)

        # Precompute cumulative quantity held by day
        sorted_lots = sorted(lots, key=lambda x: x["purchaseDate"])
        cumulative_quantity_by_date = {}
        running_quantity = 0

        for date in history.index:
            date_str = date.strftime("%Y-%m-%d")
            for lot in sorted_lots:
                if lot["purchaseDate"] == date_str:
                    running_quantity += lot["quantity"]
            cumulative_quantity_by_date[date_str] = running_quantity

        # Calculate portfolio value per day
        for date, row in history.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            price = row.get("Close")
            quantity = cumulative_quantity_by_date.get(date_str, 0)
            if price and quantity:
                portfolio_value_by_day[date_str] += price * quantity
                all_dates.add(date_str)

    sorted_dates = sorted(all_dates)
    output = {
        "id": "Portfolio",
        "data": [{"x": date, "y": round(portfolio_value_by_day[date], 2)} for date in sorted_dates]
    }

    return [output]

# Include routes
app.include_router(router)
