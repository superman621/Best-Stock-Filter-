import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pyotp
from datetime import datetime, timedelta
from SmartApi import SmartConnect
from supabase import create_client, Client

# Page Setup - Phone me sidebar shuru me band rahegi
st.set_page_config(
    page_title="Sandeep Kumar | Pro Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# State initialization
if "user" not in st.session_state:
    st.session_state["user"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "login"

# Supabase Auth Client Init (Auto-Fix for trailing path / invalid URL)
@st.cache_resource
def init_supabase() -> Client:
    raw_url = st.secrets["SUPABASE_URL"].strip()
    base_url = raw_url.split("/auth")[0].split("/rest")[0].rstrip("/")
    key = st.secrets["SUPABASE_KEY"].strip()
    return create_client(base_url, key)

supabase = init_supabase()

# ================= LOGIN SCREEN THEME =================
if st.session_state["user"] is None:
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        #MainMenu, header, footer, [data-testid="stToolbar"], [data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
        }

        .stApp {
            background: radial-gradient(circle at 50% 16%, rgba(255, 255, 255, 0.95) 0%, rgba(144, 202, 249, 0.45) 12%, rgba(25, 118, 210, 0.6) 28%, rgba(13, 37, 72, 0.95) 65%, #07111e 100%),
                        linear-gradient(180deg, #1e88e5 0%, #0d2847 45%, #050d1a 100%) !important;
            min-height: 100vh;
        }

        .stApp::before {
            content: "";
            position: fixed;
            top: 35px;
            left: 50%;
            transform: translateX(-50%);
            width: 105px;
            height: 105px;
            background: radial-gradient(circle, #ffffff 40%, rgba(255, 255, 255, 0.8) 65%, rgba(255, 255, 255, 0) 100%);
            border-radius: 50%;
            box-shadow: 0 0 50px rgba(255, 255, 255, 0.85);
            pointer-events: none;
            z-index: 0;
        }

        div[data-testid="stForm"] {
            position: relative;
            z-index: 10;
            background: rgba(255, 255, 255, 0.12) !important;
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            border: 1px solid rgba(255, 255, 255, 0.28) !important;
            border-radius: 28px !important;
            padding: 38px 30px 25px 30px !important;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45) !important;
            margin-top: 40px;
        }

        .stTextInput div[data-baseweb="input"] {
            background-color: rgba(255, 255, 255, 0.45) !important;
            border: 1.5px solid rgba(255, 255, 255, 0.8) !important;
            border-radius: 35px !important;
            height: 50px;
            padding-left: 10px;
            transition: all 0.3s ease !important;
        }

        .stTextInput div[data-baseweb="input"]:focus-within {
            background-color: #ffffff !important;
            border-color: #00b0ff !important;
            box-shadow: 0 0 16px rgba(0, 176, 255, 0.7) !important;
        }

        .stTextInput input {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
        }

        .stTextInput input::placeholder {
            color: #475569 !important;
            -webkit-text-fill-color: #475569 !important;
            font-weight: 500 !important;
        }

        div[data-testid="stForm"] div[data-testid="stFormSubmitButton"] {
            display: flex !important;
            justify-content: center !important;
            width: 100% !important;
        }

        div[data-testid="stForm"] .stButton > button {
            background: linear-gradient(135deg, #1e88e5 0%, #00b0ff 100%) !important;
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            border: none !important;
            height: 48px !important;
            font-weight: 700 !important;
            font-size: 1.05rem !important;
            border-radius: 35px !important;
            width: 100% !important;
            box-shadow: 0 6px 20px rgba(0, 176, 255, 0.45) !important;
            transition: all 0.3s ease !important;
        }

        div[data-testid="stForm"] .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 25px rgba(0, 176, 255, 0.7) !important;
        }

        div[data-testid="stVerticalBlock"] > div.stButton > button {
            background: transparent !important;
            border: none !important;
            color: rgba(255, 255, 255, 0.9) !important;
            box-shadow: none !important;
            font-size: 0.9rem !important;
            margin-top: 4px;
        }
        div[data-testid="stVerticalBlock"] > div.stButton > button:hover {
            color: #ffffff !important;
            text-decoration: underline !important;
            background: transparent !important;
        }
    </style>
    """, unsafe_allow_html=True)

    _, col_auth, _ = st.columns([1, 1.15, 1])
    with col_auth:
        mode = st.session_state["auth_mode"]
        
        # ---------------- FORGOT PASSWORD VIEW ----------------
        if mode == "forgot":
            with st.form("forgot_password_form"):
                st.markdown("""
                <div style='text-align: center; margin-bottom: 20px;'>
                    <h1 style='font-size: 2.1rem; font-weight: 800; color: #ffffff; margin: 0;'>Reset Access</h1>
                    <p style='color: rgba(255,255,255,0.85); font-size: 0.85rem; margin-top: 6px;'>Apna registered email enter karein password reset link paane ke liye.</p>
                </div>
                """, unsafe_allow_html=True)
                
                reset_email = st.text_input("Reset Email", placeholder="✉️  email@domain.com", label_visibility="collapsed")
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                
                submit_reset = st.form_submit_button("Send Reset Link", use_container_width=True)
                
                if submit_reset:
                    if not reset_email:
                        st.error("⚠️ Kripya email enter karein.")
                    else:
                        try:
                            clean_reset = reset_email.replace("✉️", "").strip()
                            supabase.auth.reset_password_for_email(
                                clean_reset, 
                                {"redirect_to": "https://beststockfilter.streamlit.app"}
                            )
                            st.success("📩 Password reset link aapke email par bhej diya gaya hai! Inbox check karein.")
                        except Exception as e:
                            st.error(f"Reset Failed: {str(e)}")
            
            if st.button("⬅️ Back to Login", key="back_to_login", use_container_width=True):
                st.session_state["auth_mode"] = "login"
                st.rerun()

        # ---------------- LOGIN & REGISTER VIEW ----------------
        else:
            is_login = mode == "login"
            card_title = "Login" if is_login else "Register"
            
            with st.form("auth_form"):
                st.markdown(f"""
                <div style='text-align: center; margin-bottom: 24px;'>
                    <h1 style='font-size: 2.3rem; font-weight: 800; color: #ffffff; margin: 0; letter-spacing: 0.5px;'>{card_title}</h1>
                </div>
                """, unsafe_allow_html=True)
                
                full_name = None
                if not is_login:
                    full_name = st.text_input("Name", placeholder="👤  Full Name (Jaise: Rahul Sharma)", label_visibility="collapsed")
                    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                
                email = st.text_input("Email", placeholder="✉️  email@domain.com", label_visibility="collapsed")
                st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
                password = st.text_input("Password", type="password", placeholder="🔒  ••••••••••••", label_visibility="collapsed")
                
                st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
                submit = st.form_submit_button(card_title, use_container_width=True)
                
                if submit:
                    if not email or not password:
                        st.error("⚠️ Email aur Password dono fill karein.")
                    elif not is_login and not full_name:
                        st.error("⚠️️ Kripya apna Naam fill karein.")
                    elif len(password) < 6:
                        st.error("⚠️ Password minimum 6 characters ka hona chahiye.")
                    else:
                        clean_email = email.replace("✉️", "").strip()
                        if "@" not in clean_email:
                            clean_email = f"{clean_email}@terminal.com"
                        
                        if not is_login:
                            try:
                                res = supabase.auth.sign_up({
                                    "email": clean_email,
                                    "password": password,
                                    "options": {
                                        "data": {"full_name": full_name.strip()}
                                    }
                                })
                                if res.user:
                                    st.success("✅ Account ban gaya! Ab Login karke access karein.")
                                    st.session_state["auth_mode"] = "login"
                            except Exception as e:
                                st.error(f"Sign Up Failed: {str(e)}")
                        else:
                            try:
                                res = supabase.auth.sign_in_with_password({"email": clean_email, "password": password})
                                if res.user:
                                    st.session_state["user"] = res.user.email
                                    meta_name = res.user.user_metadata.get("full_name") if res.user.user_metadata else None
                                    st.session_state["user_name"] = meta_name if meta_name else res.user.email.split("@")[0].capitalize()
                                    st.rerun()
                            except Exception:
                                st.error("❌ Invalid Credentials. Dobara check karein.")

            if is_login:
                if st.button("Don't have an account? Register", key="switch_to_reg", use_container_width=True):
                    st.session_state["auth_mode"] = "register"
                    st.rerun()
                if st.button("Forgot Password?", key="switch_to_forgot", use_container_width=True):
                    st.session_state["auth_mode"] = "forgot"
                    st.rerun()
            else:
                if st.button("Already have an account? Login", key="switch_to_login", use_container_width=True):
                    st.session_state["auth_mode"] = "login"
                    st.rerun()

    st.stop()

# ================= POST-LOGIN TERMINAL THEME & APP =================
st.markdown("""
<style>
    /* Global Background Fix */
    .stApp { 
        background: #080a0f !important; 
        color: #f1f5f9 !important; 
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important; 
    }
    .stApp::before { display: none !important; }
    
    /* Text Color Fix - Sabhi text clear dikhenge */
    h1, h2, h3, h4, h5, p, span, label, div {
        color: #f1f5f9 !important;
    }

    section[data-testid="stSidebar"] { 
        background-color: #0f131c !important; 
        border-right: 1px solid #1e2638 !important; 
    }

    /* Selectbox dropdown fix */
    div[data-baseweb="select"] {
        background-color: #161c2b !important;
        border: 1px solid #2d384e !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="select"] * {
        color: #ffffff !important;
    }

    /* Screener Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #0052cc 0%, #00c49f 100%) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 0.6rem 1.2rem !important;
        box-shadow: 0 4px 15px rgba(0, 196, 159, 0.3) !important;
    }

    /* Metrics Cards */
    div[data-testid="stMetric"] {
        background-color: #111622 !important;
        border: 1px solid #1e2638 !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
    }
    div[data-testid="stMetric"] label { color: #8b9bb4 !important; font-size: 0.8rem !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #00d2c4 !important;
        font-family: monospace !important;
        font-weight: 700 !important;
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
        if data.get('status'):
            return smart_api
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
display_name = st.session_state.get('user_name', st.session_state['user'])
with c_title:
    st.markdown("<h2 style='margin-bottom:0;'>⚡ SANDEEP KUMAR <span style='font-size:1rem;color:#00d2c4;'>PRO TERMINAL</span></h2>", unsafe_allow_html=True)
    st.
