import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Coin Detail", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    body {font-family: 'Inter', sans-serif;}
    .main {background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);}
    .glass-card {
        background: rgba(30,35,60,0.7);
        backdrop-filter: blur(16px);
        border-radius: 20px;
        border: 1px solid rgba(0,212,170,0.2);
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    }
    .glass-card:hover {transform: translateY(-4px);}
    .price-up {color:#00ff88; font-weight:700;}
    .price-down {color:#ff6b6b; font-weight:700;}
    .back-btn {color:#00d4aa; text-decoration:none; font-weight:600;}
</style>
""", unsafe_allow_html=True)

st.markdown("<a href='/' class='back-btn'>Back to Rankings</a><br><br>", unsafe_allow_html=True)

query_params = st.query_params
coin_id = query_params.get("id", [None])[0]
if not coin_id:
    st.error("No coin selected.")
    st.stop()

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
        return df.iloc[::4].reset_index(drop=True)
    except:
        return pd.DataFrame()

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

col1, col2 = st.columns([1, 4])
with col1:
    if img: st.image(img, width=80)
with col2:
    st.markdown(f"# {name} <sup style='color:#888; font-size:0.6em;'>{symbol}</sup>", unsafe_allow_html=True)
    cls = "price-up" if change >= 0 else "price-down"
    st.markdown(f"<h2>${price:,.4f} <span class='{cls}'>{change:+.2f}%</span></h2>", unsafe_allow_html=True)

st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Market Cap", f"${cap/1e9:.2f}B" if cap else "N/A")
with c2: st.metric("24h Volume", f"${vol/1e6:.1f}M" if vol else "N/A")
with c3: st.metric("ATH", f"${ath:,.2f}" if ath else "N/A")
with c4: st.metric("ATL", f"${atl:,.4f}" if atl else "N/A")
st.markdown("</div>", unsafe_allow_html=True)

ohlc = get_ohlc(coin_id)
if not ohlc.empty:
    delta = ohlc["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss))

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=ohlc['ts'], open=ohlc['open'], high=ohlc['high'], low=ohlc['low'], close=ohlc['close']))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=500, margin=dict(t=40))
    st.plotly_chart(fig, use_container_width=True)

    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=ohlc['ts'], y=rsi, line=dict(color="#00d4aa")))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ff6b6b")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="#00ff88")
    fig_rsi.update_layout(height=180, margin=dict(t=0), template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)
else:
    st.info("Chart loading...")

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
