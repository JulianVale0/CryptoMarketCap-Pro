import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="CryptoMarketCap Pro", page_icon="Chart increasing", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#00d4aa">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/service-worker.js');
    });
  }
</script>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .main {background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); font-family: 'Inter', sans-serif; color: #e0e0e0;}
    .glass-card {
        background: rgba(30, 35, 60, 0.7); backdrop-filter: blur(16px); border-radius: 20px;
        border: 1px solid rgba(0, 212, 170, 0.2); padding: 24px; margin: 16px 0;
        box-shadow: 0 12px 32px rgba(0,0,0,0.4); transition: all 0.4s;
    }
    .glass-card:hover {transform: translateY(-8px);}
    h1 {color: #00d4aa; text-shadow: 0 0 20px rgba(0,212,170,0.5);}
    .crypto-table tr:hover {background: rgba(0,212,170,0.08);}
    .crypto-table a {color: inherit; text-decoration: none; display: block;}
    .price-up {color: #00ff88; font-weight: 700;}
    .price-down {color: #ff6b6b; font-weight: 700;}
    .sparkline {font-family: monospace; font-size: 14px;}
    .footer {text-align: center; color: #666; font-size: 14px; margin-top: 60px;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>CryptoMarketCap Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>Live prices - Real-time rankings</p>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center; margin:8px 0;'>
  <span style='background:#00d4aa; color:#000; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:700; animation: pulse 2s infinite;'>LIVE</span>
</div>
<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.7}}</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def fetch_top():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": True,
        "price_change_percentage": "1h,24h,7d"
    }
    headers = {"User-Agent": "CryptoMarketCap-Pro/1.0"}
    try:
        return requests.get(url, params=params, headers=headers, timeout=15).json()
    except:
        return None

with st.spinner("Loading live data..."):
    data = fetch_top()

if data and len(data) > 0:
    # === ALL YOUR TABLE CODE HERE (df, formatting, clickable rows) ===
    # ... keep everything from df = pd.DataFrame(data) to st.markdown("</div>", unsafe_allow_html=True)
else:
    st.error("Failed to load data. Check internet or CoinGecko status. Retrying in 10s...")
    st.rerun()  # Auto-retry

st.markdown("<div class='footer'>Live - Updates every 10s</div>", unsafe_allow_html=True)
