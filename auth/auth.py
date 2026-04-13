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
    [data-testid="stSidebar"]{display:none}
    #MainMenu,footer,header{visibility:hidden}
    [data-testid="stAppViewContainer"]>.main{
        background: linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%);
        min-height:100vh;
    }
    .lcard{
        background:rgba(255,255,255,0.05);
        backdrop-filter:blur(20px);
        border:1px solid rgba(255,255,255,0.12);
        border-radius:20px;
        padding:44px 48px 36px;
    }
    .lbadge{
        display:inline-flex;align-items:center;gap:8px;
        background:rgba(99,102,241,0.2);border:1px solid rgba(99,102,241,0.4);
        border-radius:20px;padding:4px 14px;font-size:11px;color:#a5b4fc;
        margin-bottom:20px;letter-spacing:0.04em;
    }
    .ltitle{font-size:28px;font-weight:800;color:#fff;margin-bottom:6px;letter-spacing:-0.5px}
    .lsub{font-size:13px;color:rgba(255,255,255,0.55);margin-bottom:32px}
    .lcreds{
        background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.25);
        border-radius:10px;padding:14px 16px;font-size:12px;
        color:rgba(255,255,255,0.6);margin-top:16px;line-height:2;
    }
    .lcreds strong{color:#a5b4fc}
    /* Override Streamlit form inputs for dark bg */
    [data-testid="stForm"] input{
        background:rgba(255,255,255,0.07) !important;
        border:1px solid rgba(255,255,255,0.15) !important;
        color:#fff !important; border-radius:10px !important;
    }
    [data-testid="stForm"] input:focus{
        border-color:#6366f1 !important;
        box-shadow:0 0 0 3px rgba(99,102,241,0.2) !important;
    }
    [data-testid="stForm"] label{color:rgba(255,255,255,0.7) !important;font-size:13px !important}
    [data-testid="stFormSubmitButton"]>button{
        background:linear-gradient(135deg,#6366f1,#8b5cf6) !important;
        border:none !important;border-radius:10px !important;
        font-weight:600 !important;font-size:14px !important;
        color:#fff !important;padding:10px !important;
        transition:opacity .2s !important;
    }
    [data-testid="stFormSubmitButton"]>button:hover{opacity:.88 !important}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    _, col, _ = st.columns([1.2, 2, 1.2])
    with col:
        st.markdown("""
        <div class="lcard">
          <div class="lbadge">⬡ &nbsp;AI-Powered Analytics</div>
          <div class="ltitle">noon OOS Agent</div>
          <div class="lsub">Out-of-Stock Intelligence — powered by Claude AI &amp; BigQuery</div>
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
