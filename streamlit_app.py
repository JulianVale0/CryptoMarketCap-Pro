# File name: streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# === PAGE CONFIG ===
st.set_page_config(
    page_title="Crypto Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === DARK THEME CSS ===
st.markdown("""
<style>
    .main {background-color: #0e1117; color: white;}
    .stMetric {color: white; background-color: #1f2633; padding: 10px; border-radius: 10px;}
    .css-1d391kg {color: white;}
    h1, h2, h3 {color: #ffffff;}
    .stSelectbox > div > div {background-color: #1f2633; color: white;}
    .stDataFrame {background-color: #1f2633;}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
st.sidebar.title("🔍 Select Coin")
coin_options = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "BNB": "binancecoin",
    "XRP": "ripple",
    "Cardano": "cardano",
    "Dogecoin": "dogecoin",
    "Avalanche": "avalanche-2",
    "Polkadot": "polkadot",
    "Chainlink": "chainlink"
}
coin_name = st.sidebar.selectbox("Coin", list(coin_options.keys()))
coin_id = coin_options[coin_name]

timeframe = st.sidebar.selectbox("Timeframe", ["1D", "7D", "30D", "90D", "1Y", "MAX"])

# === API CALLS ===
@st.cache_data(ttl=10)
def fetch_data(endpoint):
    url = f"https://api.coingecko.com/api/v3{endpoint}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# === TOP 10 COINS ===
st.markdown("## **Top 10 Cryptocurrencies**")
top_coins = fetch_data("/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1")
if top_coins:
    df_top = pd.DataFrame(top_coins)[["name", "symbol", "current_price", "price_change_percentage_24h", "market_cap"]]
    df_top.columns = ["Name", "Symbol", "Price", "24h %", "Market Cap"]
    df_top["Price"] = df_top["Price"].apply(lambda x: f"${x:,.2f}")
    df_top["24h %"] = df_top["24h %"].apply(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A")
    df_top["Market Cap"] = df_top["Market Cap"].apply(lambda x: f"${x/1e9:.2f}B")
    df_top["Symbol"] = df_top["Symbol"].str.upper()
    st.dataframe(df_top, use_container_width=True, hide_index=True)

# === SELECTED COIN CHART ===
st.markdown(f"## **{coin_name} Price Chart**")
days_map = {"1D": 1, "7D": 7, "30D": 30, "90D": 90, "1Y": 365, "MAX": 2000}
days = days_map[timeframe]

ohlc_data = fetch_data(f"/coins/{coin_id}/ohlc?vs_currency=usd&days={days}")
if ohlc_data:
    df_ohlc = pd.DataFrame(ohlc_data, columns=["timestamp", "open", "high", "low", "close"])
    df_ohlc["timestamp"] = pd.to_datetime(df_ohlc["timestamp"], unit='ms')

    fig = go.Figure(data=[go.Candlestick(
        x=df_ohlc['timestamp'],
        open=df_ohlc['open'],
        high=df_ohlc['high'],
        low=df_ohlc['low'],
        close=df_ohlc['close'],
        increasing_line_color='#00ff88', decreasing_line_color='#ff4455'
    )])
    fig.update_layout(
        title=f"{coin_name} ({timeframe})",
        xaxis_title="Time",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        height=600,
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

# === COIN METRICS ===
coin_info = fetch_data(f"/coins/{coin_id}")
if coin_info:
    market = coin_info.get("market_data", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Market Cap", f"${market.get('market_cap', {}).get('usd', 0):,.0f}")
    col2.metric("24h Volume", f"${market.get('total_volume', {}).get('usd', 0):,.0f}")
    col3.metric("Circulating Supply", f"{market.get('circulating_supply', 0):,.0f}")
    col4.metric("ATH", f"${market.get('ath', {}).get('usd', 0):,.0f}")

# === PORTFOLIO TRACKER ===
st.markdown("## **Portfolio Tracker**")
with st.expander("Add Your Holdings"):
    portfolio = {}
    for name, cid in coin_options.items():
        amt = st.number_input(f"{name} ({cid.upper()})", min_value=0.0, value=0.0, step=0.001, key=cid)
        if amt > 0:
            price = fetch_data(f"/simple/price?ids={cid}&vs_currencies=usd")[cid]["usd"]
            portfolio[name] = {"amount": amt, "value": amt * price}
    
    if portfolio:
        total = sum(item["value"] for item in portfolio.values())
        st.metric("**Total Portfolio Value**", f"${total:,.2f}")
        
        df_port = pd.DataFrame([
            {"Coin": k, "Amount": v["amount"], "Value": f"${v['value']:,.2f}"}
            for k,v in portfolio.items()
        ])
        st.dataframe(df_port, use_container_width=True, hide_index=True)

# === FOOTER ===
st.markdown("---")
st.caption("**Data Source: CoinGecko API** • **Auto-refreshes every 10 seconds** • Built with Streamlit")
