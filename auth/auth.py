import hashlib, hmac, streamlit as st

USERS = {
    "admin":            {"password_hash": hashlib.sha256("admin123".encode()).hexdigest(), "name": "Admin User",        "role": "admin"},
    "category_manager": {"password_hash": hashlib.sha256("noon2024".encode()).hexdigest(), "name": "Category Manager",  "role": "manager"},
    "analyst":          {"password_hash": hashlib.sha256("analyst123".encode()).hexdigest(),"name": "Data Analyst",     "role": "analyst"},
}

def _hash(p): return hashlib.sha256(p.encode()).hexdigest()
def check_credentials(u, p):
    user = USERS.get(u.lower().strip())
    return user and hmac.compare_digest(user["password_hash"], _hash(p))
def get_user(u): return USERS.get(u.lower().strip(), {})
def is_authenticated(): return st.session_state.get("authenticated", False)
def logout():
    for k in ["authenticated","username","user_name","user_role"]: st.session_state.pop(k, None)

def login_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Full page reset ── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"]  { display: none; }
    #MainMenu, footer, header  { visibility: hidden; }

    [data-testid="stAppViewContainer"] > .main {
        background: #0e0e0e;
        min-height: 100vh;
        display: flex;
        align-items: center;
    }

    /* ── Subtle background glow ── */
    [data-testid="stAppViewContainer"] > .main::before {
        content: '';
        position: fixed;
        top: 50%;  left: 50%;
        transform: translate(-50%, -60%);
        width: 600px; height: 600px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,206,0,0.07) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Card ── */
    .login-wrap {
        background: #161616;
        border: 1px solid rgba(255, 206, 0, 0.18);
        border-radius: 24px;
        padding: 52px 52px 44px;
        box-shadow:
            0 0 0 1px rgba(255,255,255,0.03),
            0 32px 64px rgba(0,0,0,0.55),
            0 0 80px rgba(255,206,0,0.05);
        position: relative;
        overflow: hidden;
    }

    /* Top accent line */
    .login-wrap::before {
        content: '';
        position: absolute;
        top: 0; left: 10%; right: 10%;
        height: 2px;
        background: linear-gradient(90deg, transparent, #FFCE00, transparent);
        border-radius: 0 0 2px 2px;
    }

    /* ── noon wordmark ── */
    .noon-wordmark {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 6px;
    }
    .noon-wordmark svg { display: block; }

    /* ── Tagline under logo ── */
    .login-tagline {
        text-align: center;
        font-size: 11px;
        font-weight: 500;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: rgba(255, 206, 0, 0.45);
        margin-bottom: 36px;
    }

    /* ── Divider ── */
    .login-divider {
        height: 1px;
        background: rgba(255,255,255,0.06);
        margin: 0 -4px 32px;
    }

    /* ── Welcome text ── */
    .login-welcome {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 4px;
        letter-spacing: -0.3px;
    }
    .login-sub {
        font-size: 13px;
        color: rgba(255,255,255,0.38);
        margin-bottom: 28px;
    }

    /* ── Form inputs ── */
    [data-testid="stForm"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    [data-testid="stForm"] label {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: rgba(255,255,255,0.5) !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        margin-bottom: 6px !important;
    }
    [data-testid="stForm"] input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        font-size: 14px !important;
        padding: 12px 16px !important;
        transition: all 0.2s !important;
    }
    [data-testid="stForm"] input:hover {
        border-color: rgba(255,206,0,0.3) !important;
        background: rgba(255,255,255,0.07) !important;
    }
    [data-testid="stForm"] input:focus {
        border-color: #FFCE00 !important;
        background: rgba(255,206,0,0.06) !important;
        box-shadow: 0 0 0 3px rgba(255,206,0,0.12) !important;
        outline: none !important;
    }
    [data-testid="stForm"] input::placeholder {
        color: rgba(255,255,255,0.2) !important;
    }

    /* ── Sign in button ── */
    [data-testid="stFormSubmitButton"] > button {
        width: 100% !important;
        background: #FFCE00 !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        color: #111111 !important;
        padding: 13px !important;
        margin-top: 8px !important;
        letter-spacing: 0.02em !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 20px rgba(255,206,0,0.25) !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background: #ffe033 !important;
        box-shadow: 0 6px 28px rgba(255,206,0,0.38) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0px) !important;
    }

    /* ── Error message ── */
    [data-testid="stAlert"] {
        background: rgba(239,68,68,0.1) !important;
        border: 1px solid rgba(239,68,68,0.25) !important;
        border-radius: 10px !important;
        color: #fca5a5 !important;
        font-size: 13px !important;
    }

    /* ── Footer ── */
    .login-footer {
        text-align: center;
        font-size: 11px;
        color: rgba(255,255,255,0.18);
        margin-top: 28px;
        letter-spacing: 0.04em;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1.1, 1.6, 1.1])
    with col:
        # Card top (logo + tagline + divider + welcome)
        st.markdown("""
        <div class="login-wrap">
          <!-- noon wordmark -->
          <div class="noon-wordmark">
            <svg width="110" height="38" viewBox="0 0 110 38" xmlns="http://www.w3.org/2000/svg">
              <text x="2" y="32"
                    font-family="'Arial Black', Arial, sans-serif"
                    font-weight="900"
                    font-size="36"
                    fill="#FFCE00"
                    letter-spacing="-1">noon</text>
            </svg>
          </div>
          <div class="login-tagline">OOS Intelligence Platform</div>
          <div class="login-divider"></div>
          <div class="login-welcome">Welcome back</div>
          <div class="login-sub">Sign in to your account to continue</div>
        </div>
        """, unsafe_allow_html=True)

        # Streamlit form (rendered on top of card via negative margin trick)
        st.markdown("""
        <style>
        /* Pull form up into the card visually */
        [data-testid="stForm"] {
            margin-top: -16px !important;
            background: #161616 !important;
            border: 1px solid rgba(255,206,0,0.18) !important;
            border-top: none !important;
            border-radius: 0 0 24px 24px !important;
            padding: 8px 52px 44px !important;
            box-shadow: 0 32px 64px rgba(0,0,0,0.55) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("User ID", placeholder="Enter your user ID")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.form_submit_button("Sign In →", use_container_width=True):
                if check_credentials(username, password):
                    user = get_user(username)
                    st.session_state.update(
                        authenticated=True, username=username,
                        user_name=user["name"], user_role=user["role"]
                    )
                    st.rerun()
                else:
                    st.error("Incorrect user ID or password. Please try again.")

        st.markdown("""
        <div class="login-footer">© 2025 noon · Powered by Claude AI</div>
        """, unsafe_allow_html=True)

    return False
