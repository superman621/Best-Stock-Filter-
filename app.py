import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyotp, feedparser
from datetime import datetime, timedelta
from SmartApi import SmartConnect
from supabase import create_client, Client

# --- पेज सेटअप व स्टेट ---
st.set_page_config(page_title="AlphaX | Momentum Terminal", page_icon="⚡", layout="wide")
defaults = {"user": None, "user_name": None, "auth_mode": "login", "lang": "English", "theme_mode": "Dark"}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# --- भाषा डिक्शनरी ---
T = {
    "English": {
        "news_badge": "🔴 LIVE NEWS", "terminal_title": "MOMENTUM TERMINAL", "live_feed": "Live Data Feed Active",
        "member": "Authenticated Member", "live_badge": "● LIVE ANGEL ONE", "risk_engine": "Risk Configuration",
        "portfolio_cap": "Portfolio Capital (₹)", "risk_per_trade": "Risk Per Trade (%)", "target_return": "Profit Target (%)",
        "min_score": "Min Momentum Threshold", "logout": "🚪 Log Out", "tab_screener": "🚀 Automated Scanner",
        "tab_search": "🔍 Deep Stock Inspector", "select_asset": "Search Stock / Index (e.g. NIFTY 50, TATA, RELIANCE)", 
        "gen_matrix": "📊 Generate Matrix", "scan_btn": "⚡ Scan Momentum Setups Across Universe", 
        "cmp": "Current Price (CMP)", "target": "Target", "sl": "ATR Stop Loss", "rsi": "RSI (14 Day)", 
        "scanning": "Filtering momentum setups across watchlist...", "fetching": "Fetching technical metrics...", 
        "filtered_title": "🎯 Screened Candidates", "col_symbol": "Symbol", "col_score": "Confidence Score", 
        "col_cmp": "CMP (₹)", "col_target": "Target", "col_sl": "Stop Loss", "col_rsi": "RSI", "col_vol": "Volume Surge", 
        "col_qty": "Position Qty", "col_cap": "Required Capital (₹)", "login": "Login", "register": "Register", 
        "welcome_back": "Welcome Back", "create_acc": "Create Account", "full_name": "Full Name", "email": "Email", 
        "password": "Password", "continue": "Continue", "forgot_pwd": "Forgot Password?", "reset_access": "Reset Access", 
        "send_reset": "Send Reset Link", "back_login": "⬅️ Back to Login", "new_here": "Don't have an account? Register", 
        "already_acc": "Already have an account? Login", "vol_chart": "VOLUME PROFILE", "rsi_chart": "RSI (14) MOMENTUM", 
        "price_chart": "PRICE", "theme_label": "🎨 Theme Mode"
    },
    "Hindi": {
        "news_badge": "🔴 ताज़ा खबरें", "terminal_title": "मोमेंटम टर्मिनल", "live_feed": "लाइव मार्केट फीड सक्रिय",
        "member": "सक्रिय सदस्य", "live_badge": "● लाइव एंजल वन", "risk_engine": "रिस्क मैनेजमेंट इंजन",
        "portfolio_cap": "कुल कैपिटल (₹)", "risk_per_trade": "प्रति ट्रेड रिस्क (%)", "target_return": "टारगेट रिटर्न (%)",
        "min_score": "न्यूनतम मोमेंटम स्कोर", "logout": "🚪 लॉग आउट", "tab_screener": "🚀 ऑटोमेटेड स्क्रीनर",
        "tab_search": "🔍 डीप स्टॉक चार्ट", "select_asset": "स्टॉक या इंडेक्स खोजें (उदा. NIFTY 50, TATA)", 
        "gen_matrix": "📊 चार्ट और मैट्रिक्स देखें", "scan_btn": "⚡ हाई मोमेंटम स्टॉक्स स्कैन करें", 
        "cmp": "करंट प्राइस (CMP)", "target": "टारगेट", "sl": "ATR स्टॉप लॉस", "rsi": "RSI (14 दिन)", 
        "scanning": "EMA, RSI और वॉल्यूम ब्रेकआउट्स स्कैन हो रहे हैं...", "fetching": "टेक्निकल डेटा लोड हो रहा है...", 
        "filtered_title": "🎯 चुने गए स्टॉक्स", "col_symbol": "स्टॉक", "col_score": "मोमेंटम स्कोर", 
        "col_cmp": "CMP (₹)", "col_target": "टारगेट", "col_sl": "स्टॉप लॉस", "col_rsi": "RSI", "col_vol": "वॉल्यूम उछाल", 
        "col_qty": "शेयर संख्या (Qty)", "col_cap": "जरूरी कैपिटल (₹)", "login": "लॉगिन करें", "register": "रजिस्टर करें", 
        "welcome_back": "वापसी पर स्वागत है", "create_acc": "नया अकाउंट बनाएं", "full_name": "पूरा नाम", "email": "ईमेल", 
        "password": "पासवर्ड", "continue": "आगे बढ़ें", "forgot_pwd": "पासवर्ड भूल गए?", "reset_access": "पासवर्ड रीसेट", 
        "send_reset": "रीसेट लिंक भेजें", "back_login": "⬅️ लॉगिन पर वापस जाएं", "new_here": "नया अकाउंट बनाएं (Register)", 
        "already_acc": "पहले से अकाउंट है? लॉगिन करें", "vol_chart": "वॉल्यूम ट्रेंड", "rsi_chart": "RSI (14) मोमेंटम", 
        "price_chart": "प्राइस", "theme_label": "🎨 थीम मोड"
    }
}
txt = T[st.session_state["lang"]]
is_light = (st.session_state["theme_mode"] == "Light")

# --- टाइमफ्रेम मैपिंग ---
INTERVAL_MAP = {
    "5m":  ("FIVE_MINUTE", 5),
    "15m": ("FIFTEEN_MINUTE", 15),
    "1h":  ("ONE_HOUR", 60),
    "1D":  ("ONE_DAY", 180)
}

# --- मनीकंट्रोल न्यूज़ ---
@st.cache_data(ttl=120)
def fetch_moneycontrol_news():
    try:
        feed = feedparser.parse("https://www.moneycontrol.com/rss/latestnews.xml")
        return [{"title": e.title.replace('"', '&quot;').replace("'", "&#39;"), "link": e.link} for e in feed.entries[:15]]
    except Exception: return []

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"].strip().split("/auth")[0].split("/rest")[0].rstrip("/"), st.secrets["SUPABASE_KEY"].strip())

supabase = init_supabase()

# --- सभी NSE स्टॉक्स और NIFTY 50 मास्टर डेटा फ़ेच (24h Cache) ---
@st.cache_data(ttl=86400)
def load_all_nse_instruments():
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        res = requests.get(url, timeout=10)
        data = res.json()
        stocks = {}
        # Nifty 50 इंडेक्स सबसे पहले जोड़ें
        stocks["NIFTY 50 (INDEX)"] = {"token": "99926000", "exch": "NSE"}
        stocks["BANKNIFTY (INDEX)"] = {"token": "99926009", "exch": "NSE"}
        
        for item in data:
            # केवल NSE Equity (NSE-EQ) उठाएं
            if item.get("exch_seg") == "NSE" and item.get("symbol", "").endswith("-EQ"):
                sym = item["symbol"].replace("-EQ", "")
                stocks[f"{sym} | {item.get('name', '')[:20]}"] = {
                    "token": item.get("token"),
                    "symbol": sym,
                    "exch": "NSE"
                }
        return stocks
    except Exception:
        # बैकअप लिस्ट यदि नेटवर्क इशू हो
        return {
            "NIFTY 50 (INDEX)": {"token": "99926000", "exch": "NSE"},
            "RELIANCE": {"token": "2885", "exch": "NSE"},
            "TCS": {"token": "11536", "exch": "NSE"},
            "HDFCBANK": {"token": "1333", "exch": "NSE"},
            "INFY": {"token": "1594", "exch": "NSE"}
        }

ALL_INSTRUMENTS = load_all_nse_instruments()
# ================= ऑथेंटिकेशन स्क्रीन =================
if st.session_state["user"] is None:
    st.markdown("""<style>
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] { display: none !important; }
        .stApp { background: radial-gradient(circle at 50% 20%, rgba(14,165,233,0.15) 0%, rgba(8,10,15,0.95) 70%), #07090e !important; }
        div[data-testid="stForm"] { background: rgba(17,24,39,0.75)!important; backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; padding: 35px; }
        .stTextInput input { color: #f8fafc !important; }
        div[data-testid="stFormSubmitButton"] > button { background: linear-gradient(135deg, #0ea5e9, #2563eb) !important; color:#fff !important; border-radius:12px; height:48px; }
    </style>""", unsafe_allow_html=True)
    
    _, col_l = st.columns([4, 1])
    with col_l:
        l = st.selectbox("🌐 Language", ["English", "Hindi"], index=0 if st.session_state["lang"] == "English" else 1)
        if l != st.session_state["lang"]: st.session_state["lang"] = l; st.rerun()

    _, col_auth, _ = st.columns([1, 1.1, 1])
    with col_auth:
        mode = st.session_state["auth_mode"]
        if mode == "forgot":
            with st.form("forgot_form"):
                st.markdown(f"<h2 style='text-align:center;color:#fff;'>{txt['reset_access']}</h2>", unsafe_allow_html=True)
                reset_email = st.text_input(txt["email"], placeholder="email@domain.com")
                if st.form_submit_button(txt["send_reset"], use_container_width=True):
                    try: supabase.auth.reset_password_for_email(reset_email.strip()); st.success("Reset link sent!")
                    except Exception as e: st.error(str(e))
            if st.button(txt["back_login"], use_container_width=True): st.session_state["auth_mode"] = "login"; st.rerun()
        else:
            is_login = (mode == "login")
            with st.form("auth_form"):
                st.markdown(f"<h2 style='text-align:center;color:#fff;'>{txt['welcome_back'] if is_login else txt['create_acc']}</h2>", unsafe_allow_html=True)
                full_name = None if is_login else st.text_input(txt["full_name"], placeholder="Rahul Sharma")
                email = st.text_input(txt["email"], placeholder="email@domain.com")
                pwd = st.text_input(txt["password"], type="password", placeholder="••••••••")
                if st.form_submit_button(txt["continue"], use_container_width=True):
                    if not email or not pwd: st.error("Fields cannot be empty.")
                    elif not is_login and not full_name: st.error("Name required.")
                    else:
                        clean_email = f"{email}@terminal.com" if "@" not in email else email
                        try:
                            if not is_login:
                                if supabase.auth.sign_up({"email": clean_email, "password": pwd, "options": {"data": {"full_name": full_name.strip()}}}).user:
                                    st.success("Account created! Please log in."); st.session_state["auth_mode"] = "login"
                            else:
                                res = supabase.auth.sign_in_with_password({"email": clean_email, "password": pwd})
                                if res.user:
                                    st.session_state["user"] = res.user.email
                                    st.session_state["user_name"] = (res.user.user_metadata or {}).get("full_name", res.user.email.split("@")[0].title())
                                    st.rerun()
                        except Exception as e: st.error("Authentication error: " + str(e))
            btn_t = txt["new_here"] if is_login else txt["already_acc"]
            if st.button(btn_t, use_container_width=True):
                st.session_state["auth_mode"] = "register" if is_login else "login"; st.rerun()
            if is_login and st.button(txt["forgot_pwd"], use_container_width=True):
                st.session_state["auth_mode"] = "forgot"; st.rerun()
    st.stop()
# ================= यूनिफाइड CSS (CSS Variables) =================
theme_vars = """
    --bg: #f7f9fa; --fg: #111827; --card-bg: #fff; --border: #e2e8f0; --primary: #0066cc;
    --side-bg: #fff; --news-bg: #dbeafe; --news-text: #0066cc; --bullet: #0066cc;
""" if is_light else """
    --bg: #0b0f17; --fg: #f1f5f9; --card-bg: rgba(18,24,38,0.75); --border: rgba(255,255,255,0.08);
    --primary: #38bdf8; --side-bg: #080c14; --news-bg: linear-gradient(135deg, #ef4444, #b91c1c); --news-text: #fff; --bullet: #f59e0b;
"""
st.markdown(f"""<style>
    :root {{ {theme_vars} }}
    .stApp {{ background-color: var(--bg) !important; color: var(--fg) !important; }}
    section[data-testid="stSidebar"] {{ background-color: var(--side-bg) !important; border-right: 1px solid var(--border) !important; }}
    .news-ticker-container {{ display: flex; align-items: center; background: var(--card-bg); border: 1px solid var(--border); border-radius: 8px; height: 42px; margin-bottom: 16px; overflow: hidden; }}
    .news-badge {{ background: var(--news-bg); color: var(--news-text); font-weight: 800; font-size: 0.75rem; padding: 0 14px; height: 100%; display: flex; align-items: center; white-space: nowrap; }}
    .ticker-scroll-wrap {{ overflow: hidden; white-space: nowrap; width: 100%; }}
    .ticker-track {{ display: inline-block; padding-left: 100%; animation: marquee 35s linear infinite; }}
    .ticker-track:hover {{ animation-play-state: paused; }}
    .ticker-item {{ color: var(--fg) !important; font-size: 0.85rem; margin-right: 35px; text-decoration: none; font-weight: 600; }}
    .ticker-item:hover {{ color: var(--primary) !important; text-decoration: underline !important; }}
    .ticker-bullet {{ color: var(--bullet); margin-right: 6px; }}
    .metric-card {{ background: var(--card-bg); border: 1px solid var(--border); border-top: 3px solid var(--primary); border-radius: 8px; padding: 14px 18px; }}
    .metric-card .label {{ font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #64748b; }}
    .metric-card .val {{ font-size: 1.4rem; font-weight: 800; margin: 4px 0; }}
    .metric-card .sub {{ font-size: 0.72rem; color: var(--primary); font-weight: 600; }}
    .stButton > button {{ background: var(--primary) !important; color: #fff !important; border: none !important; border-radius: 6px !important; font-weight: 700 !important; }}
    @keyframes marquee {{ 0% {{ transform: translate3d(0, 0, 0); }} 100% {{ transform: translate3d(-100%, 0, 0); }} }}
</style>""", unsafe_allow_html=True)

# Ticker UI
news_feed = fetch_moneycontrol_news()
if news_feed:
    items = "".join([f'<a href="{i["link"]}" target="_blank" class="ticker-item"><span class="ticker-bullet">⚡</span>{i["title"]}</a>' for i in news_feed])
    st.markdown(f'<div class="news-ticker-container"><div class="news-badge">{txt["news_badge"]}</div><div class="ticker-scroll-wrap"><div class="ticker-track">{items}</div></div></div>', unsafe_allow_html=True)

def get_angel_client():
    try:
        api = SmartConnect(api_key=st.secrets["ANGEL_API_KEY"])
        return api if api.generateSession(st.secrets["ANGEL_CLIENT_CODE"], st.secrets["ANGEL_PIN"], pyotp.TOTP(st.secrets["ANGEL_TOTP_KEY"]).now()).get('status') else None
    except Exception: return None

def fetch_and_prepare_df(api, token, tf="1D"):
    interval_code, days_back = INTERVAL_MAP.get(tf, ("ONE_DAY", 180))
    to_d = datetime.now().strftime("%Y-%m-%d %H:%M")
    from_d = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d 09:15")
    
    res = api.getCandleData({"exchange": "NSE", "symboltoken": str(token), "interval": interval_code, "fromdate": from_d, "todate": to_d})
    if not res.get('status') or not res.get('data') or len(res['data']) < 25: return None
    df = pd.DataFrame(res['data'], columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Time'] = pd.to_datetime(df['Time'])
    
    # इंडिकेटर्स
    df['EMA20'], df['EMA50'] = df['Close'].ewm(span=20, adjust=False).mean(), df['Close'].ewm(span=50, adjust=False).mean()
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Upper'], df['BB_Lower'] = df['BB_Mid'] + 2*df['Close'].rolling(20).std(), df['BB_Mid'] - 2*df['Close'].rolling(20).std()
    df['Vol_SMA20'] = df['Volume'].rolling(20).mean()
    
    # RSI & ATR
    d = df['Close'].diff()
    rs = (d.clip(lower=0)).rolling(14).mean() / ((-d.clip(upper=0)).rolling(14).mean().replace(0, 0.0001))
    df['RSI'] = 100 - (100 / (1 + rs))
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - df['Close'].shift()).abs(), (df['Low'] - df['Close'].shift()).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # MACD
    ema12, ema26 = df['Close'].ewm(span=12, adjust=False).mean(), df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    return df

def render_chart(df, symbol, target_val, sl_val, active_inds, tf="1D"):
    show_vol = "Volume" in active_inds
    show_rsi = "RSI" in active_inds
    show_macd = "MACD" in active_inds
    
    rows = 1 + int(show_vol) + int(show_rsi) + int(show_macd)
    heights = [0.55] + [0.45 / (rows - 1)] * (rows - 1) if rows > 1 else [1.0]
    titles = [""]
    if show_vol: titles.append(txt["vol_chart"])
    if show_rsi: titles.append(txt["rsi_chart"])
    if show_macd: titles.append("MACD")

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=heights, subplot_titles=titles)
    fig.add_trace(go.Candlestick(x=df['Time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=txt["price_chart"], increasing_line_color='#10b981', decreasing_line_color='#ef4444'), 1, 1)
    
    if "EMA 20" in active_inds: fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA20'], line=dict(color='#f59e0b', width=1.5), name="EMA 20"), 1, 1)
    if "EMA 50" in active_inds: fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA50'], line=dict(color='#0284c7' if is_light else '#38bdf8', width=1.5), name="EMA 50"), 1, 1)
    if "Bollinger Bands" in active_inds:
        fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Upper'], line=dict(color='rgba(148,163,184,0.4)', width=1, dash='dot'), name="BB Upper"), 1, 1)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Lower'], line=dict(color='rgba(148,163,184,0.4)', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(148,163,184,0.05)', name="BB Lower"), 1, 1)
        
    if target_val and sl_val:
        cmp = float(df.iloc[-1]['Close'])
        fig.add_hrect(y0=cmp, y1=target_val, fillcolor="rgba(16, 185, 129, 0.08)", line_width=0, row=1, col=1)
        fig.add_hrect(y0=sl_val, y1=cmp, fillcolor="rgba(239, 68, 68, 0.08)", line_width=0, row=1, col=1)
        fig.add_hline(y=target_val, line_dash="dash", line_color="#10b981", annotation_text=f" TGT ₹{target_val}", row=1, col=1)
        fig.add_hline(y=sl_val, line_dash="dash", line_color="#ef4444", annotation_text=f" SL ₹{sl_val}", row=1, col=1)
        
    curr_r = 2
    if show_vol:
        v_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df['Time'], y=df['Volume'], marker_color=v_colors, opacity=0.75, name="Volume"), curr_r, 1)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Vol_SMA20'], line=dict(color='#fbbf24', width=1.2), name="Vol MA"), curr_r, 1)
        curr_r += 1
        
    if show_rsi:
        fig.add_trace(go.Scatter(x=df['Time'], y=df['RSI'], line=dict(color='#a855f7', width=1.6), name="RSI"), curr_r, 1)
        fig.add_hrect(y0=30, y1=70, fillcolor="#0284c7" if is_light else "#38bdf8", opacity=0.08, line_width=0, row=curr_r, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=curr_r, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#10b981", row=curr_r, col=1)
        curr_r += 1

    if show_macd:
        h_colors = ['#10b981' if h >= 0 else '#ef4444' for h in df['MACD_Hist']]
        fig.add_trace(go.Bar(x=df['Time'], y=df['MACD_Hist'], marker_color=h_colors, opacity=0.6, name="Hist"), curr_r, 1)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['MACD'], line=dict(color='#0284c7' if is_light else '#38bdf8', width=1.3), name="MACD"), curr_r, 1)
        fig.add_trace(go.Scatter(x=df['Time'], y=df['Signal'], line=dict(color='#f59e0b', width=1.3), name="Signal"), curr_r, 1)

    fig.update_layout(
        paper_bgcolor="#ffffff" if is_light else "#0b0f17", plot_bgcolor="#f8fafc" if is_light else "#0e1422",
        dragmode=False, xaxis_rangeslider_visible=False, height=680, margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(color="#334155" if is_light else "#94a3b8", size=10)),
        font=dict(family="Arial, sans-serif" if is_light else "JetBrains Mono, monospace", color="#334155" if is_light else "#94a3b8"),
        newshape=dict(line=dict(color="#38bdf8", width=2))
    )
    
    fig.update_xaxes(gridcolor="#e2e8f0" if is_light else "#1e293b", fixedrange=True)
    fig.update_yaxes(gridcolor="#e2e8f0" if is_light else "#1e293b", fixedrange=True)
    
    if tf in ["5m", "15m", "1h"]:
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"]), dict(bounds=[15.5, 9.25], pattern="hour")])

    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': True,
        'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawrect', 'eraseshape'],
        'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
        'scrollZoom': False, 'doubleClick': False
    })
# --- हेडर ---
display_user = st.session_state.get('user_name', 'Trader')
col_head, col_status = st.columns([3, 1])
with col_head:
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:10px;'>
        <h2 style='margin:0; font-size:1.85rem; font-weight:900; letter-spacing:-0.5px;'>
            ⚡ ALPHA<span style='color:{"#0066cc" if is_light else "#38bdf8"};'>X</span> 
            <span style='color:{"#0066cc" if is_light else "#38bdf8"}; font-size:0.85rem; border:1px solid {"#0066cc" if is_light else "#0284c7"}; padding:2px 10px; border-radius:6px; vertical-align:middle; margin-left:6px;'>
                {txt['terminal_title']}
            </span>
        </h2>
    </div>
    <p style='color:{"#64748b" if is_light else "#94a3b8"}; margin:4px 0 0 0; font-size:0.85rem;'>
        {txt['live_feed']} • {txt['member']}: <span style='font-weight:600;'>{display_user}</span>
    </p>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown(f"<div style='text-align:right; margin-top:8px;'><span style='background:rgba(16,185,129,0.15);color:#10b981;border:1px solid #10b981;padding:4px 12px;border-radius:15px;font-size:0.75rem;font-weight:700;'>{txt['live_badge']}</span></div>", unsafe_allow_html=True)

# --- साइडबार ---
st.sidebar.markdown(f"**{txt['member']}:** `{display_user}`")
selected_theme = st.sidebar.selectbox(txt["theme_label"], ["Light", "Dark"], index=0 if is_light else 1)
selected_lang = st.sidebar.selectbox("🌐 Language", ["English", "Hindi"], index=0 if st.session_state["lang"] == "English" else 1)
if selected_theme != st.session_state["theme_mode"] or selected_lang != st.session_state["lang"]:
    st.session_state["theme_mode"], st.session_state["lang"] = selected_theme, selected_lang
    st.rerun()

if st.sidebar.button(txt["logout"], use_container_width=True):
    supabase.auth.sign_out()
    st.session_state["user"], st.session_state["user_name"] = None, None
    st.rerun()

st.sidebar.markdown(f"---\n#### ⚙️ {txt['risk_engine']}")
account_capital = st.sidebar.number_input(txt["portfolio_cap"], value=100000, step=10000)
risk_per_trade_pct = st.sidebar.slider(txt["risk_per_trade"], 0.5, 3.0, 1.5, 0.25)
target_pct_choice = st.sidebar.slider(txt["target_return"], 5, 25, 10, 1)
min_score = st.sidebar.slider(txt["min_score"], 40, 85, 60, 5)

# --- टैब्स ---
tab_screener, tab_search = st.tabs([txt["tab_screener"], txt["tab_search"]])

with tab_search:
    c_s1, c_s2 = st.columns([3, 1])
    # भारतीय बाज़ार के सभी 2000+ स्टॉक्स और NIFTY 50 सर्च
    searched_stock = c_s1.selectbox(
        txt["select_asset"], 
        options=list(ALL_INSTRUMENTS.keys()), 
        index=0, 
        label_visibility="collapsed"
    )
    btn_search = c_s2.button(txt["gen_matrix"], use_container_width=True)

    if btn_search or st.session_state.get("active_search") == searched_stock:
        st.session_state["active_search"] = searched_stock
        
        c_tf, c_ind = st.columns([1.5, 2.5])
        with c_tf:
            selected_tf = st.radio("Timeframe", ["5m", "15m", "1h", "1D"], index=3, horizontal=True, label_visibility="collapsed")
        with c_ind:
            selected_inds = st.multiselect("Indicators", ["EMA 20", "EMA 50", "Bollinger Bands", "Volume", "RSI", "MACD"], default=["EMA 20", "EMA 50", "Volume", "RSI"], label_visibility="collapsed")

        api = get_angel_client()
        if api:
            stock_info = ALL_INSTRUMENTS[searched_stock]
            token = stock_info["token"]
            
            with st.spinner(f"Loading {selected_tf} chart for {searched_stock}..."):
                df_search = fetch_and_prepare_df(api, token, tf=selected_tf)
                if df_search is not None:
                    cmp = float(df_search.iloc[-1]['Close'])
                    atr = float(df_search.iloc[-1]['ATR']) if pd.notna(df_search.iloc[-1]['ATR']) else (cmp * 0.02)
                    tgt, sl, rsi = round(cmp * (1 + target_pct_choice/100), 2), round(cmp - 1.5 * atr, 2), round(float(df_search.iloc[-1]['RSI']), 1)
                    
                    cols = st.columns(4)
                    card_data = [
                        (txt['cmp'], f"₹{cmp:,.2f}", f"Live {selected_tf} Price", ""),
                        (f"{txt['target']} (+{target_pct_choice}%)", f"₹{tgt:,.2f}", "Upside Target", "color:#10b981;"),
                        (txt['sl'], f"₹{sl:,.2f}", "Trailing Protection", "color:#ef4444;"),
                        (txt['rsi'], f"{rsi}", "Bullish" if 50 <= rsi <= 70 else "Neutral/Extreme", "color:#7c3aed;")
                    ]
                    for col, (l, v, s, sty) in zip(cols, card_data):
                        col.markdown(f"<div class='metric-card'><div class='label'>{l}</div><div class='val' style='{sty}'>{v}</div><div class='sub'>{s}</div></div>", unsafe_allow_html=True)
                    
                    st.write("")
                    render_chart(df_search, searched_stock, tgt, sl, selected_inds, tf=selected_tf)
                else:
                    st.warning(f"Could not load data for {searched_stock}. Market might be closed or token inactive.")

with tab_screener:
    if st.button(txt["scan_btn"], use_container_width=True):
        api = get_angel_client()
        if not api: st.error("Angel One Authentication Failed.")
        else:
            with st.spinner(txt["scanning"]):
                all_results, p_bar = [], st.progress(0)
                # स्क्रीनर के लिए टॉप लिक्विड स्टॉक्स (Nifty 50 स्टॉक्स)
                scan_universe = [k for k in ALL_INSTRUMENTS.keys() if "INDEX" not in k][:30]
                
                for idx, sym_label in enumerate(scan_universe):
                    p_bar.progress((idx + 1) / len(scan_universe))
                    try:
                        token = ALL_INSTRUMENTS[sym_label]["token"]
                        df = fetch_and_prepare_df(api, token, tf="1D")
                        if df is None: continue
                        last, prev = df.iloc[-1], df.iloc[-2]
                        cmp, ema20, ema50, rsi = float(last['Close']), float(last['EMA20']), float(last['EMA50']), float(last['RSI'])
                        vol_ratio = float(last['Volume']) / (float(last['Vol_SMA20']) if last['Vol_SMA20'] > 0 else 1.0)
                        
                        score = (35 if cmp > ema20 > ema50 else 20 if cmp > ema20 else 0) + \
                                (30 if 50 <= rsi <= 70 else 15 if 45 <= rsi < 50 else 0) + \
                                (25 if vol_ratio >= 1.2 else 15 if vol_ratio >= 1.0 else 0) + \
                                (10 if cmp > float(prev['High']) else 0)
                        
                        if score >= min_score:
                            atr = float(last['ATR']) if pd.notna(last['ATR']) else (cmp * 0.02)
                            sl = round(cmp - 1.5 * atr, 2)
                            qty = int((account_capital * (risk_per_trade_pct / 100)) // (cmp - sl)) if (cmp - sl) > 0 else 0
                            clean_sym = sym_label.split(" | ")[0]
                            all_results.append({
                                txt["col_symbol"]: clean_sym, txt["col_score"]: score, txt["col_cmp"]: round(cmp, 2),
                                f"{txt['col_target']} (+{target_pct_choice}%)": round(cmp * (1 + target_pct_choice/100), 2),
                                txt["col_sl"]: sl, txt["col_rsi"]: round(rsi, 1), txt["col_vol"]: f"{round(vol_ratio, 1)}x",
                                txt["col_qty"]: qty, txt["col_cap"]: round(qty * cmp, 2), "_score": score
                            })
                    except Exception: continue
                p_bar.empty()
                if all_results:
                    all_results.sort(key=lambda x: x.pop('_score'), reverse=True)
                    st.session_state["adv_results"] = all_results

    if st.session_state.get("adv_results"):
        res = st.session_state["adv_results"]
        st.markdown(f"#### {txt['filtered_title']} ({len(res)})")
        st.dataframe(pd.DataFrame(res), use_container_width=True, hide_index=True,
                     column_config={
                         txt["col_score"]: st.column_config.ProgressColumn(txt["col_score"], format="%d%%", min_value=0, max_value=100),
                         txt["col_cmp"]: st.column_config.NumberColumn(format="₹%.2f"),
                         txt["col_cap"]: st.column_config.NumberColumn(format="₹%d")
                     })
