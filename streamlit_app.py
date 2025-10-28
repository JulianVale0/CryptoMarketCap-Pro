# File: streamlit_app.py (FIXED & COOL GRAPHS)
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === PAGE CONFIG ===
st.set_page_config(page_title="Crypto Pro Dashboard", page_icon="Chart increasing", layout="wide")

# === DARK PRO THEME ===
st.markdown("""
<style>
    .main {background-color: #0e1117; color: #e0e00e;}
    .stMetric {background-color: #1a1f2e; padding: 12px; border-radius: 12px; border: 1px solid #2a2f45;}
    h1, h2, h3 {color: #00d4aa;}
    .stSelectbox > div > div {background-color: #1a1f2e; color: white; border: 1px solid #2a2f45;}
    .stDataFrame {background-color: #1a1f2e; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.title("Select Coin")
coin_options = {
    "Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana",
    "BNB": "binancecoin", "XRP": "ripple", "Cardano": "cardano",
    "Dogecoin": "dogecoin", "Avalanche": "avalanche-2"
}
coin_name = st.sidebar.selectbox("Coin", list(coin_options.keys()))
coin_id = coin_options[coin_name]
timeframe = st.sidebar.selectbox("Timeframe", ["1D", "7D", "30D", "90D", "1Y"])

# === API FETCH ===
@st.cache_data(ttl=10)
def fetch(endpoint):
    url = f"https://api.coingecko.com/api/v3{endpoint}"
    try:
        return requests.get(url, timeout=10).json()
    except:
        return None

# === TOP 10 TABLE WITH SPARKLINE (FIXED) ===
st.markdown("## **Top 10 Coins**")
top = fetch("/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=true")
if top:
    df = pd.DataFrame(top)
    df = df[["name", "symbol", "current_price", "price_change_percentage_24h", "market_cap", "sparkline_in_7d"]]
    df.columns = ["Name", "Symbol", "Price", "24h %", "Market Cap", "7d Trend"]
    df["Price"] = df["Price"].apply(lambda x: f"${x:,.2f}")
    df["24h %"] = df["24h %"].apply(lambda x: f"<span style='color:{'lime' if x>=0 else 'red'}; font-weight:bold'>{x:+.2f}%</span>" if pd.notnull(x) else "N/A")
    df["Market Cap"] = df["Market Cap"].apply(lambda x: f"${x/1e9:.2f}B")
    df["Symbol"] = df["Symbol"].str.upper()

    # === SAFE SPARKLINE FUNCTION ===
    def safe_sparkline(spark_data):
        if not spark_data or 'price' not in spark_data or len(spark_data['price']) == 0:
            return "───"
        prices = spark_data['price'][-20:]  # Last 20 points
        first = prices[0]
        return ''.join(['█' if p > first else '░' for p in prices])[::-1]

    df["7d Trend"] = df["7d Trend"].apply(safe_sparkline)
    
    # === RENDER HTML TABLE ===
    html_table = df.to_html(escape=False, index=False)
    st.markdown(html_table, unsafe_allow_html=True)

# === PRO CANDLESTICK + VOLUME + RSI ===
st.markdown(f"## **{coin_name} Pro Chart**")
days = {"1D":1, "7D":7, "30D":30, "90D":90, "1Y":365}[timeframe]
ohlc = fetch(f"/coins/{coin_id}/ohlc?vs_currency=usd&days={days}")
market = fetch(f"/coins/{coin_id}/market_chart?vs_currency=usd&days={days}")

if ohlc and market:
    # Candlestick
    df_candles = pd.DataFrame(ohlc, columns=["time", "open", "high", "low", "close"])
    df_candles["time"] = pd.to_datetime(df_candles["time"], unit='ms')
    
    # Volume
    df_vol = pd.DataFrame(market['total_volumes'], columns=['time', 'volume'])
    df_vol['time'] = pd.to_datetime(df_vol['time'], unit='ms')
    
    # RSI
    prices = pd.DataFrame(market['prices'], columns=['time', 'price'])
    prices['time'] = pd.to_datetime(prices['time'], unit='ms')
    delta = prices['price'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    prices['rsi'] = rsi

    # Subplots
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(f"{coin_name} Price", "Volume", "RSI (14)"),
        row_heights=[0.6, 0.2, 0.2]
    )

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df_candles['time'], open=df_candles['open'], high=df_candles['high'],
        low=df_candles['low'], close=df_candles['close'],
        name="Price", increasing_line_color='#00ff88', decreasing_line_color='#ff4455'
    ), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df_vol['time'], y=df_vol['volume'], name="Volume", marker_color='#445577'), row=2, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=prices['time'], y=prices['rsi'], name="RSI", line=dict(color='#ffaa00')), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(
        height=800, template="plotly_dark", xaxis_rangeslider_visible=False,
        title_text=f"{coin_name} - {timeframe} (Live • Auto-Update)"
    )
    st.plotly_chart(fig, use_container_width=True)

# === PORTFOLIO ===
st.markdown("## **Portfolio Tracker**")
with st.expander("Add Holdings"):
    portfolio = {}
    for name, cid in coin_options.items():
        amt = st.number_input(name, min_value=0.0, value=0.0, step=0.001, key=cid)
        if amt > 0:
            price = fetch(f"/simple/price?ids={cid}&vs_currencies=usd")[cid]["usd"]
            portfolio[name] = amt * price
    if portfolio:
        total = sum(portfolio.values())
        st.metric("**Total Value**", f"${total:,.2f}")
        df_p = pd.DataFrame(list(portfolio.items()), columns=["Coin", "Value"])
        df_p["Value"] = df_p["Value"].apply(lambda x: f"${x:,.2f}")
        st.dataframe(df_p, hide_index=True)

st.caption("**Live • Auto-updates every 10s** • Data: CoinGecko • Built with Streamlit")
