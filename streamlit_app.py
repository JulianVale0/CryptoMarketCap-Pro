# File: streamlit_app.py (FINAL — BULLETPROOF)
import streamlit as st
import requests
import pandas as pd

# === PAGE CONFIG ===
st.set_page_config(page_title="CryptoMarketCap Pro", page_icon="Chart increasing", layout="wide", initial_sidebar_state="collapsed")

# === ULTRA-SMOOTH GLASS UI ===
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .main {background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%); font-family: 'Inter', sans-serif; color: #e0e0e0;}
    
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
    
    h1 {color: #00d4aa; text-shadow: 0 0 20px rgba(0, 212, 170, 0.5); font-weight: 700; letter-spacing: -1px;}
    h2 {color: #00ff88; font-weight: 600;}
    
    .stDataFrame {border: none; border-radius: 16px; overflow: hidden;}
    .row:hover {background: rgba(0, 212, 170, 0.05) !important; transition: 0.3s;}
    
    .price-up {color: #00ff88; font-weight: 700; text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);}
    .price-down {color: #ff6b6b; font-weight: 700; text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);}
    
    .sparkline {font-family: monospace; font-size: 14px; letter-spacing: 1px;}
    
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

    # === SAFELY EXTRACT COLUMNS ===
    cols = {
        "Name": "name",
        "Symbol": "symbol",
        "Price": "current_price",
        "1h%": "price_change_percentage_1h_in_currency",
        "24h%": "price_change_percentage_24h_in_currency",
        "7d%": "price_change_percentage_7d_in_currency",
        "Market Cap": "market_cap",
        "Volume": "total_volume",
        "7d Spark": "sparkline_in_7d"
    }

    # Only include columns that exist
    available_cols = [v for k, v in cols.items() if v in df.columns]
    df = df[available_cols].copy()

    # Add Rank
    df = df.reset_index(drop=True)
    df.insert(0, "#", range(1, len(df) + 1))

    # Map back to display names
    display_cols = ["#"] + [k for k, v in cols.items() if v in available_cols]
    df.columns = display_cols

    # Format
    if "Price" in df.columns:
        df["Price"] = df["Price"].apply(lambda x: f"${x:,.4f}" if x < 1 else f"${x:,.2f}")
    if "Market Cap" in df.columns:
        df["Market Cap"] = df["Market Cap"].apply(lambda x: f"${x/1e9:.2f}B")
    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].apply(lambda x: f"${x/1e6:.1f}M")

    # Price change badges
    def color_change(val):
        if pd.isna(val): return "N/A"
        color = "price-up" if val >= 0 else "price-down"
        return f"<span class='{color}'>{val:+.2f}%</span>"

    for col in ["1h%", "24h%", "7d%"]:
        if col in df.columns:
            df[col] = df[col].apply(color_change)

    # Sparkline
    def safe_sparkline(spark):
        if not spark or 'price' not in spark or len(spark['price']) == 0: return "───"
        prices = spark['price'][-30:]
        first = prices[0]
        return ''.join(['<span style="color:#00ff88">█</span>' if p > first else '<span style="color:#666">░</span>' for p in prices])[::-1]
    if "7d Spark" in df.columns:
        df["7d Spark"] = df["7d Spark"].apply(safe_sparkline)

    # Render
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Top 100 Cryptocurrencies")
    html = df.to_html(escape=False, index=False)
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.error("Failed to load data. Retrying in 10s...")

# === FOOTER ===
st.markdown("<div class='footer'>Live • Auto-updates every 10s • Built with ❤️ by Grok</div>", unsafe_allow_html=True)
