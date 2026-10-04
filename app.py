import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Pro Live Swing Screener", layout="wide")
st.title("🎯 15-Day Swing Screener + Live Chart")
st.caption("Uptrend + RSI + Volume Momentum Screen with Live Interactive Charts")

WATCHLIST = [
    "TATAMOTORS.NS", "RELIANCE.NS", "SBIN.NS", "INFY.NS", "ICICIBANK.NS", 
    "ITC.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "LT.NS", 
    "MARUTI.NS", "AXISBANK.NS", "KOTAKBANK.NS", "TITAN.NS", "BAJFINANCE.NS",
    "SUNPHARMA.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "COALINDIA.NS",
    "VEDL.NS", "HINDALCO.NS", "BEL.NS", "HAL.NS", "ZOMATO.NS", 
    "DLF.NS", "TRENT.NS", "BHEL.NS", "CANBK.NS", "PNB.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "JIOFIN.NS", "IRFC.NS", "RVNL.NS"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss.replace(0, 0.0001))
    return 100 - (100 / (1 + rs))

# Scan Button
if st.button("🚀 Scan Market Now", use_container_width=True):
    with st.spinner("Analyzing momentum setups..."):
        all_results = []
        progress_bar = st.progress(0)

        for idx, ticker in enumerate(WATCHLIST):
            progress_bar.progress((idx + 1) / len(WATCHLIST))
            try:
                t = yf.Ticker(ticker)
                df = t.history(period="6mo", interval="1d")
                if df.empty or len(df) < 50:
                    continue

                df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
                df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df['Close'], 14)

                last = df.iloc[-1]
                cmp = float(last['Close'])
                ema20 = float(last['EMA20'])
                ema50 = float(last['EMA50'])
                rsi = float(last['RSI'])
                vol = float(last['Volume'])
                avg_vol = float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0

                score = 0
                if cmp > ema20 > ema50: score += 40
                elif cmp > ema20: score += 20
                if 50 <= rsi <= 72: score += 30
                elif 45 <= rsi < 50: score += 15

                vol_ratio = vol / avg_vol
                if vol_ratio >= 1.2: score += 30
                elif vol_ratio >= 0.9: score += 15

                if score >= 60:
                    clean_sym = ticker.replace(".NS", "")
                    all_results.append({
                        "Stock": clean_sym,
                        "Ticker": ticker,
                        "Score": f"{score}%",
                        "CMP (₹)": round(cmp, 2),
                        "Target 10% (₹)": round(cmp * 1.10, 2),
                        "SL 5% (₹)": round(cmp * 0.95, 2),
                        "RSI": round(rsi, 1),
                        "_score": score
                    })
            except Exception:
                continue

        progress_bar.empty()
        if all_results:
            all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
            for item in all_results: del item['_score']
        st.session_state["stocks_data"] = all_results

# Display Table & Live Chart
if "stocks_data" in st.session_state:
    data = st.session_state["stocks_data"]
    if data:
        st.success(f"🎯 Total {len(data)} Setups Found!")
        display_df = pd.DataFrame(data).drop(columns=["Ticker"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📈 Live Interactive Chart")

        col1, col2 = st.columns([2, 1])
        with col1:
            selected_stock = st.selectbox("Stock chunein:", [item["Stock"] for item in data])
        with col2:
            timeframe = st.selectbox("Timeframe:", ["Daily (D)", "1 Hour (60)", "15 Minute (15)"])

        tf_code = "D" if "Daily" in timeframe else ("60" if "1 Hour" in timeframe else "15")

        # Live Embedded TradingView Frame (Direct Iframe - No Restrictions)
        tv_embed_url = (
            f"https://s.tradingview.com/widgetembed/?"
            f"symbol=NSE%3A{selected_stock}"
            f"&interval={tf_code}"
            f"&theme=dark"
            f"&style=1"
            f"&timezone=Asia%2FKolkata"
            f"&withdateranges=1"
            f"&hideideas=1"
        )

        components.html(
            f"""
            <iframe 
                src="{tv_embed_url}" 
                width="100%" 
                height="520" 
                frameborder="0" 
                allowtransparency="true" 
                scrolling="no" 
                style="border-radius: 10px;">
            </iframe>
            """,
            height=540
        )
        
