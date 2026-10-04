import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="Swing Screener Pro", layout="wide")
st.title("🎯 15-Day Swing Screener (10% Target Setup)")
st.caption("Auto-ranks top momentum stocks based on Trend + Volume + RSI")

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

if st.button("🚀 Scan Market Now", use_container_width=True):
    with st.spinner("Analyzing stocks..."):
        all_results = []
        progress_bar = st.progress(0)

        for idx, ticker in enumerate(WATCHLIST):
            progress_bar.progress((idx + 1) / len(WATCHLIST))
            try:
                # Direct history use karte hain (no multi-index error)
                t = yf.Ticker(ticker)
                df = t.history(period="6mo", interval="1d")
                
                if df.empty or len(df) < 50:
                    continue

                # Indicators
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

                # Score System (Taaki 0 results na aayein):
                # +40 points: Price above 20 EMA and 50 EMA
                # +30 points: Healthy RSI (50 to 70)
                # +30 points: Volume Surge (Above average)
                score = 0
                if cmp > ema20 > ema50:
                    score += 40
                elif cmp > ema20:
                    score += 20
                    
                if 50 <= rsi <= 72:
                    score += 30
                elif 45 <= rsi < 50:
                    score += 15

                vol_ratio = vol / avg_vol
                if vol_ratio >= 1.2:
                    score += 30
                elif vol_ratio >= 0.9:
                    score += 15

                # Sirf wahi stocks show honge jinka setup 60%+ strong hai
                if score >= 60:
                    all_results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Setup Strength": f"{score}%",
                        "CMP (₹)": round(cmp, 2),
                        "Target 10% (₹)": round(cmp * 1.10, 2),
                        "Stop-Loss 5% (₹)": round(cmp * 0.95, 2),
                        "RSI": round(rsi, 1),
                        "Volume Ratio": f"{round(vol_ratio, 2)}x",
                        "_score": score
                    })
            except Exception:
                continue

        progress_bar.empty()
        
        # Sort best setups on top
        if all_results:
            all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
            for item in all_results:
                del item['_score']
        
        st.session_state["stocks_data"] = all_results

# Display Table & Interactive TradingView Chart
if "stocks_data" in st.session_state:
    data = st.session_state["stocks_data"]
    if data:
        st.success(f"🎯 Total {len(data)} High-Probability Swing Setups Found!")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📊 Live Chart View")

        stock_symbols = [item["Stock"] for item in data]
        selected = st.selectbox("Chart dekhne ke liye stock chunein:", stock_symbols)

        tv_html = f"""
        <div class="tradingview-widget-container" style="height:500px;width:100%">
          <div id="tradingview_chart" style="height:500px;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget(
          {{
            "autosize": true,
            "symbol": "NSE:{selected}",
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
        """
        components.html(tv_html, height=520)
    else:
        st.warning("Filhal market condition weak hai, koi bhi stock minimum 60% setup match nahi kar raha.")
        
