import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyotp
import feedparser
from datetime import datetime, timedelta
from SmartApi import SmartConnect
from supabase import create_client, Client

# --- Page Setup ---
st.set_page_config(
    page_title="Sandeep Kumar | Pro Terminal 2.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- State Initialization ---
if "user" not in st.session_state:
    st.session_state["user"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"
if "lang" not in st.session_state:
    st.session_state["lang"] = "English"

# --- Translations Dictionary ---
T = {
    "English": {
        "news_badge": "🔴 LIVE NEWS",
        "terminal_title": "PRO TERMINAL",
        "live_feed": "Live Data Feed Active",
        "member": "Authenticated Member",
        "live_badge": "● LIVE ANGEL ONE",
        "risk_engine": "Risk Configuration",
        "portfolio_cap": "Portfolio Capital (₹)",
        "risk_per_trade": "Risk Per Trade (%)",
        "target_return": "Profit Target (%)",
        "min_score": "Min Momentum Threshold",
        "logout": "🚪 Log Out",
        "tab_screener": "🚀 Automated Scanner",
        "tab_search": "🔍 Deep Stock Inspector",
        "select_asset": "Select Asset to Inspect",
        "gen_matrix": "📊 Generate Matrix",
        "scan_btn": "⚡ Scan Momentum Setups Across Universe",
        "cmp": "Current Price (CMP)",
        "target": "Target",
        "sl": "ATR Stop Loss",
        "rsi": "RSI (14 Day)",
        "scanning": "Filtering momentum setups across watchlist...",
        "fetching": "Fetching technical metrics...",
        "filtered_title": "🎯 Screened Candidates",
        "col_symbol": "Symbol",
        "col_score": "Confidence Score",
        "col_cmp": "CMP (₹)",
        "col_target": "Target",
        "col_sl": "Stop Loss",
        "col_rsi": "RSI",
        "col_vol": "Volume Surge",
        "col_qty": "Position Qty",
        "col_cap": "Required Capital (₹)",
        "login": "Login",
        "register": "Register",
        "welcome_back": "Welcome Back",
        "create_acc": "Create Account",
        "full_name": "Full Name",
        "email": "Email",
        "password": "Password",
        "continue": "Continue",
        "forgot_pwd": "Forgot Password?",
        "reset_access": "Reset Access",
        "send_reset": "Send Reset Link",
        "back_login": "⬅️ Back to Login",
        "new_here": "Don't have an account? Register",
        "already_acc": "Already have an account? Login",
        "vol_chart": "VOLUME PROFILE",
        "rsi_chart": "RSI (14) MOMENTUM",
        "price_chart": "PRICE"
    },
    "Hindi": {
        "news_badge": "🔴 ताज़ा खबरें",
        "terminal_title": "प्रो टर्मिनल",
        "live_feed": "लाइव मार्केट फीड सक्रिय",
        "member": "सक्रिय सदस्य",
        "live_badge": "● लाइव एंजल वन",
        "risk_engine": "रिस्क मैनेजमेंट इंजन",
        "portfolio_cap": "कुल कैपिटल (₹)",
        "risk_per_trade": "प्रति ट्रेड रिस्क (%)",
        "target_return": "टारगेट रिटर्न (%)",
        "min_score": "न्यूनतम मोमेंटम स्कोर",
        "logout": "🚪 लॉग आउट",
        "tab_screener": "🚀 ऑटोमेटेड स्क्रीनर",
        "tab_search": "🔍 डीप स्टॉक चार्ट",
        "select_asset": "स्टॉक चुनें",
        "gen_matrix": "📊 चार्ट और मैट्रिक्स देखें",
        "scan_btn": "⚡ हाई मोमेंटम स्टॉक्स स्कैन करें",
        "cmp": "करंट प्राइस (CMP)",
        "target": "टारगेट",
        "sl": "ATR स्टॉप लॉस",
        "rsi": "RSI (14 दिन)",
        "scanning": "EMA, RSI और वॉल्यूम ब्रेकआउट्स स्कैन हो रहे हैं...",
        "fetching": "टेक्निकल डेटा लोड हो रहा है...",
        "filtered_title": "🎯 चुने गए स्टॉक्स",
        "col_symbol": "स्टॉक",
        "col_score": "मोमेंटम स्कोर",
        "col_cmp": "CMP (₹)",
        "col_target": "टारगेट",
        "col_sl": "स्टॉप लॉस",
        "col_rsi": "RSI",
        "col_vol": "वॉल्यूम उछाल",
        "col_qty": "शेयर संख्या (Qty)",
        "col_cap": "जरूरी कैपिटल (₹)",
        "login": "लॉगिन करें",
        "register": "रजिस्टर करें",
        "welcome_back": "वापसी पर स्वागत है",
        "create_acc": "नया अकाउंट बनाएं",
        "full_name": "पूरा नाम",
        "email": "ईमेल",
        "password": "पासवर्ड",
        "continue": "आगे बढ़ें",
        "forgot_pwd": "पासवर्ड भूल गए?",
        "reset_access": "पासवर्ड रीसेट",
        "send_reset": "रीसेट लिंक भेजें",
        "back_login": "⬅️ लॉगिन पर वापस जाएं",
        "new_here": "नया अकाउंट बनाएं (Register)",
        "already_acc": "पहले से अकाउंट है? लॉगिन करें",
        "vol_chart": "वॉल्यूम ट्रेंड",
        "rsi_chart": "RSI (14) मोमेंटम",
        "price_chart": "प्राइस"
    }
}

txt = T[st.session_state["lang"]]

# --- Cache News Fetch (Updates every 2.5 minutes) ---
@st.cache_data(ttl=150)
def fetch_moneycontrol_news():
    try:
        url = "https://www.moneycontrol.com/rss/latestnews.xml"
        feed = feedparser.parse(url)
        news_items = []
        for entry in feed.entries[:12]:
            clean_title = entry.title.replace('"', '&quot;').replace("'", "&#39;")
            news_items.append({
                "title": clean_title,
                "link": entry.link
            })
        return news_items
    except Exception:
        return []

@st.cache_resource
def init_supabase() -> Client:
    raw_url = st.secrets["SUPABASE_URL"].strip()
    base_url = raw_url.split("/auth")[0].split("/rest")[0].rstrip("/")
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(base_url, key)

supabase = init_supabase()

# ================= LOGIN SCREEN =================
if st.session_state["user"] is None:
    st.markdown("""
    <style>
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] { display: none !important; }
        .stApp {
            background: radial-gradient(circle at 50% 20%, rgba(14, 165, 233, 0.15) 0%, rgba(8, 10, 15, 0.95) 70%), #07090e !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }
        div[data-testid="stForm"] {
            background: rgba(17, 24, 39, 0.7) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 20px !important;
            padding: 35px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6) !important;
        }
        .stTextInput div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.04) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 12px !important;
            height: 48px;
        }
        .stTextInput input { color: #f8fafc !important; }
        div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 12px !important;
            height: 48px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    _, col_lang = st.columns([4, 1])
    with col_lang:
        chosen_lang = st.selectbox("🌐 Language", ["English", "Hindi"], index=0 if st.session_state["lang"] == "English" else 1)
        if chosen_lang != st.session_state["lang"]:
            st.session_state["lang"] = chosen_lang
            st.rerun()

    _, col_auth, _ = st.columns([1, 1.1, 1])
    with col_auth:
        mode = st.session_state["auth_mode"]
        if mode == "forgot":
            with st.form("forgot_form"):
                st.markdown(f"<h2 style='text-align:center; color:#fff;'>{txt['reset_access']}</h2>", unsafe_allow_html=True)
                reset_email = st.text_input(txt["email"], placeholder="email@domain.com")
                if st.form_submit_button(txt["send_reset"], use_container_width=True):
                    try:
                        supabase.auth.reset_password_for_email(reset_email.strip())
                        st.success("Reset link sent!")
                    except Exception as e:
                        st.error(str(e))
            if st.button(txt["back_login"], use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()
        else:
            is_login = mode == "login"
            with st.form("auth_form"):
                st.markdown(f"<h2 style='text-align:center; color:#fff;'>{txt['welcome_back'] if is_login else txt['create_acc']}</h2>", unsafe_allow_html=True)
                full_name = None if is_login else st.text_input(txt["full_name"], placeholder="Rahul Sharma")
                email = st.text_input(txt["email"], placeholder="email@domain.com")
                password = st.text_input(txt["password"], type="password", placeholder="••••••••")
                if st.form_submit_button(txt["continue"], use_container_width=True):
                    if not email or not password:
                        st.error("Fields cannot be empty.")
                    elif not is_login and not full_name:
                        st.error("Name required.")
                    else:
                        clean_email = f"{email}@terminal.com" if "@" not in email else email
                        if not is_login:
                            try:
                                res = supabase.auth.sign_up({"email": clean_email, "password": password, "options": {"data": {"full_name": full_name.strip()}}})
                                if res.user:
                                    st.success("Account created! Please log in.")
                                    st.session_state["auth_mode"] = "login"
                            except Exception as e:
                                st.error(str(e))
                        else:
                            try:
                                res = supabase.auth.sign_in_with_password({"email": clean_email, "password": password})
                                if res.user:
                                    st.session_state["user"] = res.user.email
                                    meta = res.user.user_metadata or {}
                                    st.session_state["user_name"] = meta.get("full_name", res.user.email.split("@")[0].title())
                                    st.rerun()
                            except Exception:
                                st.error("Invalid credentials.")
            if is_login:
                if st.button(txt["new_here"], use_container_width=True):
                    st.session_state["auth_mode"] = "register"
                    st.rerun()
                if st.button(txt["forgot_pwd"], use_container_width=True):
                    st.session_state["auth_mode"] = "forgot"
                    st.rerun()
            else:
                if st.button(txt["already_acc"], use_container_width=True):
                    st.session_state["auth_mode"] = "login"
                    st.rerun()
    st.stop()

# ================= DASHBOARD UI & TICKER STYLING =================
st.markdown("""
<style>
    .stApp { background-color: #0b0f17 !important; color: #f1f5f9 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; }
    section[data-testid="stSidebar"] { background: #080c14 !important; border-right: 1px solid rgba(255, 255, 255, 0.06) !important; }
    
    /* Live Stock Ticker Bar on Top */
    .news-ticker-container {
        display: flex;
        align-items: center;
        background: #0f172a;
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 8px;
        overflow: hidden;
        height: 42px;
        margin-bottom: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.35);
    }
    .news-badge {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
        color: #ffffff;
        font-weight: 800;
        font-size: 0.72rem;
        letter-spacing: 0.05em;
        padding: 0 16px;
        height: 100%;
        display: flex;
        align-items: center;
        white-space: nowrap;
        z-index: 5;
        box-shadow: 3px 0 10px rgba(0, 0, 0, 0.5);
    }
    .ticker-scroll-wrap {
        overflow: hidden;
        white-space: nowrap;
        width: 100%;
    }
    .ticker-track {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 35s linear infinite;
    }
    .ticker-track:hover {
        animation-play-state: paused;
    }
    .ticker-item {
        display: inline-block;
        color: #cbd5e1;
        font-size: 0.85rem;
        margin-right: 40px;
        text-decoration: none;
        transition: color 0.2s;
    }
    .ticker-item:hover {
        color: #38bdf8 !important;
        text-decoration: underline !important;
    }
    .ticker-bullet {
        color: #f59e0b;
        margin-right: 8px;
    }
    @keyframes marquee {
        0% { transform: translate3d(0, 0, 0); }
        100% { transform: translate3d(-100%, 0, 0); }
    }

    /* Cards & Components */
    .metric-card {
        background: rgba(18, 24, 38, 0.75); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px;
        padding: 16px 20px; backdrop-filter: blur(10px); box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .metric-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; }
    .metric-card .val { font-size: 1.45rem; font-weight: 700; color: #f8fafc; font-family: 'JetBrains Mono', monospace; }
    .metric-card .sub { font-size: 0.75rem; color: #38bdf8; margin-top: 2px; }
    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important; color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 10px !important; font-weight: 600 !important;
    }
    .stButton > button:hover { border-color: #38bdf8 !important; box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important; }
    div[data-testid="stDataFrame"] { border: 1px solid rgba(255, 255, 255, 0.08) !important; border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ================= TOP MONEYCONTROL LIVE NEWS TICKER =================
news_feed = fetch_moneycontrol_news()
if news_feed:
    ticker_html_items = "".join([
        f'<a href="{item["link"]}" target="_blank" class="ticker-item"><span class="ticker-bullet">⚡</span>{item["title"]}</a>'
        for item in news_feed
    ])
    st.markdown(f"""
    <div class="news-ticker-container">
        <div class="news-badge">{txt['news_badge']}</div>
        <div class="ticker-scroll-wrap">
            <div class="ticker-track">
                {ticker_html_items}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

MASTER_STOCKS = {
    "RELIANCE": "2885", "TCS": "11536", "HDFCBANK": "1333", "INFY": "1594",
    "ICICIBANK": "4963", "BHARTIARTL": "10604", "SBIN": "3045", "LT": "11483",
    "ITC": "1660", "TATAMOTORS": "3456", "AXISBANK": "5900", "KOTAKBANK": "1922",
    "TITAN": "3506", "BAJFINANCE": "317", "SUNPHARMA": "3351", "NTPC": "11630",
    "POWERGRID": "14977", "TATASTEEL": "3499", "COALINDIA": "20374", "VEDL": "3063",
    "HINDALCO": "1363", "BEL": "383", "HAL": "2303", "DLF": "14732", "TRENT": "1964",
    "ADANIENT": "25", "ADANIPORTS": "15083", "ASIANPAINT": "236", "BAJAJFINSV": "16675",
    "ZOMATO": "5097", "JIOFIN": "18143", "IRFC": "160", "RVNL": "13745", "BHEL": "438"
}

def get_angel_client():
    try:
        smart_api = SmartConnect(api_key=st.secrets["ANGEL_API_KEY"])
        totp = pyotp.TOTP(st.secrets["ANGEL_TOTP_KEY"]).now()
        data = smart_api.generateSession(st.secrets["ANGEL_CLIENT_CODE"], st.secrets["ANGEL_PIN"], totp)
        return smart_api if data.get('status') else None
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
    from_date = (datetime.now() - timedelta(days=160)).strftime("%Y-%m-%d 09:15")
    res = smart_api.getCandleData({
        "exchange": "NSE", "symboltoken": token,
        "interval": "ONE_DAY", "fromdate": from_date, "todate": to_date
    })
    if not res.get('status') or not res.get('data'):
        return None
    df = pd.DataFrame(res['data'], columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    if len(df) < 35:
        return None
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
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.62, 0.18, 0.20],
        subplot_titles=["", txt["vol_chart"], txt["rsi_chart"]]
    )
    fig.add_trace(go.Candlestick(
        x=df['Time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name=txt["price_chart"], increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA20'], line=dict(color='#f59e0b', width=1.5), name="EMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA50'], line=dict(color='#38bdf8', width=1.5), name="EMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Upper'], line=dict(color='rgba(148, 163, 184, 0.4)', width=1, dash='dot'), name="Upper Band"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Lower'], line=dict(color='rgba(148, 163, 184, 0.4)', width=1, dash='dot'), name="Lower Band"), row=1, col=1)
    
    if target_val and sl_val:
        fig.add_hline(y=target_val, line_dash="dash", line_color="#10b981", annotation_text=f" {txt['target']} ₹{target_val}", row=1, col=1)
        fig.add_hline(y=sl_val, line_dash="dash", line_color="#ef4444", annotation_text=f" {txt['sl']} ₹{sl_val}", row=1, col=1)
        
    v_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df['Time'], y=df['Volume'], marker_color=v_colors, opacity=0.7, name="Volume"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['Vol_SMA20'], line=dict(color='#fbbf24', width=1), name="Vol MA"), row=2, col=1)
    
    fig.add_trace(go.Scatter(x=df['Time'], y=df['RSI'], line=dict(color='#a855f7', width=1.7), name="RSI"), row=3, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="#38bdf8", opacity=0.05, line_width=0, row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#10b981", row=3, col=1)
    
    fig.update_layout(
        paper_bgcolor='#0b0f17', plot_bgcolor='#0e1422',
        xaxis_rangeslider_visible=False, height=650, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#94a3b8", size=10)),
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8")
    )
    fig.update_xaxes(gridcolor='#1e293b')
    fig.update_yaxes(gridcolor='#1e293b')
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

# --- NAVIGATION HEADER ---
col_head, col_status = st.columns([3, 1])
display_user = st.session_state.get('user_name', 'Trader')
with col_head:
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:12px;'>
        <h2 style='margin:0; font-size:1.8rem; font-weight:800;'>⚡ SANDEEP KUMAR <span style='color:#38bdf8; font-size:0.9rem; border:1px solid #0284c7; padding:2px 8px; border-radius:6px;'>{txt['terminal_title']}</span></h2>
    </div>
    <p style='color:#64748b; margin:2px 0 0 0; font-size:0.85rem;'>{txt['live_feed']} • {txt['member']}: <span style='color:#94a3b8;'>{display_user}</span></p>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown(f"""
    <div style='text-align:right; margin-top:8px;'>
        <span style='background:rgba(16, 185, 129, 0.15); color:#10b981; border:1px solid rgba(16, 185, 129, 0.3); padding:6px 14px; border-radius:20px; font-size:0.75rem; font-weight:600;'>
            {txt['live_badge']}
        </span>
    </div>
    """, unsafe_allow_html=True)

# --- SIDEBAR (Language Toggle & Risk Config) ---
st.sidebar.markdown(f"**{txt['member']}:** `{display_user}`")

selected_lang = st.sidebar.selectbox("🌐 Language / भाषा", ["English", "Hindi"], index=0 if st.session_state["lang"] == "English" else 1)
if selected_lang != st.session_state["lang"]:
    st.session_state["lang"] = selected_lang
    st.rerun()

if st.sidebar.button(txt["logout"], use_container_width=True):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.session_state["user_name"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown(f"#### ⚙️ {txt['risk_engine']}")
account_capital = st.sidebar.number_input(txt["portfolio_cap"], value=100000, step=10000)
risk_per_trade_pct = st.sidebar.slider(txt["risk_per_trade"], min_value=0.5, max_value=3.0, value=1.5, step=0.25)
target_pct_choice = st.sidebar.slider(txt["target_return"], min_value=5, max_value=25, value=10, step=1)
min_score = st.sidebar.slider(txt["min_score"], min_value=40, max_value=85, value=60, step=5)

st.write("")

# --- TABS ---
tab_screener, tab_search = st.tabs([txt["tab_screener"], txt["tab_search"]])

with tab_search:
    c_s1, c_s2 = st.columns([3, 1])
    with c_s1:
        searched_stock = st.selectbox(txt["select_asset"], sorted(list(MASTER_STOCKS.keys())), label_visibility="collapsed")
    with c_s2:
        btn_search = st.button(txt["gen_matrix"], use_container_width=True)

    if btn_search or st.session_state.get("active_search") == searched_stock:
        st.session_state["active_search"] = searched_stock
        api = get_angel_client()
        if api:
            with st.spinner(txt["fetching"]):
                df_search = fetch_and_prepare_df(api, MASTER_STOCKS[searched_stock])
                if df_search is not None:
                    cmp = float(df_search.iloc[-1]['Close'])
                    atr = float(df_search.iloc[-1]['ATR']) if not pd.isna(df_search.iloc[-1]['ATR']) else (cmp * 0.02)
                    tgt = round(cmp * (1 + (target_pct_choice / 100.0)), 2)
                    sl = round(cmp - (1.5 * atr), 2)
                    rsi = round(float(df_search.iloc[-1]['RSI']), 1)
                    
                    k1, k2, k3, k4 = st.columns(4)
                    k1.markdown(f"<div class='metric-card'><div class='label'>{txt['cmp']}</div><div class='val'>₹{cmp:,.2f}</div><div class='sub'>Live NSE Price</div></div>", unsafe_allow_html=True)
                    k2.markdown(f"<div class='metric-card'><div class='label'>{txt['target']} (+{target_pct_choice}%)</div><div class='val' style='color:#10b981;'>₹{tgt:,.2f}</div><div class='sub'>Upside Target</div></div>", unsafe_allow_html=True)
                    k3.markdown(f"<div class='metric-card'><div class='label'>{txt['sl']}</div><div class='val' style='color:#ef4444;'>₹{sl:,.2f}</div><div class='sub'>Trailing Protection</div></div>", unsafe_allow_html=True)
                    k4.markdown(f"<div class='metric-card'><div class='label'>{txt['rsi']}</div><div class='val' style='color:#a855f7;'>{rsi}</div><div class='sub'>{'Bullish' if 50 <= rsi <= 70 else 'Neutral/Extreme'}</div></div>", unsafe_allow_html=True)
                    
                    st.write("")
                    render_chart(df_search, searched_stock, tgt, sl)

with tab_screener:
    if st.button(txt["scan_btn"], use_container_width=True):
        api = get_angel_client()
        if not api:
            st.error("Authentication to Angel One API failed. Recheck credentials.")
        else:
            with st.spinner(txt["scanning"]):
                all_results = []
                candles_store = {}
                progress_bar = st.progress(0)
                scan_universe = list(MASTER_STOCKS.items())[:25]
                
                for idx, (sym, token) in enumerate(scan_universe):
                    progress_bar.progress((idx + 1) / len(scan_universe))
                    try:
                        df = fetch_and_prepare_df(api, token)
                        if df is None:
                            continue
                        last, prev = df.iloc[-1], df.iloc[-2]
                        cmp, ema20, ema50 = float(last['Close']), float(last['EMA20']), float(last['EMA50'])
                        rsi = float(last['RSI'])
                        vol = float(last['Volume'])
                        avg_vol = float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0
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
                                txt["col_symbol"]: sym,
                                txt["col_score"]: score,
                                txt["col_cmp"]: round(cmp, 2),
                                f"{txt['col_target']} (+{target_pct_choice}%)": target_price,
                                txt["col_sl"]: stop_loss,
                                txt["col_rsi"]: round(rsi, 1),
                                txt["col_vol"]: f"{round(vol_ratio, 1)}x",
                                txt["col_qty"]: qty,
                                txt["col_cap"]: trade_capital,
                                "_score": score
                            })
                    except Exception:
                        continue

                progress_bar.empty()
                if all_results:
                    all_results = sorted(all_results, key=lambda x: x['_score'], reverse=True)
                    for item in all_results:
                        del item['_score']
                    st.session_state["adv_results"] = all_results
                    st.session_state["adv_candles"] = candles_store

    if "adv_results" in st.session_state and st.session_state["adv_results"]:
        results = st.session_state["adv_results"]
        st.markdown(f"#### {txt['filtered_title']} ({len(results)})")
        
        st.dataframe(
            pd.DataFrame(results),
            use_container_width=True,
            hide_index=True,
            column_config={
                txt["col_score"]: st.column_config.ProgressColumn(txt["col_score"], format="%d%%", min_value=0, max_value=100),
                txt["col_cmp"]: st.column_config.NumberColumn(format="₹%.2f"),
                txt["col_cap"]: st.column_config.NumberColumn(format="₹%d")
            }
        )
