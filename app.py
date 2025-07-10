from fastapi import APIRouter, Request
from typing import List
import yfinance as yf
from collections import defaultdict
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/price")
def get_price(symbol: str):
    ticker = yf.Ticker(symbol)
    price = ticker.info.get("regularMarketPrice", 0)
    return { "symbol": symbol.upper(), "price": price }

@history_router.post("/portfolio-history")
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

        for date, row in history.iterrows():
            date_str = date.strftime("%Y-%m-%d")
            for lot in lots:
                if date_str >= lot["purchaseDate"]:
                    portfolio_value_by_day[date_str] += row["Close"] * lot["quantity"]
                    all_dates.add(date_str)

    sorted_dates = sorted(all_dates)
    output = {
        "id": "Portfolio",
        "data": [{"x": date, "y": round(portfolio_value_by_day[date], 2)} for date in sorted_dates]
    }

    return [output]
