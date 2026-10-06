import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyotp
from datetime import datetime, timedelta
from SmartApi import SmartConnect
from supabase import create_client, Client

# --- पेज सेटअप ---
st.set_page_config(
    page_title="Sandeep Kumar | Pro Terminal 2.0",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- स्टेट इनिशियलाइज़ेशन ---
if "user" not in st.session_state:
    st.session_state["user"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

@st.cache_resource
def init_supabase() -> Client:
    raw_url = st.secrets["SUPABASE_URL"].strip()
    base_url = raw_url.split("/auth")[0].split("/rest")[0].rstrip("/")
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(base_url, key)

supabase = init_supabase()

# ================= आधुनिक लॉगिन स्क्रीन =================
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

    _, col_auth, _ = st.columns([1, 1.1, 1])
    with col_auth:
        st.write("")
        st.write("")
        mode = st.session_state["auth_mode"]
        
        # पासवर्ड रीसेट
        if mode == "forgot":
            with st.form("forgot_form"):
                st.markdown("<h2 style='text-align:center; color:#fff;'>पासवर्ड रीसेट</h2>", unsafe_allow_html=True)
                reset_email = st.text_input("ईमेल", placeholder="email@domain.com")
                if st.form_submit_button("रीसेट लिंक भेजें", use_container_width=True):
                    try:
                        supabase.auth.reset_password_for_email(reset_email.strip())
                        st.success("पासवर्ड रीसेट लिंक आपके ईमेल पर भेज दिया गया है!")
                    except Exception as e:
                        st.error(str(e))
            if st.button("लॉगिन पर वापस जाएं", use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()
        
        # लॉगिन और रजिस्ट्रेशन
        else:
            is_login = mode == "login"
            with st.form("auth_form"):
                st.markdown(f"<h2 style='text-align:center; color:#fff;'>{'लॉगिन करें' if is_login else 'नया अकाउंट बनाएं'}</h2>", unsafe_allow_html=True)
                full_name = None if is_login else st.text_input("पूरा नाम", placeholder="राहुल शर्मा")
                email = st.text_input("ईमेल", placeholder="email@domain.com")
                password = st.text_input("पासवर्ड", type="password", placeholder="••••••••")
                
                if st.form_submit_button("आगे बढ़ें", use_container_width=True):
                    if not email or not password:
                        st.error("कृपया सभी डिटेल्स भरें।")
                    elif not is_login and not full_name:
                        st.error("कृपया अपना नाम दर्ज करें।")
                    else:
                        clean_email = f"{email}@terminal.com" if "@" not in email else email
                        if not is_login:
                            try:
                                res = supabase.auth.sign_up({"email": clean_email, "password": password, "options": {"data": {"full_name": full_name.strip()}}})
                                if res.user:
                                    st.success("अकाउंट बन गया! अब लॉगिन करें।")
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
                                st.error("गलत ईमेल या पासवर्ड। दोबारा जांचें।")
            
            if is_login:
                if st.button("नया अकाउंट बनाएं (Register)", use_container_width=True):
                    st.session_state["auth_mode"] = "register"
                    st.rerun()
                if st.button("पासवर्ड भूल गए?", use_container_width=True):
                    st.session_state["auth_mode"] = "forgot"
                    st.rerun()
            else:
                if st.button("पहले से अकाउंट है? लॉगिन करें", use_container_width=True):
                    st.session_state["auth_mode"] = "login"
                    st.rerun()
    st.stop()

# ================= डैशबोर्ड डार्क टर्मिनल स्टाइल =================
st.markdown("""
<style>
    /* डार्क टर्मिनल बेस */
    .stApp {
        background-color: #0b0f17 !important;
        color: #f1f5f9 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    /* साइडबार स्टाइल */
    section[data-testid="stSidebar"] {
        background: #080c14 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    /* मॉडर्न ग्लास कार्ड्स */
    .metric-card {
        background: rgba(18, 24, 38, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .metric-card .label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; }
    .metric-card .val { font-size: 1.45rem; font-weight: 700; color: #f8fafc; font-family: 'JetBrains Mono', monospace; }
    .metric-card .sub { font-size: 0.75rem; color: #38bdf8; margin-top: 2px; }

    /* बटन डिज़ाइन */
    .stButton > button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton > button:hover {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
    }
    
    /* डेटाफ्रेम डिज़ाइन */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        overflow: hidden;
    }
</style>
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
        subplot_titles=["", "वॉल्यूम ट्रेंड", "RSI (14) मोमेंटम"]
    )
    # कैंडलस्टिक
    fig.add_trace(go.Candlestick(
        x=df['Time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="प्राइस", increasing_line_color='#10b981', decreasing_line_color='#ef4444'
    ), row=1, col=1)
    
    # EMAs और बोलिंजर बैंड्स
    fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA20'], line=dict(color='#f59e0b', width=1.5), name="EMA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA50'], line=dict(color='#38bdf8', width=1.5), name="EMA 50"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Upper'], line=dict(color='rgba(148, 163, 184, 0.4)', width=1, dash='dot'), name="Upper Band"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['BB_Lower'], line=dict(color='rgba(148, 163, 184, 0.4)', width=1, dash='dot'), name="Lower Band"), row=1, col=1)
    
    if target_val and sl_val:
        fig.add_hline(y=target_val, line_dash="dash", line_color="#10b981", annotation_text=f" Target ₹{target_val}", row=1, col=1)
        fig.add_hline(y=sl_val, line_dash="dash", line_color="#ef4444", annotation_text=f" Stop Loss ₹{sl_val}", row=1, col=1)
        
    # वॉल्यूम
    v_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df['Time'], y=df['Volume'], marker_color=v_colors, opacity=0.7, name="वॉल्यूम"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Time'], y=df['Vol_SMA20'], line=dict(color='#fbbf24', width=1), name="वॉल्यूम SMA 20"), row=2, col=1)
    
    # RSI इंडिकेटर
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

# --- हेडर बार ---
col_head, col_status = st.columns([3, 1])
display_user = st.session_state.get('user_name', 'Trader')
with col_head:
    st.markdown(f"""
    <div style='display:flex; align-items:center; gap:12px;'>
        <h2 style='margin:0; font-size:1.8rem; font-weight:800;'>⚡ PRO TERMINAL <span style='color:#38bdf8; font-size:0.9rem; border:1px solid #0284c7; padding:2px 8px; border-radius:6px;'>v2.0</span></h2>
    </div>
    <p style='color:#64748b; margin:2px 0 0 0; font-size:0.85rem;'>लाइव मार्केट फीड सक्रिय • सदस्य: <span style='color:#94a3b8;'>{display_user}</span></p>
    """, unsafe_allow_html=True)

with col_status:
    st.markdown("""
    <div style='text-align:right; margin-top:8px;'>
        <span style='background:rgba(16, 185, 129, 0.15); color:#10b981; border:1px solid rgba(16, 185, 129, 0.3); padding:6px 14px; border-radius:20px; font-size:0.75rem; font-weight:600;'>
            ● LIVE ANGEL ONE
        </span>
    </div>
    """, unsafe_allow_html=True)

# --- साइडबार सेटिंग्स ---
st.sidebar.markdown(f"**अकाउंट:** `{display_user}`")
if st.sidebar.button("लॉग आउट (Log Out)", use_container_width=True):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.session_state["user_name"] = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("#### ⚙️ रिस्क मैनेजमेंट इंजन")
account_capital = st.sidebar.number_input("कुल कैपिटल (₹)", value=100000, step=10000)
risk_per_trade_pct = st.sidebar.slider("प्रति ट्रेड रिस्क (%)", min_value=0.5, max_value=3.0, value=1.5, step=0.25)
target_pct_choice = st.sidebar.slider("टारगेट रिटर्न (%)", min_value=5, max_value=25, value=10, step=1)
min_score = st.sidebar.slider("न्यूनतम मोमेंटम स्कोर", min_value=40, max_value=85, value=60, step=5)

st.write("")

# --- दो मुख्य टैब्स ---
tab_screener, tab_search = st.tabs(["🚀 ऑटोमेटेड स्क्रीनर", "🔍 डीप स्टॉक चार्ट"])

with tab_search:
    c_s1, c_s2 = st.columns([3, 1])
    with c_s1:
        searched_stock = st.selectbox("स्टॉक चुनें", sorted(list(MASTER_STOCKS.keys())), label_visibility="collapsed")
    with c_s2:
        btn_search = st.button("चार्ट और मैट्रिक्स देखें", use_container_width=True)

    if btn_search or st.session_state.get("active_search") == searched_stock:
        st.session_state["active_search"] = searched_stock
        api = get_angel_client()
        if api:
            with st.spinner("टेक्निकल डेटा लोड हो रहा है..."):
                df_search = fetch_and_prepare_df(api, MASTER_STOCKS[searched_stock])
                if df_search is not None:
                    cmp = float(df_search.iloc[-1]['Close'])
                    atr = float(df_search.iloc[-1]['ATR']) if not pd.isna(df_search.iloc[-1]['ATR']) else (cmp * 0.02)
                    tgt = round(cmp * (1 + (target_pct_choice / 100.0)), 2)
                    sl = round(cmp - (1.5 * atr), 2)
                    rsi = round(float(df_search.iloc[-1]['RSI']), 1)
                    
                    # मॉडर्न कार्ड्स
                    k1, k2, k3, k4 = st.columns(4)
                    k1.markdown(f"<div class='metric-card'><div class='label'>करंट प्राइस (CMP)</div><div class='val'>₹{cmp:,.2f}</div><div class='sub'>लाइव मार्केट रेट</div></div>", unsafe_allow_html=True)
                    k2.markdown(f"<div class='metric-card'><div class='label'>टारगेट (+{target_pct_choice}%)</div><div class='val' style='color:#10b981;'>₹{tgt:,.2f}</div><div class='sub'>पोटेंशियल गेन</div></div>", unsafe_allow_html=True)
                    k3.markdown(f"<div class='metric-card'><div class='label'>ATR स्टॉप लॉस</div><div class='val' style='color:#ef4444;'>₹{sl:,.2f}</div><div class='sub'>ट्रेलिंग रिस्क लेवल</div></div>", unsafe_allow_html=True)
                    k4.markdown(f"<div class='metric-card'><div class='label'>RSI (14 दिन)</div><div class='val' style='color:#a855f7;'>{rsi}</div><div class='sub'>{'बुलिश मोमेंटम' if 50 <= rsi <= 70 else 'न्यूट्रल/एक्स्ट्रीम'}</div></div>", unsafe_allow_html=True)
                    
                    st.write("")
                    render_chart(df_search, searched_stock, tgt, sl)

with tab_screener:
    if st.button("⚡ हाई मोमेंटम स्टॉक्स स्कैन करें", use_container_width=True):
        api = get_angel_client()
        if not api:
            st.error("Angel One लॉगिन फ़ेल हुआ। API क्रेडेंशियल्स की जांच करें।")
        else:
            with st.spinner("EMA, RSI, वॉल्यूम और ब्रेकआउट्स स्कैन किए जा रहे हैं..."):
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
                                "Symbol": sym,
                                "Setup Score": score,
                                "CMP (₹)": round(cmp, 2),
                                f"Target (+{target_pct_choice}%)": target_price,
                                "Stop Loss": stop_loss,
                                "RSI": round(rsi, 1),
                                "Volume Surge": f"{round(vol_ratio, 1)}x",
                                "Recommended Qty": qty,
                                "Capital Required": trade_capital,
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
        st.markdown(f"#### 🎯 चुने गए स्टॉक्स ({len(results)})")
        
        # मॉडर्न प्रोग्रेस बार टेबल
        st.dataframe(
            pd.DataFrame(results),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Setup Score": st.column_config.ProgressColumn("Confidence Score", format="%d%%", min_value=0, max_value=100),
                "CMP (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                "Capital Required": st.column_config.NumberColumn(format="₹%d")
            }
        )
