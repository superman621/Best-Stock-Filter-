import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Pro Swing Screener", layout="wide")
st.title("🎯 Pro 15-Day Swing Screener (10% Target)")
st.caption("Filters: EMA Trend (20>50) + RSI Momentum (55-70) + High Volume Surge + TradingView Link")

# Liquid High-Beta & Momentum Stocks (Nifty 100 & Midcap Leaders)
WATCHLIST = [
    "TATAMOTORS.NS", "RELIANCE.NS", "SBIN.NS", "INFY.NS", "ICICIBANK.NS", 
    "ITC.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "LT.NS", 
    "MARUTI.NS", "AXISBANK.NS", "KOTAKBANK.NS", "TITAN.NS", "BAJFINANCE.NS",
    "SUNPHARMA.NS", "NTPC.NS", "POWERGRID.NS", "TATASTEEL.NS", "COALINDIA.NS",
    "VEDL.NS", "HINDALCO.NS", "BEL.NS", "HAL.NS", "ZOMATO.NS", 
    "DLF.NS", "TRENT.NS", "BHEL.NS", "CANBK.NS", "PNB.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "JIOFIN.NS", "IRFC.NS", "RVNL.NS",
    "DIXON.NS", "POLYCAB.NS", "PERSISTENT.NS", "KPITTECH.NS", "BOSCHLTD.NS"
]

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if st.button("⚡ Scan Market (Advance)", use_container_width=True):
    with st.spinner("Analyzing momentum, RSI & volume breakouts..."):
        results = []
        progress_bar = st.progress(0)
        
        for idx, ticker in enumerate(WATCHLIST):
            progress_bar.progress((idx + 1) / len(WATCHLIST))
            try:
                # 6 months daily candles for accurate RSI & EMA
                df = yf.download(ticker, period="6mo", interval="1d", progress=False)
                if len(df) < 55:
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # Technical Indicators
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

                # Advance Screening Logic:
                # 1. Structural Uptrend: Price > 20 EMA > 50 EMA
                uptrend = cmp > ema20 > ema50
                
                # 2. RSI Sweet Spot: Between 55 and 70 (Strong momentum, not heavily overbought)
                rsi_ok = 55 <= rsi <= 72
                
                # 3. Volume confirmation: Current volume > 1.25x of 20-day average
                vol_surge = vol >= (1.25 * avg_vol)
                
                # 4. Breakout: Closing above yesterday's High
                breakout = cmp > float(prev['High'])

                if uptrend and rsi_ok and vol_surge and breakout:
                    clean_symbol = ticker.replace(".NS", "")
                    tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{clean_symbol}"
                    
                    target = round(cmp * 1.10, 2)
                    sl = round(cmp * 0.95, 2)
                    vol_times = round(vol / avg_vol, 2)

                    results.append({
                        "Stock": clean_symbol,
                        "CMP (₹)": round(cmp, 2),
                        "Target 10% (₹)": target,
                        "Stop-Loss 5% (₹)": sl,
                        "RSI (14)": round(rsi, 1),
                        "Vol Surge": f"{vol_times}x",
                        "Chart": tv_link
                    })
            except Exception:
                continue

        progress_bar.empty()

        if results:
            st.success(f"🎯 Total {len(results)} High-Probability Setups Found!")
            df_res = pd.DataFrame(results)
            
            # Display interactive table with clickable TradingView chart links
            st.dataframe(
                df_res,
                column_config={
                    "Chart": st.column_config.LinkColumn("TradingView", display_text="Open Chart ↗")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("Aaj market me 1.25x volume + RSI momentum condition match karne wala stock nahi mila. Market close hone ke baad ya kal dobara try karein.")
            
