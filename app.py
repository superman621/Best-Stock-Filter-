import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="15-Day Swing Screener", layout="centered")
st.title("📈 15-Day 10% Swing Screener")

WATCHLIST = ["TATAMOTORS.NS", "RELIANCE.NS", "SBIN.NS", "INFY.NS", "ICICIBANK.NS", "ITC.NS", "TCS.NS"]

if st.button("Scan Market Now"):
    with st.spinner("Analyzing stocks..."):
        results = []
        for ticker in WATCHLIST:
            try:
                df = yf.download(ticker, period="3mo", interval="1d", progress=False)
                if len(df) < 30: continue

                df['EMA20'] = df['Close'].ewm(span=20).mean()
                df['EMA50'] = df['Close'].ewm(span=50).mean()
                df['Vol_SMA20'] = df['Volume'].rolling(20).mean()

                last = df.iloc[-1]
                prev = df.iloc[-2]

                uptrend = float(last['Close']) > float(last['EMA20']) > float(last['EMA50'])
                volume_surge = float(last['Volume']) > (1.3 * float(last['Vol_SMA20']))
                breakout = float(last['Close']) > float(prev['High'])

                if uptrend and volume_surge and breakout:
                    cmp = round(float(last['Close']), 2)
                    results.append({
                        "Stock": ticker.replace(".NS", ""),
                        "Buy Price": f"₹{cmp}",
                        "Target (+10%)": f"₹{round(cmp * 1.10, 2)}",
                        "Stop-Loss (-5%)": f"₹{round(cmp * 0.95, 2)}"
                    })
            except:
                continue

        if results:
            st.table(pd.DataFrame(results))
        else:
            st.info("Aaj koi 10% setup match nahi hua.")
          
