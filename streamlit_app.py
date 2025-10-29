# streamlit_app.py
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="NEXA • Rankings", layout="wide")

# ----------------------------------------------------------------------
# 1. STYLE
# ----------------------------------------------------------------------
st.markdown(
    """
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
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# 2. FETCH TOP 100 COINS (CoinGecko)
# ----------------------------------------------------------------------
@st.cache_data(ttl=60)
def get_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1}
    headers = {"User-Agent": "NEXA/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return []

coins = get_top_coins()
if not coins:
    st.error("Failed to load rankings.")
    st.stop()

df = pd.DataFrame(coins)
df = df[["id", "symbol", "name", "current_price", "price_change_percentage_24h", "market_cap"]]
df.columns = ["id", "Symbol", "Name", "Price", "24h%", "Market Cap"]

# ----------------------------------------------------------------------
# 3. SEARCH BAR
# ----------------------------------------------------------------------
search = st.text_input("Search coin", placeholder="BTC, Ethereum, SOL...")

if search:
    df = df[df["Name"].str.contains(search, case=False) | df["Symbol"].str.contains(search, case=False)]

# ----------------------------------------------------------------------
# 4. TABLE
# ----------------------------------------------------------------------
st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
st.markdown("### Top 100 Coins")

for _, row in df.iterrows():
    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 3, 2, 1, 2])
    with col1:
        st.write(f"**#{df.index[_] + 1}**")
    with col2:
        st.write(row["Symbol"].upper())
    with col3:
        st.write(row["Name"])
    with col4:
        st.write(f"${row['Price']:,.4f}")
    with col5:
        change = row["24h%"]
        cls = "price-up" if change >= 0 else "price-down"
        st.markdown(f"<span class='{cls}'>{change:+.2f}%</span>", unsafe_allow_html=True)
    with col6:
        if st.button("View", key=row["id"]):
            st.session_state.selected_coin = row["id"]
            st.switch_page("pages/coin.py")
st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# 5. LIVE BADGE
# ----------------------------------------------------------------------
st.markdown(
    """
<div style='text-align:center; margin:20px 0;'>
  <span style='background:#00d4aa; color:#000; padding:4px 12px; border-radius:12px; font-size:12px; font-weight:700; animation: pulse 2s infinite;'>
    LIVE
  </span>
</div>
<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.7}}</style>
""",
    unsafe_allow_html=True,
)