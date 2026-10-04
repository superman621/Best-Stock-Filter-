import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Swing Screener Pro", layout="wide")
st.title("🎯 15-Day Swing Screener (10% Target Setup)")
st.caption("Filters high-momentum stocks with Native Interactive Candlestick Charts")

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
    with st.spinner("Analyzing stocks and technical setups..."):
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

                if score >= 60:
                    all_results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Ticker": ticker,
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
        
        if all_results:
            all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
            for item in all_results:
                del item['_score']
        
        st.session_state["stocks_data"] = all_results

# Display Section
if "stocks_data" in st.session_state:
    data = st.session_state["stocks_data"]
    if data:
        st.success(f"🎯 Total {len(data)} Stocks Filtered!")
        display_df = pd.DataFrame(data).drop(columns=["Ticker"])
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.subheader("📊 Direct Candlestick Chart View")

        stock_symbols = [item["Stock"] for item in data]
        selected_stock = st.selectbox("Chart dekhne ke liye stock chunein:", stock_symbols)
        
        # Selected stock details
        selected_item = next(item for item in data if item["Stock"] == selected_stock)
        target_val = selected_item["Target 10% (₹)"]
        sl_val = selected_item["Stop-Loss 5% (₹)"]

        # Fetch candle data for selected stock
        hist = yf.Ticker(selected_item["Ticker"]).history(period="3mo", interval="1d")

        # Native Candlestick Chart
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name=selected_stock
        )])

        # Target (10%) & Stop-loss (5%) horizontal lines
        fig.add_hline(y=target_val, line_dash="dash", line_color="green", annotation_text=f"Target 10%: ₹{target_val}")
        fig.add_hline(y=sl_val, line_dash="dash", line_color="red", annotation_text=f"SL 5%: ₹{sl_val}")

        fig.update_layout(
            title=f"{selected_stock} Daily Chart (Target & SL Levels)",
            yaxis_title="Price (₹)",
            xaxis_rangeslider_visible=False,
            height=450,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        # TradingView link for external detailed view
        st.link_button(f"🌐 Open {selected_stock} in TradingView App/Site", f"https://in.tradingview.com/chart/?symbol=NSE:{selected_stock}")
    else:
        st.warning("Aaj koi setup match nahi hua.")
        
