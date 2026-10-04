import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="15-Day Swing Screener", layout="centered")
st.title("📈 15-Day 10% Swing Screener")
st.caption("Filters stocks with EMA Uptrend + High Relative Volume + Bullish Momentum")

# Nifty 50 & Momentum Midcap Stocks
WATCHLIST = [
    "TATAMOTORS.NS", "RELIANCE.NS", "SBIN.NS", "INFY.NS", "ICICIBANK.NS", 
    "ITC.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "LT.NS", 
    "MARUTI.NS", "AXISBANK.NS", "KOTAKBANK.NS", "TITAN.NS", "BAJFINANCE.NS",
    "SUNPHARMA.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "COALINDIA.NS",
    "VEDL.NS", "HINDALCO.NS", "BEL.NS", "HAL.NS", "ZOMATO.NS", 
    "DLF.NS", "TRENT.NS", "BHEL.NS", "CANBK.NS", "PNB.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "JIOFIN.NS", "IRFC.NS", "RVNL.NS"
]

if st.button("🚀 Scan Market Now", use_container_width=True):
    with st.spinner("Scanning top momentum stocks..."):
        results = []
        for ticker in WATCHLIST:
            try:
                # 3 month daily data
                df = yf.download(ticker, period="3mo", interval="1d", progress=False)
                if len(df) < 30:
                    continue

                # MultiIndex fix if yfinance returns multi-level columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
                df['Vol_SMA20'] = df['Volume'].rolling(20).mean()

                last = df.iloc[-1]
                prev = df.iloc[-2]

                close_price = float(last['Close'])
                ema20 = float(last['EMA20'])
                ema50 = float(last['EMA50'])
                vol = float(last['Volume'])
                avg_vol = float(last['Vol_SMA20'])

                # Practical 10% Swing Filter:
                # 1. Price above 20 EMA and 50 EMA (Clear Uptrend)
                # 2. Bullish day (Close > Open)
                # 3. Volume is at least above 20-day average
                # 4. Price near 20-day high (within 5% of recent high)
                recent_high = float(df['High'].tail(20).max())
                near_high = close_price >= (recent_high * 0.95)
                
                uptrend = close_price > ema20 > ema50
                bullish_candle = close_price > float(last['Open'])
                good_volume = vol >= avg_vol

                if uptrend and near_high and bullish_candle and good_volume:
                    cmp = round(close_price, 2)
                    target = round(cmp * 1.10, 2)       # 10% Target
                    sl = round(cmp * 0.95, 2)           # 5% Stop-loss
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "CMP (₹)": cmp,
                        "Target 10% (₹)": target,
                        "SL 5% (₹)": sl
                    })
            except Exception:
                continue

        if results:
            st.success(f"{len(results)} potential swing setups found!")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.warning("Aaj market close hone tak koi setup match nahi hua.")
            
