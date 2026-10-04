import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyotp
from datetime import datetime, timedelta
from SmartApi import SmartConnect
from supabase import create_client, Client

# Page Setup
st.set_page_config(
    page_title="Sandeep Kumar | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast Professional CSS
st.markdown("""
<style>
    /* Streamlit Chrome & Headers Hide */
    #MainMenu {visibility: hidden !important; display: none !important;}
    header {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    footer {visibility: hidden !important; display: none !important;}
    [data-testid="manage-app-button"] {display: none !important; visibility: hidden !important;}
    .stAppDeployButton {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"] {display: none !important; visibility: hidden !important;}
    iframe[title="Manage app"] {display: none !important; visibility: hidden !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}

    /* Global Dark Theme */
    .stApp { background-color: #080a0f; color: #f1f5f9; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #0f131c; border-right: 1px solid #1e2638; }
    
    /* Professional Glassmorphism Login Card */
    div[data-testid="stForm"] {
        background: #111622 !important;
        border: 1px solid #232d42 !important;
        border-radius: 16px !important;
        padding: 30px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
    }

    /* Input Fields Fix - Text Har Haal Me Clear Dikhne Ke Liye */
    .stTextInput label {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.3px !important;
    }
    .stTextInput div[data-baseweb="input"] {
        background-color: #161c2b !important;
        border: 1px solid #2d384e !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }
    .stTextInput div[data-baseweb="input"]:focus-within {
        border-color: #00d2c4 !important;
        box-shadow: 0 0 10px rgba(0, 210, 196, 0.2) !important;
    }
    .stTextInput input {
        color: #ffffff !important;
        font-size: 0.95rem !important;
        caret-color: #00d2c4 !important;
    }
    .stTextInput input::placeholder {
        color: #64748b !important;
    }

    /* Radio Button Labels Styling */
    div[data-testid="stRadio"] label {
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }

    /* Neon Gradient Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0052cc 0%, #00c49f 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 0.7rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-radius: 10px !important;
        width: 100% !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0, 196, 159, 0.45) !important;
    }

    /* Dashboard Metrics */
    div[data-testid="stMetric"] {
        background-color: #111622;
        border: 1px solid #1e2638;
        padding: 14px 18px;
        border-radius: 10px;
    }
    div[data-testid="stMetric"] label { color: #8b9bb4 !important; font-size: 0.8rem; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00d2c4 !important;
        font-family: monospace;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# Supabase Auth Client Init
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"].strip().rstrip("/")
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(url, key)

supabase = init_supabase()

if "user" not in st.session_state:
    st.session_state["user"] = None

# ================= PROFESSIONAL AUTHENTICATION GATEWAY =================
if st.session_state["user"] is None:
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    # Center Column for Login Box
    _, col_auth, _ = st.columns([1, 1.3, 1])
    with col_auth:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 25px;'>
            <div style='display: inline-block; background: rgba(0, 210, 196, 0.1); border: 1px solid rgba(0, 210, 196, 0.3); border-radius: 50%; padding: 12px; margin-bottom: 12px;'>
                <span style='font-size: 1.8rem;'>⚡</span>
            </div>
            <h2 style='margin: 0; font-weight: 800; letter-spacing: 0.5px;'>SANDEEP KUMAR</h2>
            <p style='color: #00d2c4; font-size: 0.85rem; font-weight: 600; margin: 4px 0 0 0; letter-spacing: 1px;'>INSTITUTIONAL SWING TERMINAL</p>
            <p style='color: #64748b; font-size: 0.8rem; margin-top: 6px;'>Enter your credentials to access live quantitative feeds</p>
        </div>
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("Access Level", ["Existing Member (Sign In)", "New Member (Sign Up)"], horizontal=True, label_visibility="collapsed")
        
        with st.form("auth_form"):
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
            email = st.text_input("EMAIL ADDRESS", placeholder="trader@quantdesk.com")
            password = st.text_input("PASSWORD", type="password", placeholder="••••••••••••")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            btn_title = "PROCEED TO TERMINAL" if "Sign In" in auth_mode else "CREATE FREE ACCOUNT"
            submit = st.form_submit_button(btn_title)
            
            if submit:
                if not email or not password:
                    st.error("⚠️ Email aur Password dono fill karein.")
                elif len(password) < 6:
                    st.error("⚠️ Password minimum 6 characters ka hona chahiye.")
                else:
                    if "Sign Up" in auth_mode:
                        try:
                            res = supabase.auth.sign_up({"email": email.strip(), "password": password})
                            if res.user:
                                st.success("✅ Account ban gaya! Ab 'Existing Member (Sign In)' select karke login karein.")
                        except Exception as e:
                            st.error(f"Sign Up Failed: {str(e)}")
                    else:
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password})
                            if res.user:
                                st.session_state["user"] = res.user.email
                                st.rerun()
                        except Exception:
                            st.error("❌ Invalid Email or Password. Dobara check karein.")

    st.stop()  # Screener code tab tak band rahega jab tak login na ho

# ================= SCREENER APP (POST-LOGIN ACCESS) =================

MASTER_STOCKS = {
    "RELIANCE": "2885", "TCS": "11536", "HDFCBANK": "1333", "INFY": "1594",
    "ICICIBANK": "4963", "BHARTIARTL": "10604", "SBIN": "3045", "LT": "11483",
    "ITC": "1660", "TATAMOTORS": "3456", "AXISBANK": "5900", "KOTAKBANK": "1922",
    "TITAN": "3506", "BAJFINANCE": "317", "SUNPHARMA": "3351", "NTPC": "11630",
    "POWERGRID": "14977", "TATASTEEL": "3499", "COALINDIA": "20374", "VEDL": "3063",
    "HINDALCO": "1363", "BEL": "383", "HAL": "2303", "DLF": "14732", "TRENT": "1964",
    "ADANIENT": "25", "ADANIPORTS": "15083", "ASIANPAINT": "236", "BAJAJFINSV": "16675",
    "BPCL": "526", "BRITANNIA": "547", "CIPLA": "694", "DIVISLAB": "10940",
    "DRREDDY": "881", "EICHERMOT": "910", "GRASIM": "1232", "HCLTECH": "7229",
    "HEROMOTOCO": "1348", "HINDUNILVR": "1394", "INDUSINDBK": "5258", "JSWSTEEL": "11723",
    "MARUTI": "10999", "NESTLEIND": "17963", "ONGC": "2475", "SBILIFE": "21808",
    "TECHM": "13538", "ULTRACEMCO": "11532", "WIPRO": "3787", "ZOMATO": "5097",
    "JIOFIN": "18143", "IRFC": "160", "RVNL": "13745", "BHEL": "438", "PNB": "10666"
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
        if data['status']: return smart_api
        return None
    except Exception:
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
    return ranges.max(axis=1).rolling(period).mean()

def fetch_and_prepare_df(smart_api, token):
    to_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    from_date = (datetime.now() - timedelta(days=150)).strftime("%Y-%m-%d 09:15")
    res = smart_api.getCandleData({
        "exchange": "NSE", "symboltoken": token,
        "interval": "ONE_DAY", "fromdate": from_date, "todate": to_date
    })
    if not res.get('status') or not res.get('data'): return None
    df = pd.DataFrame(res['data'], columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    if len(df) < 35: return None
    df['Time'] = pd.to_datetime(df['Time'])
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Std'] = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Mid'] + (2 * df['BB_Std'])
    df['BB_Lower'] = df['BB_Mid'] - (2 * df['BB_Std'])
    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['ATR'] = calculate_atr(df, 14)
    return df

def render_chart(df, symbol, target_val, sl_val):
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.60, 0.20, 0.20],
        subplot_titles=[f"{symbol} Daily Matrix (EMA + Bollinger Bands)", "Volume Surge", "RSI (14) Momentum"]
    )
    fig.add_trace(go.Candlestick(x=df['Time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price", increasing_line_color='#00e699', decreasing_line_color='#ff3366'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA20'], line=dict(color='#ff9900', width=1.5), name="EMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA50'], line=dict(color='#00bfff', width=1.5), name="EMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Upper'], line=dict(color='#7d8b99', width=1, dash='dot'), name="Upper BB"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Lower'], line=dict(color='#7d8b99', width=1, dash='dot'), name="Lower BB"), row=1, col=1)
    if target_val and sl_val:
        fig.add_hline(y=target_val, line_dash="dash", line_color="#00e699", annotation_text=f" Target: ₹{target_val}", annotation_position="top right", row=1, col=1)
        fig.add_hline(y=sl_val, line_dash="dash", line_color="#ff3366", annotation_text=f" SL: ₹{sl_val}", annotation_position="bottom right", row=1, col=1)
    vol_colors = ['#00e699' if c >= o else '#ff3366' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df['Time'], y=df['Volume'], marker_color=vol_colors, name="Volume", opacity=0.8), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['Vol_SMA20'], line=dict(color='#ffbb33', width=1), name="Vol Avg 20"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['RSI'], line=dict(color='#9966ff', width=1.8), name="RSI"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ff3366", opacity=0.6, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00e699", opacity=0.6, row=3, col=1)
    fig.update_layout(paper_bgcolor='#080a0f', plot_bgcolor='#111622', xaxis_rangeslider_visible=False, height=660, dragmode='pan', margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#8b9bb4", size=10)), font=dict(family="Courier New, monospace", color="#8b9bb4"))
    fig.update_yaxes(gridcolor='#1e2638', fixedrange=False, row=1, col=1)
    fig.update_yaxes(gridcolor='#1e2638', fixedrange=False, row=2, col=1)
    fig.update_yaxes(gridcolor='#1e2638', fixedrange=True, range=[10, 90], row=3, col=1)
    fig.update_xaxes(gridcolor='#1e2638')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': False, 'displayModeBar': True})

# --- TOP STATUS BAR ---
c_title, c_badge = st.columns([3, 1])
with c_title:
    st.markdown("<h2 style='margin-bottom:0;'>⚡ SANDEEP KUMAR <span style='font-size:1rem;color:#00d2c4;'>PRO TERMINAL</span></h2>", unsafe_allow_html=True)
    st.caption(f"Authenticated as: {st.session_state['user']} • Angel One Live Exchange Engine")
with c_badge:
    st.markdown("<div style='text-align:right;padding-top:10px;'><span style='background:#102a27;color:#00e699;padding:4px 12px;border-radius:12px;font-size:0.75rem;border:1px solid #00e699;'>LIVE SYNC</span></div>", unsafe_allow_html=True)

# Sidebar with User Info & Logout
st.sidebar.markdown(f"**Member:** `{st.session_state['user']}`")
if st.sidebar.button("🚪 Log Out", use_container_width=True):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Risk Engine")
account_capital = st.sidebar.number_input("Portfolio Capital (₹)", value=100000, step=25000)
risk_per_trade_pct = st.sidebar.slider("Risk Per Trade (%)", min_value=0.5, max_value=3.0, value=1.5, step=0.25)
target_pct_choice = st.sidebar.slider("Target Return (%)", min_value=8, max_value=15, value=10, step=1)
min_score = st.sidebar.slider("Minimum Setup Score", min_value=50, max_value=85, value=60, step=5)

st.markdown("---")

# 🔍 SEARCH BAR SECTION
st.subheader("🔍 Instant Stock Search & Chart Inspector")
all_stock_names = sorted(list(MASTER_STOCKS.keys()))
col_search, col_btn = st.columns([3, 1])
with col_search:
    searched_stock = st.selectbox("Stock search karein (Jaise: RELIANCE, TATAMOTORS, ZOMATO):", all_stock_names)
with col_btn:
    st.write("")
    st.write("")
    search_clicked = st.button("📊 Open Chart", use_container_width=True)

if search_clicked or st.session_state.get("active_search") == searched_stock:
    st.session_state["active_search"] = searched_stock
    smart_api = get_angel_client()
    if smart_api:
        with st.spinner(f"Fetching technicals for {searched_stock}..."):
            token = MASTER_STOCKS[searched_stock]
            df_search = fetch_and_prepare_df(smart_api, token)
            if df_search is not None:
                cmp = float(df_search.iloc[-1]['Close'])
                atr = float(df_search.iloc[-1]['ATR']) if not pd.isna(df_search.iloc[-1]['ATR']) else (cmp * 0.02)
                tgt = round(cmp * (1 + (target_pct_choice / 100.0)), 2)
                sl = round(cmp - (1.5 * atr), 2)
                rsi = round(float(df_search.iloc[-1]['RSI']), 1)
                
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("CMP", f"₹{round(cmp, 2)}")
                m2.metric(f"Target +{target_pct_choice}%", f"₹{tgt}")
                m3.metric("ATR Stop-Loss", f"₹{sl}")
                m4.metric("RSI (14)", f"{rsi}")
                render_chart(df_search, searched_stock, tgt, sl)

st.markdown("---")

# 🚀 SCREENER SECTION
st.subheader("⚡ Automated Momentum Screener")
if st.button("🚀 Run Deep Screener on Watchlist", use_container_width=True):
    smart_api = get_angel_client()
    if not smart_api:
        st.error("Angel One session fail ho gaya. Secrets check karein.")
    else:
        with st.spinner("Screening high momentum setups..."):
            all_results = []
            candles_store = {}
            progress = st.progress(0)
            
            scan_universe = list(MASTER_STOCKS.items())[:25]
            for idx, (sym, token) in enumerate(scan_universe):
                progress.progress((idx + 1) / len(scan_universe))
                try:
                    df = fetch_and_prepare_df(smart_api, token)
                    if df is None: continue
                    last, prev = df.iloc[-1], df.iloc[-2]
                    cmp, ema20, ema50 = float(last['Close']), float(last['EMA20']), float(last['EMA50'])
                    rsi, vol, avg_vol = float(last['RSI']), float(last['Volume']), float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0
                    atr = float(last['ATR']) if not pd.isna(last['ATR']) else (cmp * 0.02)
                    
                    score = 0
                    if cmp > ema20 > ema50: score += 35
                    elif cmp > ema20: score += 20
                    if 50 <= rsi <= 70: score += 30
                    elif 45 <= rsi < 50: score += 15
                    vol_ratio = vol / avg_vol
                    if vol_ratio >= 1.2: score += 25
                    elif vol_ratio >= 1.0: score += 15
                    if cmp > float(prev['High']): score += 10
                    
                    if score >= min_score:
                        risk_amt = account_capital * (risk_per_trade_pct / 100.0)
                        stop_loss = round(cmp - (1.5 * atr), 2)
                        risk_per_share = cmp - stop_loss
                        qty = int(risk_amt // risk_per_share) if risk_per_share > 0 else 0
                        trade_capital = round(qty * cmp, 2)
                        target_price = round(cmp * (1 + (target_pct_choice / 100.0)), 2)
                        
                        candles_store[sym] = df
                        all_results.append({
                            "Symbol": sym, "Score": f"{score}%", "CMP (₹)": round(cmp, 2),
                            f"Target +{target_pct_choice}%": target_price, "Smart SL": stop_loss,
                            "RSI": round(rsi, 1), "Vol Ratio": f"{round(vol_ratio, 2)}x",
                            "Position Qty": qty, "Deploy Cap (₹)": trade_capital, "_score": score
                        })
                except Exception:
                    continue
            progress.empty()
            if all_results:
                all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
                for item in all_results: del item['_score']
                st.session_state["adv_results"] = all_results
                st.session_state["adv_candles"] = candles_store

if "adv_results" in st.session_state:
    data = st.session_state["adv_results"]
    if data:
        st.success(f"🎯 Total {len(data)} Stocks Filtered!")
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    
