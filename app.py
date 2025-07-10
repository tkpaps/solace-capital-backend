from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf

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
