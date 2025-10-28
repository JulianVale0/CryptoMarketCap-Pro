```python
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
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100, "page": 1, "sparkline": True, "price_change_percentage": "1h,24h,7d"}
    try: return requests.get(url, params=params, timeout=15).json()
    except: return None

data = fetch_top()
if data:
    df = pd.DataFrame(data)
    cols = {"Name": "name", "Symbol": "symbol", "Price": "current_price", "1h%": "price_change_percentage_1h_in_currency",
            "24h%": "price_change_percentage_24h_in_currency", "7d%": "price_change_percentage_7d_in_currency",
            "Market Cap": "market_cap", "Volume": "total_volume", "7d Spark": "sparkline_in_7d"}
    df = df[[v for k,v in cols.items() if v in df.columns]].copy()
    df.insert(0, "#", range(1, len(df)+1))
    df.columns = ["#"] + [k for k,v in cols.items() if v in df.columns]

    if "Price" in df.columns:
        df["Price"] = df["Price"].apply(lambda x: f"${x:,.6f}".rstrip("0").rstrip(".") if x < 1 else f"${x:,.2f}")
    if "Market Cap" in df.columns:
        df["Market Cap"] = df["Market Cap"].apply(lambda x: f"${x/1e9:.2f}B" if pd.notna(x) else "N/A")
    if "Volume" in df.columns:
        df["Volume"] = df["Volume"].apply(lambda x: f"${x/1e6:.1f}M" if pd.notna(x) else "N/A")

    def color(val):
        if pd.isna(val): return "N/A"
        return f"<span class='price-up'>{val:+.2f}%</span>" if val >= 0 else f"<span class='price-down'>{val:+.2f}%</span>"
    for c in ["1h%", "24h%", "7d%"]:
        if c in df.columns: df[c] = df[c].apply(color)

    def sparkline(s):
        if not s or 'price' not in s: return "---"
        p = s['price'][-30:]
        b = p[0]
        return ''.join('<span style="color:#00ff88">█</span>' if x >= b else '<span style="color:#ff6b6b">░</span>' for x in p)[::-1]
    if "7d Spark" in df.columns:
        df["7d Spark"] = df["sparkline_in_7d"].apply(sparkline)

    def row_link(row):
        coin_id = data[row.name]["id"]
        return f'<a href="?id={coin_id}" style="color:inherit;text-decoration:none;display:block;">{row.to_frame().T.to_html(escape=False,index=False,header=False)}</a>'
    rows = "<tr>" + "</tr><tr>".join(df.apply(row_link, axis=1)) + "</tr>"
    head = "".join(f"<th>{h}</th>" for h in df.columns)
    html = f'<table class="crypto-table" style="width:100%;border-collapse:collapse;"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>'

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("## Top 100 Cryptocurrencies")
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.error("Loading data...")

st.markdown("<div class='footer'>Live - Updates every 10s</div>", unsafe_allow_html=True)
