import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import pyotp
from datetime import datetime, timedelta
from SmartApi import SmartConnect

st.set_page_config(page_title="Angel Pro Swing Terminal", layout="wide")
st.title("⚡ Pro 15-Day Swing Screener & Risk Manager")
st.caption("Angel One SmartAPI Live Engine | Multi-Factor Momentum + Position Sizing")

# Sidebar - User Risk & Capital Settings
st.sidebar.header("💰 Risk & Capital Management")
account_capital = st.sidebar.number_input("Total Trading Capital (₹)", value=100000, step=10000)
risk_per_trade_pct = st.sidebar.slider("Risk Per Trade (%)", min_value=0.5, max_value=3.0, value=1.5, step=0.5)
target_pct_choice = st.sidebar.slider("Target Return (%)", min_value=8, max_value=15, value=10, step=1)

# Extended High Liquidity Universe (NSE Symbol: Angel Token)
ANGEL_UNIVERSE = {
    "RELIANCE": "2885", "TCS": "11536", "HDFCBANK": "1333", "INFY": "1594",
    "ICICIBANK": "4963", "BHARTIARTL": "10604", "SBIN": "3045", "LT": "11483",
    "ITC": "1660", "TATAMOTORS": "3456", "AXISBANK": "5900", "KOTAKBANK": "1922",
    "TITAN": "3506", "BAJFINANCE": "317", "SUNPHARMA": "3351", "NTPC": "11630",
    "POWERGRID": "14977", "TATASTEEL": "3499", "COALINDIA": "20374", "VEDL": "3063",
    "HINDALCO": "1363", "BEL": "383", "HAL": "2303", "DLF": "14732", "TRENT": "1964"
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
        st.sidebar.error(f"Auth Error: {e}")
        return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss.replace(0, 0.0001))
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period).mean()

# Screen Trigger Button
if st.button("🚀 Run Deep Institutional Scan", use_container_width=True):
    smart_api = get_angel_client()
    if not smart_api:
        st.error("Angel One authentication failed. Check credentials in Secrets.")
    else:
        with st.spinner("Analyzing Trend, Volume Breakouts & Calculating Volatility..."):
            all_results = []
            candles_store = {}
            progress = st.progress(0)
            
            to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            from_date = (datetime.now() - timedelta(days=150)).strftime("%Y-%m-%d 09:15")
            
            for idx, (sym, token) in enumerate(ANGEL_UNIVERSE.items()):
                progress.progress((idx + 1) / len(ANGEL_UNIVERSE))
                try:
                    res = smart_api.getCandleData({
                        "exchange": "NSE",
                        "symboltoken": token,
                        "interval": "ONE_DAY",
                        "fromdate": from_date,
                        "todate": to_date
                    })
                    if not res.get('status') or not res.get('data'):
                        continue
                        
                    df = pd.DataFrame(res['data'], columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    if len(df) < 50:
                        continue
                    
                    df['Time'] = pd.to_datetime(df['Time'])
                    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
                    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
                    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
                    df['RSI'] = calculate_rsi(df['Close'], 14)
                    df['ATR'] = calculate_atr(df, 14)
                    
                    candles_store[sym] = df
                    last = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    cmp = float(last['Close'])
                    ema20 = float(last['EMA20'])
                    ema50 = float(last['EMA50'])
                    rsi = float(last['RSI'])
                    vol = float(last['Volume'])
                    avg_vol = float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0
                    atr = float(last['ATR']) if not pd.isna(last['ATR']) else (cmp * 0.02)
                    
                    # Trend Quality Scoring
                    score = 0
                    if cmp > ema20 > ema50: score += 35
                    elif cmp > ema20: score += 20
                    
                    if 52 <= rsi <= 68: score += 30
                    elif 48 <= rsi < 52: score += 15
                    
                    vol_ratio = vol / avg_vol
                    if vol_ratio >= 1.3: score += 25
                    elif vol_ratio >= 1.0: score += 15
                    
                    # Breakout confirmation
                    if cmp > float(prev['High']): score += 10
                    
                    if score >= 65:
                        # Position Sizing Logic
                        risk_amt = account_capital * (risk_per_trade_pct / 100.0)
                        stop_loss = round(cmp - (1.5 * atr), 2)  # Volatility-based SL
                        risk_per_share = cmp - stop_loss
                        
                        if risk_per_share > 0:
                            qty = int(risk_amt // risk_per_share)
                            trade_capital = round(qty * cmp, 2)
                        else:
                            qty = 0
                            trade_capital = 0
                            
                        target_price = round(cmp * (1 + (target_pct_choice / 100.0)), 2)
                        
                        all_results.append({
                            "Stock": sym,
                            "Setup Score": f"{score}%",
                            "CMP (₹)": round(cmp, 2),
                            f"Target {target_pct_choice}% (₹)": target_price,
                            "Smart SL (ATR)": stop_loss,
                            "RSI": round(rsi, 1),
                            "Vol Surge": f"{round(vol_ratio, 2)}x",
                            "Rec. Qty": qty,
                            "Capital Req (₹)": trade_capital,
                            "_score": score
                        })
                except Exception:
                    continue
                    
            progress.empty()
            if all_results:
                all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
                for item in all_results: del item['_score']
                st.session_state["adv_results"] = all_results
                st.session_state["adv_candles"] = candles_store

# Output UI
if "adv_results" in st.session_state:
    data = st.session_state["adv_results"]
    if data:
        st.success(f"🎯 Total {len(data)} High-Probability Setups Filtered with Sizing!")
        
        display_df = pd.DataFrame(data)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("📊 Interactive Technical Chart with Targets & EMA")
        
        selected_stock = st.selectbox("Stock chunein:", [i["Stock"] for i in data])
        stock_details = next(i for i in data if i["Stock"] == selected_stock)
        
        target_val = stock_details[f"Target {target_pct_choice}% (₹)"]
        sl_val = stock_details["Smart SL (ATR)"]
        
        df_chart = st.session_state["adv_candles"][selected_stock]
        
        # High quality Plotly Candlestick with 20 EMA, 50 EMA and SL/Target
        fig = go.Figure()
        
        # Candles
        fig.add_trace(go.Candlestick(
            x=df_chart['Time'],
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close'],
            name="Price"
        ))
        
        # Indicators
        fig.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['EMA20'], line=dict(color='orange', width=1.5), name="EMA 20"))
        fig.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['EMA50'], line=dict(color='cyan', width=1.5), name="EMA 50"))
        
        # Horizontal Levels
        fig.add_hline(y=target_val, line_dash="dash", line_color="green", annotation_text=f"Target: ₹{target_val}")
        fig.add_hline(y=sl_val, line_dash="dash", line_color="red", annotation_text=f"Smart SL: ₹{sl_val}")
        
        fig.update_layout(
            title=f"{selected_stock} Setup (Orange: 20 EMA | Cyan: 50 EMA)",
            yaxis_title="Price (₹)",
            xaxis_rangeslider_visible=False,
            height=520,
            template="plotly_dark",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Metric Cards for Trade Plan
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Recommended Qty", f"{stock_details['Rec. Qty']} Shares")
        c2.metric("Capital to Deploy", f"₹{stock_details['Capital Req (₹)']}")
        c3.metric("Max Loss on SL", f"₹{round((stock_details['CMP (₹)'] - sl_val) * stock_details['Rec. Qty'], 2)}")
        c4.metric("Potential Profit", f"₹{round((target_val - stock_details['CMP (₹)']) * stock_details['Rec. Qty'], 2)}")
    else:
        st.warning("Aaj market me 65%+ score wala setup nahi mila.")
                
