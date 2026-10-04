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

# User Session State
if "user" not in st.session_state:
    st.session_state["user"] = None

# Custom High-Contrast & Glassmorphic CSS
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    /* Streamlit Chrome & Headers Hide */
    #MainMenu, header, footer {visibility: hidden !important; display: none !important;}
    [data-testid="stToolbar"], [data-testid="stHeader"] {display: none !important;}
    [data-testid="manage-app-button"], .stAppDeployButton {display: none !important; visibility: hidden !important;}
    div[class*="viewerBadge"], iframe[title="Manage app"], div[data-testid="stStatusWidget"] {display: none !important;}

    /* Global Dark Theme */
    .stApp { 
        background-color: #080a0f; 
        color: #f1f5f9; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
    }
    section[data-testid="stSidebar"] { background-color: #0f131c; border-right: 1px solid #1e2638; }

    /* ================= LOGIN THEME (GLASSMORPHISM) ================= */
    .login-wrapper {
        min-height: 82vh;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        background: radial-gradient(circle at 50% 12%, rgba(220, 240, 255, 0.45) 0%, rgba(25, 118, 210, 0.6) 28%, rgba(13, 27, 62, 0.95) 75%, #070e1e 100%),
                    linear-gradient(180deg, #1976d2 0%, #0c2340 55%, #050d1a 100%);
        border-radius: 28px;
        padding: 50px 20px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
        animation: fadeIn 0.8s ease-in-out;
    }

    /* Ambient Moon / Glowing Orb */
    .login-wrapper::before {
        content: "";
        position: absolute;
        top: 28px;
        left: 50%;
        transform: translateX(-50%);
        width: 110px;
        height: 110px;
        background: radial-gradient(circle, #ffffff 30%, rgba(255, 255, 255, 0.8) 60%, rgba(255, 255, 255, 0) 100%);
        border-radius: 50%;
        filter: blur(1px);
        box-shadow: 0 0 45px rgba(255, 255, 255, 0.85);
        z-index: 1;
        pointer-events: none;
        animation: pulseMoon 4s ease-in-out infinite alternate;
    }

    @keyframes pulseMoon {
        0% { transform: translateX(-50%) scale(0.96); opacity: 0.9; }
        100% { transform: translateX(-50%) scale(1.04); opacity: 1; filter: blur(0.5px); }
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Glassmorphism Card Overlay */
    div[data-testid="stForm"] {
        position: relative;
        z-index: 2;
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 24px !important;
        padding: 35px 32px !important;
        box-shadow: 0 20px 45px rgba(0, 0, 0, 0.45) !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }

    div[data-testid="stForm"]:hover {
        border-color: rgba(255, 255, 255, 0.35) !important;
        box-shadow: 0 25px 55px rgba(0, 114, 255, 0.25) !important;
    }

    /* Pill-Shaped Inputs */
    .stTextInput div[data-baseweb="input"] {
        background-color: rgba(255, 255, 255, 0.16) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 30px !important;
        color: #ffffff !important;
        padding-left: 10px;
        transition: all 0.3s ease !important;
    }

    .stTextInput div[data-baseweb="input"]:focus-within {
        background-color: rgba(255, 255, 255, 0.24) !important;
        border-color: #2196f3 !important;
        box-shadow: 0 0 15px rgba(33, 150, 243, 0.45) !important;
    }

    .stTextInput input {
        color: #ffffff !important;
        font-size: 0.95rem !important;
    }

    .stTextInput input::placeholder {
        color: rgba(255, 255, 255, 0.65) !important;
    }

    /* Pill Blue Gradient Button */
    .stButton > button {
        background: linear-gradient(135deg, #1e88e5 0%, #00b0ff 100%) !important;
        color: #ffffff !important;
        border: none !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        border-radius: 30px !important;
        width: 100% !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 6px 20px rgba(0, 176, 255, 0.35) !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(0, 176, 255, 0.6) !important;
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

# ================= AUTHENTICATION GATEWAY =================
if st.session_state["user"] is None:
    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)
    
    _, col_auth, _ = st.columns([1, 1.25, 1])
    with col_auth:
        st.markdown("""
        <div style='text-align: center; margin-bottom: 22px; position: relative; z-index: 2;'>
            <h1 style='font-size: 2.3rem; font-weight: 800; color: #ffffff; margin-bottom: 4px; letter-spacing: 0.5px;'>Login</h1>
            <p style='color: rgba(255, 255, 255, 0.75); font-size: 0.85rem; margin: 0;'>Institutional Quantitative Screener</p>
        </div>
        """, unsafe_allow_html=True)
        
        auth_mode = st.radio("Access Level", ["Existing Member (Sign In)", "New Member (Sign Up)"], horizontal=True, label_visibility="collapsed")
        
        with st.form("auth_form"):
            email = st.text_input("Username / Email", placeholder="👤  Username or email@address.com")
            password = st.text_input("Password", type="password", placeholder="🔒  ••••••••••••")
            
            st.markdown("""
            <div style='display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: rgba(255, 255, 255, 0.85); margin: 6px 2px 18px 2px;'>
                <span><i class="fa-solid fa-square-check" style="color: #00b0ff; margin-right: 4px;"></i> Remember me</span>
                <span style='color: rgba(255, 255, 255, 0.85); cursor: pointer;'>Forgot Password</span>
            </div>
            """, unsafe_allow_html=True)
            
            btn_title = "Login" if "Sign In" in auth_mode else "Register"
            submit = st.form_submit_button(btn_title)
            
            st.markdown("""
            <div style='text-align: center; margin-top: 14px; font-size: 0.85rem; color: rgba(255, 255, 255, 0.8);'>
                Don't have an account? <span style='color: #ffffff; font-weight: 600;'>Register</span>
            </div>
            """, unsafe_allow_html=True)
            
            if submit:
                if not email or not password:
                    st.error("⚠️ Email aur Password dono fill karein.")
                elif len(password) < 6:
                    st.error("⚠️ Password minimum 6 characters ka hona chahiye.")
                else:
                    clean_email = email.replace("👤", "").strip()
                    if "Sign Up" in auth_mode:
                        try:
                            res = supabase.auth.sign_up({"email": clean_email, "password": password})
                            if res.user:
                                st.success("✅ Account ban gaya! Ab Sign In select karke login karein.")
                        except Exception as e:
                            st.error(f"Sign Up Failed: {str(e)}")
                    else:
                        try:
                            res = supabase.auth.sign_in_with_password({"email": clean_email, "password": password})
                            if res.user:
                                st.session_state["user"] = res.user.email
                                st.rerun()
                        except Exception:
                            st.error("❌ Invalid Email or Password. Dobara check karein.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

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

# Sidebar
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
                    if df is None: 
                        continue
                    last, prev = df.iloc[-1], df.iloc[-2]
                    cmp, ema20, ema50 = float(last['Close']), float(last['EMA20']), float(last['EMA50'])
                    rsi = float(last['RSI'])
                    vol = float(last['Volume'])
                    avg_vol = float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0
                    atr = float(last['ATR']) if not pd.isna(last['ATR']) else (cmp * 0.02)
                    
                    score = 0
                    if cmp > ema20 > ema50: 
                        score += 35
                    elif cmp > ema20: 
                        score += 20
                    
                    if 50 <= rsi <= 70: 
                        score += 30
                    elif 45 <= rsi < 50: 
                        score += 15
                    
                 
