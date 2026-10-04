import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Pro Swing Screener with Chart", layout="wide")
st.title("🎯 Pro 15-Day Swing Screener (10% Target)")
st.caption("Filters: EMA Trend + RSI + Volume Breakout with Embedded TradingView Charts")

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
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Scan Button
if st.button("⚡ Scan Market", use_container_width=True):
    with st.spinner("Analyzing stocks and charts..."):
        results = []
        progress_bar = st.progress(0)
        
        for idx, ticker in enumerate(WATCHLIST):
            progress_bar.progress((idx + 1) / len(WATCHLIST))
            try:
                df = yf.download(ticker, period="6mo", interval="1d", progress=False)
                if len(df) < 50:
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
                df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
                df['RSI'] = calculate_rsi(df['Close'], 14)

                last = df.iloc[-1]
                prev = df.iloc[-2]

                cmp = float(last['Close'])
                ema20 = float(last['EMA20'])
                ema50 = float(last['EMA50'])
                rsi = float(last['RSI'])
                vol = float(last['Volume'])
                avg_vol = float(last['Vol_SMA20'])

                # Filter Conditions
                uptrend = cmp > ema20 > ema50
                rsi_ok = 55 <= rsi <= 72
                vol_surge = vol >= (1.2 * avg_vol)
                breakout = cmp > float(prev['High'])

                if uptrend and rsi_ok and vol_surge and breakout:
                    clean_sym = ticker.replace(".NS", "")
                    results.append({
                        "Stock": clean_sym,
                        "CMP (₹)": round(cmp, 2),
                        "Target 10% (₹)": round(cmp * 1.10, 2),
                        "Stop-Loss 5% (₹)": round(cmp * 0.95, 2),
                        "RSI": round(rsi, 1),
                        "Volume": f"{round(vol / avg_vol, 2)}x"
                    })
            except Exception:
                continue

        progress_bar.empty()
        st.session_state["scan_results"] = results

# Display Data & Charts
if "scan_results" in st.session_state:
    data = st.session_state["scan_results"]
    if data:
        st.success(f"{len(data)} Stocks Filtered!")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📊 Live TradingView Chart View")

        # Dropdown to select filtered stock
        stock_names = [item["Stock"] for item in data]
        selected_stock = st.selectbox("Stock select karein jiska chart dekhna hai:", stock_names)

        # TradingView Widget Embed
        tv_html = f"""
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container" style="height:500px;width:100%">
          <div id="tradingview_chart" style="height:500px;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "autosize": true,
            "symbol": "NSE:{selected_stock}",
            "interval": "D",
            "timezone": "Asia/Kolkata",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_chart"
          }}
          );
          </script>
        </div>
        <!-- TradingView Widget END -->
        """
        components.html(tv_html, height=520)

    else:
        st.warning("Aaj market close hone tak koi setup match nahi hua.")
        
