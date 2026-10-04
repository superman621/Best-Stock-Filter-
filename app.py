import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pyotp
from datetime import datetime, timedelta
from SmartApi import SmartConnect

st.set_page_config(page_title="Angel One Swing Screener", layout="wide")
st.title("🎯 Angel One Pro Swing Screener (10% Target)")
st.caption("Direct NSE Real-Time Feed powered by Angel One SmartAPI")

# Top Liquid Swing Stocks (Symbol: NSE Token)
ANGEL_STOCKS = {
    "SBIN": "3045",
    "TATAMOTORS": "3456",
    "RELIANCE": "2885",
    "INFY": "1594",
    "ICICIBANK": "4963",
    "ITC": "1660",
    "TCS": "11536",
    "HDFCBANK": "1333",
    "BHARTIARTL": "10604",
    "LT": "11483",
    "AXISBANK": "5900",
    "KOTAKBANK": "1922",
    "TITAN": "3506",
    "TATASTEEL": "3499",
    "BEL": "383"
}

def get_angel_client():
    try:
        api_key = st.secrets["ANGEL_API_KEY"]
        client_code = st.secrets["ANGEL_CLIENT_CODE"]
        pin = st.secrets["ANGEL_PIN"]
        totp_key = st.secrets["ANGEL_TOTP_KEY"]
        
        totp = pyotp.TOTP(totp_key).now()
        smart_api = SmartConnect(api_key=api_key)
        data = smart_api.generateSession(client_code, pin, totp)
        if data['status']:
            return smart_api
        return None
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss.replace(0, 0.0001))
    return 100 - (100 / (1 + rs))

if st.button("🚀 Scan Market via Angel One API", use_container_width=True):
    smart_api = get_angel_client()
    if not smart_api:
        st.error("Angel One login fail ho gaya. Kripya Streamlit Secrets me API Key, PIN aur TOTP check karein.")
    else:
        with st.spinner("Angel One servers se live candle data scan ho raha hai..."):
            all_results = []
            candles_store = {}
            progress = st.progress(0)
            
            # Dates setup (Pichhle 6 mahine)
            to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            from_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d 09:15")
            
            for idx, (sym, token) in enumerate(ANGEL_STOCKS.items()):
                progress.progress((idx + 1) / len(ANGEL_STOCKS))
                try:
                    historic_param = {
                        "exchange": "NSE",
                        "symboltoken": token,
                        "interval": "ONE_DAY",
                        "fromdate": from_date,
                        "todate": to_date
                    }
                    res = smart_api.getCandleData(historic_param)
                    if not res.get('status') or not res.get('data'):
                        continue
                        
                    # Format: [timestamp, open, high, low, close, volume]
                    df = pd.DataFrame(res['data'], columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    if len(df) < 35:
                        continue
                    
                    df['Time'] = pd.to_datetime(df['Time'])
                    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
                    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
                    df['RSI'] = calculate_rsi(df['Close'], 14)
                    
                    candles_store[sym] = df
                    last = df.iloc[-1]
                    
                    cmp = float(last['Close'])
                    ema20 = float(last['EMA20'])
                    ema50 = float(last['EMA50'])
                    rsi = float(last['RSI'])
                    vol = float(last['Volume'])
                    avg_vol = float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0
                    
                    # 10% Swing Score
                    score = 0
                    if cmp > ema20 > ema50: score += 40
                    elif cmp > ema20: score += 20
                    if 50 <= rsi <= 72: score += 30
                    elif 45 <= rsi < 50: score += 15
                    
                    vol_ratio = vol / avg_vol
                    if vol_ratio >= 1.2: score += 30
                    elif vol_ratio >= 0.9: score += 15
                    
                    if score >= 60:
                        all_results.append({
                            "Stock": sym,
                            "Score": f"{score}%",
                            "CMP (₹)": round(cmp, 2),
                            "Target 10% (₹)": round(cmp * 1.10, 2),
                            "SL 5% (₹)": round(cmp * 0.95, 2),
                            "RSI": round(rsi, 1),
                            "Vol Ratio": f"{round(vol_ratio, 2)}x",
                            "_score": score
                        })
                except Exception:
                    continue
                    
            progress.empty()
            if all_results:
                all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
                for item in all_results: del item['_score']
                st.session_state["angel_results"] = all_results
                st.session_state["candles_store"] = candles_store

# Display Output
if "angel_results" in st.session_state:
    data = st.session_state["angel_results"]
    if data:
        st.success(f"🎯 Total {len(data)} Setups Found via Angel One Data!")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("📊 Direct Candlestick Chart (Angel One Official Feed)")
        
        selected_stock = st.selectbox("Stock chunein:", [i["Stock"] for i in data])
        stock_data = next(i for i in data if i["Stock"] == selected_stock)
        target = stock_data["Target 10% (₹)"]
        sl = stock_data["SL 5% (₹)"]
        
        hist_df = st.session_state["candles_store"][selected_stock]
        
        # Native interactive chart with Target & SL
        fig = go.Figure(data=[go.Candlestick(
            x=hist_df['Time'],
            open=hist_df['Open'],
            high=hist_df['High'],
            low=hist_df['Low'],
            close=hist_df['Close'],
            name=selected_stock
        )])
        fig.add_hline(y=target, line_dash="dash", line_color="green", annotation_text=f"Target 10%: ₹{target}")
        fig.add_hline(y=sl, line_dash="dash", line_color="red", annotation_text=f"SL 5%: ₹{sl}")
        fig.update_layout(
            title=f"{selected_stock} Daily Chart",
            yaxis_title="Price (₹)",
            xaxis_rangeslider_visible=False,
            height=480,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aaj koi setup match nahi hua.")
            
