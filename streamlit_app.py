# File: streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# === PAGE CONFIG ===
st.set_page_config(page_title="CryptoMarketCap Pro", page_icon="Chart increasing", layout="wide", initial_sidebar_state="collapsed")

# === ULTRA-SMOOTH GLASS UI ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .main {background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); font-family: 'Inter', sans-serif; color: #e0e0e0;}
    
    /* Glass Cards */
    .glass-card {
        background: rgba(30, 35, 60, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 20px;
        border: 1px solid rgba(0, 212, 170, 0.2);
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    .glass-card:hover {transform: translateY(-8px); box-shadow: 0 20px 50px rgba(0, 212, 170, 0.15);}
    
    /* Headers */
    h1 {color: #00d4aa; text-shadow: 0 0 20px rgba(0, 212, 170, 0.5); font-weight: 700; letter-spacing: -1px;}
    h2 {color: #00ff88; font-weight: 600;}
    
    /* Table */
    .stDataFrame {border: none; border-radius: 16px; overflow: hidden;}
    .stDataFrame > div {background: transparent;}
    .row:hover {background: rgba(0, 212, 170, 0.05) !important; transition: 0.3s;}
    
    /* Price Badge */
    .price-up {color: #00ff88; font-weight: 700; text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);}
    .price-down {color: #ff6b6b; font-weight: 700; text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);}
    
    /* Sparkline */
    .sparkline {font-family: monospace; font-size: 14px; letter-spacing: 1px;}
    
    /* Footer */
    .footer {text-align: center; color: #666; font-size: 14px; margin-top: 60px;}
</style>
""", unsafe_allow_html=True)

# === HEADER ===
st.markdown("<h1>CryptoMarketCap Pro</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#888;'>Live prices • Real-time rankings • Smooth experience</p>", unsafe_allow_html=True)

# === API FETCH ===
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
    try:
        return requests.get(url, params=params, timeout=15).json()
    except:
        return None

# === LIVE DATA ===
data = fetch_top()
if data:
    df = pd.DataFrame(data)
    df = df[["rank", "name", "symbol", "current_price", "price_change_percentage_1h_in_currency",
             "price_change_percentage_24h_in_currency", "price_change_percentage_7d_in_currency",
             "market_cap", "total_volume", "sparkline_in_7d"]]
    df.columns = ["#", "Name", "Symbol", "Price", "1h%", "24h%", "7d%", "Market Cap", "Volume", "7d Spark"]

    # Format
    df["Price"] = df["Price"].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
    df["Market Cap"] = df["Market Cap"].apply(lambda x: f"${x/1e9:.2f}B")
    df["Volume"] = df["Volume"].apply(lambda x: f"${x/1e6:.1f}M")
    
    # Price change badges
    def color_change(val):
        if pd.isna(val): return "N/A"
        color = "price-up" if val >= 0 else "price-down"
        return f"<span class='{color}'>{val:+.2f}%</span>"
    df["1h%"] = df["1h%"].apply(color_change)
    df["24h%"] = df["24h%"].apply(color_change)
    df["7d%"] = df["7d%"].apply(color_change)

    # Sparkline
    def sparkline(spark):
        if not spark or 'price' not in spark: return "───"
        prices = spark['price'][-30:]
        first = prices[0]
        return ''.join(['<span style="color:#00ff88">█</span>' if p > first else '<span style="color:#666">░</span>' for p in prices])[::-1]
    df["7d Spark"] = df["7d Spark"].apply(sparkline)

    # Render
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Top 100 Cryptocurrencies")
    html = df.to_html(escape=False, index=False, classes="stDataFrame")
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.error("Failed to load data. Retrying in 10s...")

# === FOOTER ===
st.markdown("<div class='footer'>Live • Auto-updates every 10s • Built with ❤️ by Grok</div>", unsafe_allow_html=True)
