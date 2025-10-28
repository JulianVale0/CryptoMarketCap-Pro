import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Coin Detail", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .main {background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); font-family: 'Inter', sans-serif; color: #e0e0e0;}
    .glass-card {
        background: rgba(30, 35, 60, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        border: 1px solid rgba(0, 212, 170, 0.3);
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.4s;
    }
    .glass-card:hover {transform: translateY(-8px); box-shadow: 0 20px 50px rgba(0, 212, 170, 0.2);}
    .price-up {color: #00ff88; font-weight: 700; text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);}
    .price-down {color: #ff6b6b; font-weight: 700; text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);}
    .back-btn {
        background: rgba(0, 212, 170, 0.2);
        color: #00d4aa;
        padding: 8px 16px;
        border-radius: 12px;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        transition: 0.3s;
    }
    .back-btn:hover {background: rgba(0, 212, 170, 0.4); transform: translateY(-2px);}
    .metric-glass {
        background: rgba(0, 212, 170, 0.1);
        padding: 12px;
        border-radius: 16px;
        border: 1px solid rgba(0, 212, 170, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# Back button + coin selection
if st.button("← Back to Rankings"):
    if "selected_coin" in st.session_state:
        del st.session_state.selected_coin
    st.switch_page("streamlit_app.py")

# Get coin from session state
if "selected_coin" not in st.session_state:
    st.error("No coin selected.")
    st.stop()

coin_id = st.session_state.selected_coin

# === MAP SYMBOL TO COINGECKO ID ===
symbol_to_id = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "TRX": "tron",
    "DOT": "polkadot",
    "MATIC": "polygon",
    "LTC": "litecoin",
    "AVAX": "avalanche-2",
    "SHIB": "shiba-inu",
    "LINK": "chainlink",
    "UNI": "uniswap"
}
coin_id = symbol_to_id.get(coin_id.upper(), coin_id.lower())

@st.cache_data(ttl=10)
def get_detail(cid):
    url = f"https://api.coingecko.com/api/v3/coins/{cid}"
    headers = {"User-Agent": "CryptoMarketCap-Pro/1.0"}
    try:
        return requests.get(url, params={"localization":False, "market_data":True, "sparkline":True}, headers=headers, timeout=15).json()
    except:
        return None

@st.cache_data(ttl=10)
def get_ohlc(cid):
    url = f"https://api.coingecko.com/api/v3/coins/{cid}/ohlc"
    headers = {"User-Agent": "CryptoMarketCap-Pro/1.0"}
    try:
        d = requests.get(url, params={"vs_currency":"usd","days":7}, headers=headers, timeout=15).json()
        df = pd.DataFrame(d, columns=["ts","open","high","low","close"])
        df["ts"] = pd.to_datetime(df["ts"], unit='ms')
        return df  # Full 4h data
    except:
        return pd.DataFrame()

# === FETCH OHLC DATA ===
ohlc = get_ohlc(coin_id)

with st.spinner("Loading coin data..."):
    detail = get_detail(coin_id)

if not detail:
    st.error("Failed to load coin. Retrying...")
    st.stop()

name = detail.get("name", "N/A")
symbol = detail.get("symbol", "").upper()
price = detail.get("market_data", {}).get("current_price", {}).get("usd", 0)
change = detail.get("market_data", {}).get("price_change_percentage_24h", 0)
cap = detail.get("market_data", {}).get("market_cap", {}).get("usd", 0)
vol = detail.get("market_data", {}).get("total_volume", {}).get("usd", 0)
ath = detail.get("market_data", {}).get("ath", {}).get("usd", 0)
atl = detail.get("market_data", {}).get("atl", {}).get("usd", 0)
img = detail.get("image", {}).get("large", "")
spark = detail.get("market_data", {}).get("sparkline_in_7d", {}).get("price", [])

# === HEADER — CLEAN & PREMIUM ===
st.markdown("<div class='glass-card' style='padding: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)

col_icon, col_name = st.columns([1, 6])
with col_icon:
    if img:
        st.image(img, width=60)
with col_name:
    st.markdown(f"<h1 style='margin:0; color:#00d4aa; text-shadow: 0 0 20px rgba(0,212,170,0.5);'>{name}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin:0; color:#888;'>{symbol}</h3>", unsafe_allow_html=True)

# Price + Change
change_cls = "price-up" if change >= 0 else "price-down"
st.markdown(f"<h2 style='margin: 12px 0 0 0;'>${price:,.4f} <span class='{change_cls}'>{change:+.2f}%</span></h2>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("### 7-Day Price Action")

if not ohlc.empty:
    # RSI
    delta = ohlc["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / loss))

    # === CANDLES — NEON LINES ONLY ===
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=ohlc['ts'],
        open=ohlc['open'],
        high=ohlc['high'],
        low=ohlc['low'],
        close=ohlc['close'],
        increasing_line_color='#00ff88',
        decreasing_line_color='#ff6b6b'
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 170, 0.1)', color='#888'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 170, 0.1)', color='#888'),
        font=dict(family="Inter", color="#e0e0e0")
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # === RSI ===
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(
        x=ohlc['ts'],
        y=rsi,
        line=dict(color="#00d4aa", width=2),
        name="RSI"
    ))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ff6b6b", annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#00ff88", annotation_text="Oversold")
    fig_rsi.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=20, b=0),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0, 212, 170, 0.1)', range=[0, 100]),
        font=dict(family="Inter", color="#e0e0e0")
    )
    st.plotly_chart(fig_rsi, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("Chart loading...")

st.markdown("</div>", unsafe_allow_html=True)

def sparkline(p):
    if len(p) < 2: return "---"
    b = p[0]
    return ''.join('<span style="color:#00ff88">█</span>' if x >= b else '<span style="color:#ff6b6b">░</span>' for x in p[-30:])[::-1]
st.markdown(f"<div class='glass-card'>7d Trend: {sparkline(spark)}</div>", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center; margin:20px 0;'>
  <span style='background:#00d4aa; color:#000; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:700; animation: pulse 2s infinite;'>
    LIVE
  </span>
</div>
<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.7}}</style>
""", unsafe_allow_html=True)
