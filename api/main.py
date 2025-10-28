# api/crypto.py
import requests
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="NEXA Crypto API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Map CoinGecko ID → Binance symbol
SYMBOL_MAP = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "solana": "SOL",
    "ripple": "XRP",
    "cardano": "ADA",
    "dogecoin": "DOGE",
    "tron": "TRX",
    "polkadot": "DOT",
    "polygon": "MATIC",
    "litecoin": "LTC",
    "avalanche-2": "AVAX",
    "shiba-inu": "SHIB",
    "chainlink": "LINK",
    "uniswap": "UNI"
}

def get_binance_klines(symbol: str, interval: str, limit: int = 1000):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        data = requests.get(url, params=params, timeout=10).json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df = df[["open_time", "open", "high", "low", "close"]]
        df.columns = ["ts", "open", "high", "low", "close"]
        df["ts"] = pd.to_datetime(df["ts"], unit='ms')
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
        return df.to_dict(orient="records")
    except:
        return []

@app.get("/ohlc/{coin_id}")
def ohlc(coin_id: str, days: int = 365):
    symbol = SYMBOL_MAP.get(coin_id, coin_id.upper()) + "USDT"
    interval = "1d"
    limit = 1000

    # For 5Y, fetch in chunks
    if days > 1000:
        all_data = []
        end_time = int(pd.Timestamp.now().timestamp() * 1000)
        while len(all_data) < days:
            start_time = end_time - (limit * 24 * 60 * 60 * 1000)  # 1000 days back
            url = "https://api.binance.com/api/v3/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": start_time,
                "endTime": end_time,
                "limit": limit
            }
            try:
                data = requests.get(url, params=params, timeout=10).json()
                if not data:
                    break
                df = pd.DataFrame(data, columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"
                ])
                df = df[["open_time", "open", "high", "low", "close"]]
                df.columns = ["ts", "open", "high", "low", "close"]
                df["ts"] = pd.to_datetime(df["ts"], unit='ms')
                df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].astype(float)
                all_data = df.to_dict(orient="records") + all_data
                end_time = int(df["ts"].min().timestamp() * 1000) - 1
                if len(data) < limit:
                    break
            except:
                break
        return {"data": all_data[-days:]}  # Return last `days` points
    else:
        return {"data": get_binance_klines(symbol, interval, limit=days)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
