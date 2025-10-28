# File: streamlit_app.py (FIXED + SMOOTH UI)
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# === PAGE CONFIG ===
st.set_page_config(page_title="Crypto Pro", page_icon="Chart increasing", layout="wide", initial_sidebar_state="collapsed")

# === SMOOTH MODERN CSS ===
st.markdown("""
<style>
    .main {background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%); font-family: 'Inter', sans-serif; color: #e0e0e0;}
    .glass-card {
        background: rgba(30, 35, 60, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    .glass-card:hover {transform: translateY(-4px); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);}
    h1, h2, h3 {color: #00d4aa; text-shadow: 0 0 10px rgba(0, 212, 170, 0.3);}
    .stMetric {background: rgba(0, 212, 170, 0.1); border: 1px solid rgba(0, 212, 170, 0.3); border-radius: 12px; padding: 12px;}
    .stMetric > div:first-child {color: #00d4aa; font-weight: 600;}
    .css-1d391kg {background: rgba(20, 25, 45, 0.9); backdrop-filter: blur(10px);}
    .stSelectbox > div > div {background: rgba(40, 45, 70, 0.8); border: 1px solid rgba(0, 212, 170, 0.3); border-radius: 12px;}
    .stButton > button {
        background: linear-gradient(45deg, #00d4aa, #00b894);
        color: white; border: none; border-radius: 12px; padding: 10px 20px;
        font-weight: 600; transition: all 0.3s ease;
    }
    .stButton > button:hover {transform: scale(1.05); box-shadow: 0 0 20px rgba(0, 212, 170, 0.5);}
    .stDataFrame {border-radius: 12px; overflow: hidden;}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR ===
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #00d4aa;'>Crypto Pro</h2>", unsafe_allow_html=True)
    coin_options = {
        "Bitcoin": "bitcoin", "Ethereum": "ethereum", "Solana": "solana",
        "BNB": "binancecoin", "XRP": "ripple", "Cardano": "cardano",
        "Dogecoin": "dogecoin", "Avalanche": "avalanche-2"
    }
    coin_name = st.selectbox("Select Coin", list(coin_options.keys()))
    coin_id = coin_options[coin_name]
    timeframe = st.selectbox("Timeframe", ["1D", "7D", "30D", "90D", "1Y"])

# === API FETCH ===
@st.cache_data(ttl=10)
def fetch(endpoint):
    try:
        return requests.get(f"https://api.coingecko.com/api/v3{endpoint}", timeout=10).json()
    except:
        return None

# === TOP 10 (GLASS CARD) ===
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("## Top 10 Coins")
top = fetch("/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=true")
if top:
    df = pd.DataFrame(top)[["name", "symbol", "current_price", "price_change_percentage_24h", "market_cap", "sparkline_in_7d"]]
    df.columns = ["Name", "Symbol", "Price", "24h %", "Market Cap", "Trend"]
    df["Price"] = df["Price"].apply(lambda x: f"${x:,.2f}")
    df["24h %"] = df["24h %"].apply(lambda x: f"<span style='color:{'lime' if x>=0 else '#ff6b6b'}; font-weight:bold'>{x:+.2f}%</span>" if pd.notnull(x) else "N/A")
    df["Market Cap"] = df["Market Cap"].apply(lambda x: f"${x/1e9:.2f}B")
    df["Symbol"] = df["Symbol"].str.upper()

    def safe_sparkline(spark):
        if not spark or 'price' not in spark or len(spark['price']) == 0: return "───"
        p = spark['price'][-20:]
        return ''.join(['█' if v > p[0] else '░' for v in p])[::-1]
    df["Trend"] = df["Trend"].apply(safe_sparkline)

    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# === PRO CHART (GLASS CARD) ===
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown(f"## {coin_name} Pro Chart")
days = {"1D":1, "7D":7, "30D":30, "90D":90, "1Y":365}[timeframe]
ohlc = fetch(f"/coins/{coin_id}/ohlc?vs_currency=usd&days={days}")
market = fetch(f"/coins/{coin_id}/market_chart?vs_currency=usd&days={days}")

if ohlc and market:
    # Candlestick
    df_c = pd.DataFrame(ohlc, columns=["time", "open", "high", "low", "close"])
    df_c["time"] = pd.to_datetime(df_c["time"], unit='ms')

    # === SAFE VOLUME HANDLING ===
    if 'total_volumes' in market and market['total_volumes']:
        df_v = pd.DataFrame(market['total_volumes'], columns=['time', 'volume'])
        df_v['time'] = pd.to_datetime(df_v['time'], unit='ms')
    else:
        df_v = pd.DataFrame({'time': df_c['time'], 'volume': [0]*len(df_c)})

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
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.6, 0.2, 0.2])
    fig.add_trace(go.Candlestick(x=df_c['time'], open=df_c['open'], high=df_c['high'],
                                 low=df_c['low'], close=df_c['close'],
                                 name="Price", increasing_line_color='#00ff88', decreasing_line_color='#ff6b6b'), row=1, col=1)
    fig.add_trace(go.Bar(x=df_v['time'], y=df_v['volume'], name="Volume", marker_color='rgba(68, 87, 119, 0.6)'), row=2, col=1)
    fig.add_trace(go.Scatter(x=prices['time'], y=prices['rsi'], name="RSI", line=dict(color='#ffaa00', width=2)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#ff6b6b", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#00ff88", row=3, col=1)

    fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False,
                      margin=dict(l=40, r=40, t=60, b=40), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# === PORTFOLIO (GLASS CARD) ===
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("## Portfolio Tracker")
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
st.markdown("</div>", unsafe_allow_html=True)

# === FOOTER ===
st.markdown("<p style='text-align: center; color: #888; margin-top: 40px;'>Live • Auto-updates • Built with ❤️</p>", unsafe_allow_html=True)
