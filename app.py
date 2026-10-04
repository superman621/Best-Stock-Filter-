import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyotp
from datetime import datetime, timedelta
from SmartApi import SmartConnect

# Set Page Config
st.set_page_config(
    page_title="AlphaPulse | Institutional Swing Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Institutional CSS Styling
st.markdown("""
<style>
    /* Global Background & Font */
    .stApp {
        background-color: #0b0e14;
        color: #e1e7ec;
    }
    
    /* Clean Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #11151f;
        border-right: 1px solid #1e2638;
    }

    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #141a29;
        border: 1px solid #232d42;
        padding: 14px 18px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetric"] label {
        color: #8b9bb4 !important;
        font-weight: 500;
        font-size: 0.85rem;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00d2c4 !important;
        font-family: 'Courier New', monospace;
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0052cc 0%, #00c49f 100%);
        color: white;
        border: none;
        padding: 0.65rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px rgba(0, 196, 159, 0.25);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0, 196, 159, 0.4);
        color: #ffffff;
    }

    /* Dataframe Header styling */
    .stDataFrame {
        border: 1px solid #1f2738;
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# App Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("<h2 style='margin-bottom: 0px;'>⚡ ALPHAPULSE <span style='font-size: 1rem; color: #00d2c4;'>PRO TERMINAL</span></h2>", unsafe_allow_html=True)
    st.caption("Quantitative 15-Day Swing Scanner • Angel One SmartAPI Feed • Risk Matrix Engine")
with col_status:
    st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='background:#102a27; color:#00e699; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight:600; border: 1px solid #00e699;'>LIVE EXCHANGE SYNC</span></div>", unsafe_allow_html=True)

st.markdown("---")

# Sidebar Configuration
st.sidebar.markdown("### 🎛️ Risk Engine")
account_capital = st.sidebar.number_input("Portfolio Capital (₹)", value=100000, step=25000)
risk_per_trade_pct = st.sidebar.slider("Risk Per Execution (%)", min_value=0.5, max_value=3.0, value=1.5, step=0.25)
target_pct_choice = st.sidebar.slider("Alpha Target (%)", min_value=8, max_value=15, value=10, step=1)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔬 Strategy Filters")
min_score = st.sidebar.slider("Minimum Setup Score", min_value=50, max_value=85, value=65, step=5)

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
        st.sidebar.error(f"Auth Exception: {e}")
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

# Scan Execution Trigger
if st.button("⚡ EXECUTE MARKET SCAN", use_container_width=True):
    smart_api = get_angel_client()
    if not smart_api:
        st.error("SmartAPI Session failed. Please check credentials in Secrets.")
    else:
        with st.spinner("Screening universe via WebSocket / REST Gateways..."):
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
                    
                    score = 0
                    if cmp > ema20 > ema50: score += 35
                    elif cmp > ema20: score += 20
                    
                    if 52 <= rsi <= 68: score += 30
                    elif 48 <= rsi < 52: score += 15
                    
                    vol_ratio = vol / avg_vol
                    if vol_ratio >= 1.3: score += 25
                    elif vol_ratio >= 1.0: score += 15
                    
                    if cmp > float(prev['High']): score += 10
                    
                    if score >= min_score:
                        risk_amt = account_capital * (risk_per_trade_pct / 100.0)
                        stop_loss = round(cmp - (1.5 * atr), 2)
                        risk_per_share = cmp - stop_loss
                        
                        qty = int(risk_amt // risk_per_share) if risk_per_share > 0 else 0
                        trade_capital = round(qty * cmp, 2)
                        target_price = round(cmp * (1 + (target_pct_choice / 100.0)), 2)
                        
                        all_results.append({
                            "Symbol": sym,
                            "Score": f"{score}%",
                            "CMP (₹)": round(cmp, 2),
                            f"Target +{target_pct_choice}%": target_price,
                            "Smart SL": stop_loss,
                            "RSI": round(rsi, 1),
                            "Vol Surge": f"{round(vol_ratio, 2)}x",
                            "Position Qty": qty,
                            "Deploy Cap (₹)": trade_capital,
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

# Display Terminal Board
if "adv_results" in st.session_state:
    data = st.session_state["adv_results"]
    if data:
        # KPI Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Universe Scanned", f"{len(ANGEL_UNIVERSE)} Liquid Assets")
        m2.metric("Filtered Setups", f"{len(data)} Stocks")
        m3.metric("Risk Budget / Trade", f"₹{round(account_capital * (risk_per_trade_pct / 100.0), 2)}")
        m4.metric("Avg Quality Score", f"{round(sum(int(x['Score'].replace('%','')) for x in data)/len(data))}%")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # Chart & Analysis Workspace
        st.subheader("📈 Institutional Candlestick Matrix")
        
        col_select, col_empty = st.columns([1, 2])
        with col_select:
            selected_stock = st.selectbox("Inspect Setup Chart:", [i["Symbol"] for i in data])
            
        stock_details = next(i for i in data if i["Symbol"] == selected_stock)
        target_val = stock_details[f"Target +{target_pct_choice}%"]
        sl_val = stock_details["Smart SL"]
        
        df_chart = st.session_state["adv_candles"][selected_stock]
        
        # Dual Pane Chart: Price (Top) + Volume (Bottom)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
        
        # Candlesticks
        fig.add_trace(go.Candlestick(
            x=df_chart['Time'],
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close'],
            name="Price",
            increasing_line_color='#00e699',
            decreasing_line_color='#ff3366'
        ), row=1, col=1)
        
        # Moving Averages
        fig.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['EMA20'], line=dict(color='#ffaa00', width=1.5), name="EMA 20"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart['Time'], y=df_chart['EMA50'], line=dict(color='#00bfff', width=1.5), name="EMA 50"), row=1, col=1)
        
        # Dynamic Target & SL lines
        fig.add_hline(y=target_val, line_dash="dash", line_color="#00e699", annotation_text=f" Target: ₹{target_val}", annotation_position="top right", row=1, col=1)
        fig.add_hline(y=sl_val, line_dash="dash", line_color="#ff3366", annotation_text=f" SL: ₹{sl_val}", annotation_position="bottom right", row=1, col=1)
        
        # Volume Bars with color matching candle direction
        vol_colors = ['#00e699' if c >= o else '#ff3366' for c, o in zip(df_chart['Close'], df_chart['Open'])]
        fig.add_trace(go.Bar(x=df_chart['Time'], y=df_chart['Volume'], marker_color=vol_colors, name="Volume", opacity=0.8), row=2, col=1)
        
        fig.update_layout(
            paper_bgcolor='#0b0e14',
            plot_bgcolor='#11151f',
            xaxis_rangeslider_visible=False,
            height=580,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#8b9bb4")),
            font=dict(family="Courier New, monospace", color="#8b9bb4")
        )
        fig.update_yaxes(gridcolor='#1e2638', row=1, col=1)
        fig.update_yaxes(gridcolor='#1e2638', row=2, col=1)
        fig.update_xaxes(gridcolor='#1e2638')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Position Sizing Breakdown Cards
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Optimal Allocation", f"{stock_details['Position Qty']} Shares")
        c2.metric("Total Exposure", f"₹{stock_details['Deploy Cap (₹)']}")
        c3.metric("Calculated Risk (SL)", f"-₹{round((stock_details['CMP (₹)'] - sl_val) * stock_details['Position Qty'], 2)}")
        c4.metric("Reward Expectation", f"+₹{round((target_val - stock_details['CMP (₹)']) * stock_details['Position Qty'], 2)}")
    else:
        st.warning("No high-probability momentum setups met the institutional filters today.")
            
