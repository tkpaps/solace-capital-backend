from fastapi import FastAPI, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import yfinance as yf
from collections import defaultdict
from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@router.get("/price")
def get_price(symbol: str):
    ticker = yf.Ticker(symbol)
    price = ticker.info.get("regularMarketPrice", 0)
    return { "symbol": symbol.upper(), "price": price }


@router.post("/portfolio-history")
async def portfolio_history(request: Request):
    body = await request.json()

    grouped = defaultdict(list)
    for lot in body:
        grouped[lot["symbol"]].append({
            "quantity": float(lot["quantity"]),
            "purchaseDate": lot["purchaseDate"]
        })

    portfolio_value_by_day = defaultdict(float)
    all_dates = set()

    for symbol, lots in grouped.items():
        min_date = min(lot["purchaseDate"] for lot in lots)
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=min_date)

        # Build a dict of date -> close price and carry forward missing days
        price_by_date = {}
        last_price = None

        for date in hist.index:
            date_str = date.strftime('%Y-%m-%d')
            last_price = hist.loc[date]["Close"]
            price_by_date[date_str] = last_price

        # Fill missing days between min_date and today
        current = datetime.strptime(min_date, "%Y-%m-%d")
        today = datetime.today()

        while current <= today:
            date_str = current.strftime("%Y-%m-%d")
            if date_str not in price_by_date and last_price is not None:
                price_by_date[date_str] = last_price
            elif date_str in price_by_date:
                last_price = price_by_date[date_str]
            current += timedelta(days=1)

        # Apply quantities per lot
        for lot in lots:
            for date_str, price in price_by_date.items():
                if date_str >= lot["purchaseDate"]:
                    portfolio_value_by_day[date_str] += price * lot["quantity"]
                    all_dates.add(date_str)

    sorted_dates = sorted(all_dates)
    output = {
        "id": "Portfolio",
        "data": [{"x": date, "y": round(portfolio_value_by_day[date], 2)} for date in sorted_dates]
    }

    return [output]

app.include_router(router)
