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

# noon logo SVG — yellow wordmark
_NOON_LOGO = """<svg width="80" height="30" viewBox="0 0 80 30" xmlns="http://www.w3.org/2000/svg">
  <text x="1" y="25" font-family="'Arial Black',Arial,sans-serif"
        font-weight="900" font-size="27" fill="#FFCE00" letter-spacing="-0.5">noon</text>
</svg>"""

def login_page():
    st.markdown("""
    <style>
    [data-testid="stSidebar"]{display:none}
    #MainMenu,footer,header{visibility:hidden}
    [data-testid="stAppViewContainer"]>.main{
        background:linear-gradient(135deg,#111111 0%,#1A1A1A 50%,#111111 100%);
        min-height:100vh;
    }
    .lcard{
        background:rgba(255,255,255,0.04);
        backdrop-filter:blur(20px);
        border:1px solid rgba(255,206,0,0.18);
        border-radius:20px;
        padding:44px 48px 36px;
    }
    .lbadge{
        display:inline-flex;align-items:center;gap:8px;
        background:rgba(255,206,0,0.12);border:1px solid rgba(255,206,0,0.28);
        border-radius:20px;padding:4px 14px;font-size:11px;color:#FFCE00;
        margin-bottom:20px;letter-spacing:0.04em;
    }
    .ltitle{font-size:26px;font-weight:800;color:#fff;margin-bottom:6px;letter-spacing:-0.5px}
    .lsub{font-size:13px;color:rgba(255,255,255,0.45);margin-bottom:32px}
    .lcreds{
        background:rgba(255,206,0,0.07);
        border:1px solid rgba(255,206,0,0.18);
        border-radius:10px;padding:14px 16px;font-size:12px;
        color:rgba(255,255,255,0.55);margin-top:16px;line-height:2;
    }
    .lcreds strong{color:#FFCE00}
    [data-testid="stForm"] input{
        background:rgba(255,255,255,0.06) !important;
        border:1px solid rgba(255,255,255,0.12) !important;
        color:#fff !important;border-radius:10px !important;
    }
    [data-testid="stForm"] input:focus{
        border-color:#FFCE00 !important;
        box-shadow:0 0 0 3px rgba(255,206,0,0.15) !important;
    }
    [data-testid="stForm"] label{color:rgba(255,255,255,0.65) !important;font-size:13px !important}
    [data-testid="stFormSubmitButton"]>button{
        background:linear-gradient(135deg,#FFCE00,#e6b800) !important;
        border:none !important;border-radius:10px !important;
        font-weight:700 !important;font-size:14px !important;
        color:#1A1A1A !important;padding:10px !important;
        transition:opacity .2s !important;
    }
    [data-testid="stFormSubmitButton"]>button:hover{opacity:.88 !important}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1.2, 2, 1.2])
    with col:
        st.markdown(f"""
        <div class="lcard">
          <div style="margin-bottom:14px">{_NOON_LOGO}</div>
          <div class="lbadge">📦 &nbsp;OOS Intelligence Platform</div>
          <div class="ltitle">Out-of-Stock Agent</div>
          <div class="lsub">Powered by Claude AI · Electronics, Fashion, Home &amp; Beauty</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="your username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            if st.form_submit_button("Sign in →", use_container_width=True):
                if check_credentials(username, password):
                    user = get_user(username)
                    st.session_state.update(authenticated=True, username=username,
                                            user_name=user["name"], user_role=user["role"])
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")

        st.markdown("""
        <div class="lcreds">
          <strong>Demo credentials</strong><br>
          admin / admin123 &nbsp;·&nbsp; category_manager / noon2024 &nbsp;·&nbsp; analyst / analyst123
        </div>
        """, unsafe_allow_html=True)
    return False
