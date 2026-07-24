import streamlit as st
import requests
import base64
from newspaper import Article

API_URL = "http://localhost:8000"

st.set_page_config(page_title="News Analyzer", page_icon="📰", layout="wide")

# ── Inline SVG icons ───────────────────────────────────────────────────────────
# Using inline SVG instead of an icon webfont — guaranteed to render regardless
# of CDN availability, ad-blockers, or font-loading restrictions.
ICON_PATHS = {
    "news":               '<path d="M16 6h3a1 1 0 0 1 1 1v11a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-11a1 1 0 0 1 1 -1h3" /><path d="M8 4h8v4h-8z" /><path d="M8 11h8" /><path d="M8 15h8" />',
    "user-circle":        '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 10m-3 0a3 3 0 1 0 6 0a3 3 0 1 0 -6 0" /><path d="M6.168 18.849a4 4 0 0 1 3.832 -2.849h4a4 4 0 0 1 3.834 2.855" />',
    "alert-circle":       '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 8v4" /><path d="M12 16h.01" />',
    "circle-check":       '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M9 12l2 2l4 -4" />',
    "circle-x":           '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M10 10l4 4m0 -4l-4 4" />',
    "wifi-off":           '<path d="M12 18l.01 0" /><path d="M9.172 15.172a4 4 0 0 1 5.656 0" /><path d="M6.343 12.343a8 8 0 0 1 3.864 -2.14m4.163 .155a7.965 7.965 0 0 1 3.287 2" /><path d="M3.515 9.515a13 13 0 0 1 3.448 -2.41m3.001 -.912a13 13 0 0 1 10.521 3.322" /><path d="M3 3l18 18" />',
    "lock":               '<path d="M5 13a2 2 0 0 1 2 -2h10a2 2 0 0 1 2 2v6a2 2 0 0 1 -2 2h-10a2 2 0 0 1 -2 -2z" /><path d="M11 16a1 1 0 1 0 2 0a1 1 0 0 0 -2 0" /><path d="M8 11v-4a4 4 0 1 1 8 0v4" />',
    "article":            '<path d="M16 6h3a1 1 0 0 1 1 1v11a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2v-11a1 1 0 0 1 1 -1h3" /><path d="M8 4h8v4h-8z" /><path d="M8 11h8" /><path d="M8 15h6" />',
    "history":            '<path d="M12 8l0 4l2 2" /><path d="M3.05 11a9 9 0 1 1 .5 4m-.5 5v-5h5" />',
    "align-left":         '<path d="M4 6l16 0" /><path d="M4 12l10 0" /><path d="M4 18l14 0" />',
    "clock":              '<path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 3" />',
    "file-text":          '<path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M5 12v-7a2 2 0 0 1 2 -2h7l5 5v4" /><path d="M9 17h6" /><path d="M9 13h6" /><path d="M5 15v6h1.5a2.5 2.5 0 0 0 0 -5h-1.5" /><path d="M17 21v-6l2.5 6v-6" />',
    "calendar":           '<path d="M4 7a2 2 0 0 1 2 -2h12a2 2 0 0 1 2 2v12a2 2 0 0 1 -2 2h-12a2 2 0 0 1 -2 -2z" /><path d="M16 3v4" /><path d="M8 3v4" /><path d="M4 11h16" /><path d="M11 15h1" /><path d="M12 15v3" />',
    "tag":                '<path d="M7.859 6h-2.834a2.025 2.025 0 0 0 -2.025 2.025v2.834c0 .537 .213 1.052 .593 1.432l8.93 8.93a2.025 2.025 0 0 0 2.864 0l5.273 -5.273a2.025 2.025 0 0 0 0 -2.864l-8.93 -8.93a2.025 2.025 0 0 0 -1.432 -.593z" /><path d="M17.5 10.5m-1.5 0a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0 -3 0" />',
    "trending-up":        '<path d="M3 17l6 -6l4 4l8 -8" /><path d="M14 7l7 0l0 7" />',
    "trending-down":      '<path d="M3 7l6 6l4 -4l8 8" /><path d="M14 17l7 0l0 -7" />',
    "cpu":                '<path d="M5 5m0 1a1 1 0 0 1 1 -1h12a1 1 0 0 1 1 1v12a1 1 0 0 1 -1 1h-12a1 1 0 0 1 -1 -1z" /><path d="M9 9h6v6h-6z" /><path d="M3 10h2" /><path d="M3 14h2" /><path d="M10 3v2" /><path d="M14 3v2" /><path d="M21 10h-2" /><path d="M21 14h-2" /><path d="M14 21v-2" /><path d="M10 21v-2" />',
    "building-government":'<path d="M4 21v-13l8 -4l8 4v13" /><path d="M4 21l16 0" /><path d="M9 21v-6a3 3 0 0 1 6 0v6" /><path d="M8 10v-4" /><path d="M16 10v-4" />',
    "trophy":             '<path d="M8 21l8 0" /><path d="M12 17l0 4" /><path d="M7 4l10 0" /><path d="M17 4v8a5 5 0 0 1 -10 0v-8" /><path d="M5 9a2 2 0 0 1 -2 -2v-1a1 1 0 0 1 1 -1h3" /><path d="M19 9a2 2 0 0 0 2 -2v-1a1 1 0 0 0 -1 -1h-3" />',
    "briefcase":          '<path d="M3 7m0 2a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v9a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2z" /><path d="M8 7v-2a2 2 0 0 1 2 -2h4a2 2 0 0 1 2 2v2" /><path d="M3 13l18 0" /><path d="M12 12l0 .01" />',
    "heart-rate-monitor": '<path d="M3 12h4l2 -7l4 14l3 -7h5" />',
    "flask":              '<path d="M9 3l6 0" /><path d="M10 9l4 0" /><path d="M10 3v6l-4 11a.7 .7 0 0 0 .5 1h11a.7 .7 0 0 0 .5 -1l-4 -11v-6" />',
    "device-tv":          '<path d="M3 7m0 2a2 2 0 0 1 2 -2h14a2 2 0 0 1 2 2v8a2 2 0 0 1 -2 2h-14a2 2 0 0 1 -2 -2z" /><path d="M16 3l-4 4l-4 -4" />',
    "leaf":               '<path d="M5 21c.5 -4.5 2.5 -8 7 -10" /><path d="M9 18c6.218 0 10.5 -3.288 11 -12v-1h-4.014c-9 0 -11.986 4 -12 9c0 1 0 3 2 4z" />',
}

def icon(name, size=16, color="currentColor", style=""):
    """Return a base64-encoded SVG wrapped in an <img> tag.

    We deliberately avoid inline <svg> markup here. Different Streamlit/
    DOMPurify versions sanitize inline SVG inconsistently — in some installs
    the <svg> element itself gets stripped from st.html() output even though
    its tags/attributes are technically on the allowlist. Encoding the icon
    as a base64 data-URI and rendering it through a plain <img> tag sidesteps
    HTML sanitization of SVG entirely and works identically across versions.
    """
    paths = ICON_PATHS.get(name, ICON_PATHS["tag"])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">{paths}</svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return (
        f'<img src="data:image/svg+xml;base64,{b64}" '
        f'width="{size}" height="{size}" '
        f'style="display:inline-block;vertical-align:-3px;{style}" />'
    )

# ── Tabler Icons CDN + professional CSS ───────────────────────────────────────
# Using st.html() instead of st.markdown() — more reliable for raw <style> blocks,
# avoids the CSS being escaped and rendered as visible text.
st.html("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
  }

  /* Fix top clipping — Streamlit's header overlay was eating into block-container */
  [data-testid="stHeader"] {
    background: #F8F9FB;
    height: 0;
  }
  .block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1180px !important;
  }
  [data-testid="stAppViewContainer"] { background: #F8F9FB; }
  [data-testid="stMain"] { background: #F8F9FB; }

  .topbar-brand { display: flex; align-items: center; gap: 11px; }
  .topbar-brand .brand-icon {
    width: 38px; height: 38px; background: #11173D; border-radius: 9px;
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-size: 18px;
    box-shadow: 0 2px 6px rgba(17,23,61,0.18);
  }
  .topbar-brand .brand-name {
    font-size: 1.15rem; font-weight: 700; color: #11173D; letter-spacing: -0.02em;
  }
  .user-pill {
    display: inline-flex; align-items: center; gap: 7px;
    background: #fff; border: 1.5px solid #E4E7EE; border-radius: 20px;
    padding: 7px 16px 7px 12px; font-size: 0.85rem; font-weight: 600; color: #11173D;
  }
  .user-pill i { font-size: 15px; color: #6B7280; }

  .auth-logo { text-align: center; margin-bottom: 1.5rem; }
  .auth-logo .logo-icon {
    width: 52px; height: 52px; background: #11173D; border-radius: 13px;
    display: inline-flex; align-items: center; justify-content: center;
    color: #fff; font-size: 24px; margin-bottom: 0.85rem;
    box-shadow: 0 4px 10px rgba(17,23,61,0.2);
  }
  .auth-logo h1 { font-size: 1.4rem; font-weight: 700; color: #11173D; margin: 0; letter-spacing: -0.02em; }
  .auth-logo p { font-size: 0.88rem; color: #6B7280; margin: 0.3rem 0 0; }

  .section-label {
    font-size: 0.74rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #11173D; margin-bottom: 0.7rem;
    padding-bottom: 0.5rem; border-bottom: 2px solid #11173D;
    display: inline-block;
  }

  .metric-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 1.25rem 0; }
  .metric-card {
    background: #fff; border: 1px solid #E4E7EE; border-left: 3px solid #11173D;
    border-radius: 8px; padding: 1.1rem 1.2rem;
  }
  .metric-card .metric-label {
    font-size: 0.76rem; font-weight: 600; color: #6B7280;
    display: flex; align-items: center; gap: 6px; margin-bottom: 0.5rem;
    text-transform: uppercase; letter-spacing: 0.03em;
  }
  .metric-card .metric-label i { font-size: 14px; color: #11173D; }
  .metric-card .metric-value { font-size: 1.3rem; font-weight: 700; color: #11173D; letter-spacing: -0.01em; }
  .metric-card .metric-sub { font-size: 0.76rem; color: #9CA3AF; margin-top: 3px; font-weight: 500; }

  .summary-panel { background: #fff; border: 1px solid #E4E7EE; border-radius: 10px; padding: 1.4rem 1.5rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(17,23,61,0.04); }
  .summary-panel .summary-header {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.82rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
    color: #11173D; margin-bottom: 0.8rem; padding-bottom: 0.7rem; border-bottom: 1px solid #F3F4F6;
  }
  .summary-panel .summary-header i { font-size: 16px; color: #11173D; }
  .summary-panel .summary-text { font-size: 0.98rem; line-height: 1.8; color: #1F2937; }

  .topic-row { display: flex; align-items: center; gap: 10px; margin-bottom: 9px; }
  .topic-name { font-size: 0.82rem; font-weight: 600; color: #1F2937; width: 104px; flex-shrink: 0; }
  .topic-bar-bg { flex: 1; background: #EEF0F4; border-radius: 4px; height: 8px; overflow: hidden; }
  .topic-bar-fill { height: 8px; border-radius: 4px; background: #11173D; }
  .topic-pct { font-size: 0.8rem; font-weight: 700; color: #11173D; width: 36px; text-align: right; flex-shrink: 0; }

  .badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 0.72rem; font-weight: 500; padding: 2px 8px; border-radius: 20px;
  }
  .badge-topic { background: #EEF2FF; color: #3730A3; }
  .badge-sentiment-pos { background: #ECFDF5; color: #065F46; }
  .badge-sentiment-neg { background: #FEF2F2; color: #991B1B; }
  .badge-date { background: #F9FAFB; color: #6B7280; border: 1px solid #E4E7EE; }
  .hi-summary {
    font-size: 0.83rem; color: #6B7280; line-height: 1.6;
    margin-top: 0.65rem; padding-top: 0.65rem; border-top: 1px solid #F3F4F6;
  }

  .status-bar {
    display: flex; align-items: center; gap: 8px;
    padding: 0.7rem 1rem; border-radius: 8px;
    font-size: 0.85rem; font-weight: 500; margin-bottom: 1rem;
  }
  .status-bar.success { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
  .status-bar.error   { background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; }
  .status-bar.info    { background: #EEF2FF; color: #3730A3; border: 1px solid #C7D2FE; }
  .status-bar i { font-size: 16px; }

  .divider { border: none; border-top: 1px solid #E4E7EE; margin: 1.5rem 0; }

  .wc-pill {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 0.78rem; color: #6B7280; padding: 3px 10px;
    background: #F9FAFB; border: 1px solid #E4E7EE; border-radius: 20px; margin-top: 6px;
  }
  .wc-pill i { font-size: 13px; }
  .wc-pill.valid { color: #065F46; background: #ECFDF5; border-color: #A7F3D0; }
  .wc-pill.invalid { color: #991B1B; background: #FEF2F2; border-color: #FECACA; }

  .empty-state { text-align: center; padding: 3rem 1rem; color: #9CA3AF; }
  .empty-state i { font-size: 36px; display: block; margin-bottom: 0.75rem; }
  .empty-state p { font-size: 0.9rem; margin: 0; }

  #MainMenu, footer { visibility: hidden; }
  [data-testid="stToolbar"] { display: none; }

  /* ── Native Streamlit control overrides ── */
  div[data-testid="stButton"] button[kind="primary"] {
    background: #11173D !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    height: 2.7rem !important;
    box-shadow: 0 2px 6px rgba(17,23,61,0.18) !important;
  }
  div[data-testid="stButton"] button[kind="primary"]:hover {
    background: #1B2559 !important;
  }
  div[data-testid="stButton"] button[kind="secondary"] {
    border: 1.5px solid #E4E7EE !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    color: #11173D !important;
    height: 2.7rem !important;
  }
  div[data-testid="stButton"] button[kind="secondary"]:hover {
    border-color: #11173D !important;
    color: #11173D !important;
  }

  div[data-baseweb="tab-list"] { gap: 1.75rem !important; border-bottom: 1px solid #E4E7EE; }
  button[data-baseweb="tab"] {
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    color: #6B7280 !important;
  }
  button[data-baseweb="tab"][aria-selected="true"] {
    color: #11173D !important;
  }
  div[data-baseweb="tab-highlight"] {
    background-color: #11173D !important;
    height: 2.5px !important;
  }

  div[data-testid="stTextInput"] input,
  div[data-testid="stTextArea"] textarea {
    border: 1.5px solid #E4E7EE !important;
    border-radius: 8px !important;
    font-size: 0.92rem !important;
  }
  div[data-testid="stTextInput"] input:focus,
  div[data-testid="stTextArea"] textarea:focus {
    border-color: #11173D !important;
    box-shadow: 0 0 0 1px #11173D !important;
  }

  label[data-testid="stWidgetLabel"] p {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    color: #374151 !important;
  }
</style>
""")

TOPIC_ICONS = {
    "politics":      "building-government",
    "technology":    "cpu",
    "sports":        "trophy",
    "business":      "briefcase",
    "health":        "heart-rate-monitor",
    "science":       "flask",
    "entertainment": "device-tv",
    "environment":   "leaf",
}

# ── Session state ─────────────────────────────────────────────────────────────
for key, val in {"token": None, "username": None}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── API helpers ────────────────────────────────────────────────────────────────
def api_post(endpoint, payload, auth=False):
    headers = {}
    if auth and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=payload,
                          headers=headers, timeout=300)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        return 0, {"detail": "Cannot connect to backend. Is FastAPI running on port 8000?"}
    except requests.exceptions.Timeout:
        return 408, {"detail": "Request timed out. The model is still processing — try again."}

def api_get(endpoint):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        r = requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=30)
        return r.status_code, r.json()
    except requests.exceptions.ConnectionError:
        return 0, {"detail": "Cannot connect to backend."}

def api_delete(endpoint):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        r = requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=10)
        return r.status_code, r.json()
    except Exception:
        return 0, {}

def logout():
    st.session_state.token    = None
    st.session_state.username = None


def status_bar(kind, icon_name, message):
    """kind: success | error | info"""
    st.html(f"""
    <div class="status-bar {kind}">
      {icon(icon_name, size=16)} {message}
    </div>""")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AUTH
# ══════════════════════════════════════════════════════════════════════════════
def show_auth_page():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.html(f"""
        <div class="auth-logo">
          <div class="logo-icon">{icon("news", size=24, color="#fff")}</div>
          <h1>News Analyzer</h1>
          <p>Summarize, classify, and analyze news articles with AI</p>
        </div>
        """)

        tab_login, tab_register = st.tabs(["Sign in", "Create account"])

        # ── Login ──────────────────────────────────────────────────────────
        with tab_login:
            st.write("")
            username = st.text_input("Username", placeholder="your_username", key="login_user")
            password = st.text_input("Password", type="password",
                                     placeholder="••••••••", key="login_pass")
            st.write("")

            if st.button("Sign in", type="primary", use_container_width=True):
                if not username or not password:
                    status_bar("error", "alert-circle", "Enter your username and password.")
                else:
                    try:
                        r = requests.post(f"{API_URL}/login",
                                          data={"username": username, "password": password},
                                          timeout=10)
                        if r.status_code == 200:
                            d = r.json()
                            st.session_state.token    = d["access_token"]
                            st.session_state.username = d["username"]
                            st.rerun()
                        else:
                            status_bar("error", "alert-circle",
                                      r.json().get("detail", "Incorrect username or password."))
                    except Exception:
                        status_bar("error", "wifi-off", "Cannot reach backend.")

        # ── Register ───────────────────────────────────────────────────────
        with tab_register:
            st.write("")
            new_user    = st.text_input("Username",            key="reg_user",    placeholder="choose_a_username")
            new_email   = st.text_input("Email address",       key="reg_email",   placeholder="you@example.com")
            new_pass    = st.text_input("Password (min 6 chars)", type="password", key="reg_pass",    placeholder="••••••••")
            new_confirm = st.text_input("Confirm password",    type="password", key="reg_confirm", placeholder="••••••••")
            st.write("")

            if st.button("Create account", type="primary", use_container_width=True):
                if not all([new_user, new_email, new_pass, new_confirm]):
                    status_bar("error", "alert-circle", "All fields are required.")
                elif new_pass != new_confirm:
                    status_bar("error", "alert-circle", "Passwords do not match.")
                elif len(new_pass) < 6:
                    status_bar("error", "alert-circle", "Password must be at least 6 characters.")
                else:
                    code, data = api_post("/register",
                                          {"username": new_user, "email": new_email, "password": new_pass})
                    if code == 201:
                        status_bar("success", "circle-check", "Account created. Sign in to continue.")
                    else:
                        status_bar("error", "alert-circle", data.get("detail", "Registration failed."))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
def show_app_page():
    # ── Top bar ────────────────────────────────────────────────────────────
    col_brand, col_user = st.columns([5, 1])
    with col_brand:
        st.html(f"""
        <div class="topbar-brand">
          <div class="brand-icon">{icon("news", size=20, color="#fff")}</div>
          <span class="brand-name">News Analyzer</span>
        </div>
        """)
    with col_user:
        st.html(f"""
        <div class="user-pill">
          {icon("user-circle", size=16, color="#6B7280")}
          {st.session_state.username}
        </div>
        """)
        if st.button("Sign out", use_container_width=True):
            logout()
            st.rerun()

    st.html("<hr class='divider'>")

    tab_analyze, tab_history = st.tabs(["Analyze", "History"])

    # ══════════════════════════════════════════════════════════════════
    # TAB: ANALYZE
    # ══════════════════════════════════════════════════════════════════
    with tab_analyze:
        left_col, right_col = st.columns([1.1, 1], gap="large")

        with left_col:
            st.html('<div class="section-label">Input</div>')

            input_mode = st.radio("Source", ["Paste text", "URL"],
                                  horizontal=True, label_visibility="collapsed")

            title = ""
            text  = ""

            if input_mode == "Paste text":
                title = st.text_input("Article title", placeholder="Optional — leave blank to skip")
                text  = st.text_area("Article text", height=240,
                                     placeholder="Paste the full article here. Minimum 50 words.",
                                     label_visibility="collapsed")
            else:
                url = st.text_input("Article URL", placeholder="https://")
                if url:
                    with st.spinner("Fetching article..."):
                        try:
                            a = Article(url)
                            a.download()
                            a.parse()
                            title, text = a.title, a.text
                            status_bar("success", "circle-check",
                                      f"Article fetched — {len(text.split())} words")
                        except Exception as e:
                            status_bar("error", "alert-circle", f"Could not fetch article: {e}")

            if text:
                wc        = len(text.split())
                valid     = wc >= 50
                cls       = "valid" if valid else "invalid"
                icon_name = "circle-check" if valid else "circle-x"
                st.html(f"""
                <span class="wc-pill {cls}">
                  {icon(icon_name, size=14)} {wc} words
                </span>""")

            st.write("")
            run = st.button("Run analysis", type="primary", use_container_width=True)

        with right_col:
            st.html('<div class="section-label">Results</div>')

            if run:
                if not text or len(text.split()) < 50:
                    status_bar("error", "alert-circle",
                              "Provide at least 50 words before running analysis.")
                else:
                    with st.spinner("Running models..."):
                        code, result = api_post("/analyze",
                                                {"text": text, "title": title},
                                                auth=True)

                    if code == 200:
                        t   = result["topic"]
                        snt = result["sentiment"]
                        snt_pos    = "Positive" in snt["sentiment"]
                        snt_icon   = "trending-up" if snt_pos else "trending-down"
                        topic_icon = TOPIC_ICONS.get(t["top_topic"], "tag")

                        st.html(f"""
                        <div class="metric-row">
                          <div class="metric-card">
                            <div class="metric-label">
                              {icon(topic_icon, size=14, color="#11173D")} Topic
                            </div>
                            <div class="metric-value">{t["top_topic"].title()}</div>
                            <div class="metric-sub">{t["confidence"]}% confidence</div>
                          </div>
                          <div class="metric-card">
                            <div class="metric-label">
                              {icon(snt_icon, size=14, color="#11173D")} Sentiment
                            </div>
                            <div class="metric-value">{snt["sentiment"].split()[0]}</div>
                            <div class="metric-sub">{snt["confidence"]}% confidence</div>
                          </div>
                          <div class="metric-card">
                            <div class="metric-label">
                              {icon("file-text", size=14, color="#11173D")} Length
                            </div>
                            <div class="metric-value">{result["word_count"]} words</div>
                            <div class="metric-sub">
                              {len(result["summary"].split())} in summary
                            </div>
                          </div>
                        </div>
                        """)

                        st.html(f"""
                        <div class="summary-panel">
                          <div class="summary-header">
                            {icon("align-left", size=15, color="#11173D")} Summary
                          </div>
                          <div class="summary-text">{result["summary"]}</div>
                        </div>
                        """)

                        st.html('<div class="section-label" style="margin-top:1rem">Topic breakdown</div>')
                        bars_html = ""
                        for topic, score in t["all_scores"].items():
                            ic = TOPIC_ICONS.get(topic, "tag")
                            bars_html += f"""
                            <div class="topic-row">
                              <div class="topic-name">
                                {icon(ic, size=13, color="#6B7280", style="margin-right:5px")}
                                {topic.title()}
                              </div>
                              <div class="topic-bar-bg">
                                <div class="topic-bar-fill" style="width:{score}%"></div>
                              </div>
                              <div class="topic-pct">{score}%</div>
                            </div>"""
                        st.html(bars_html)

                        st.html(f"""
                        <div style="margin-top:1rem;font-size:0.75rem;color:#9CA3AF;
                                    display:flex;align-items:center;gap:5px;">
                          {icon("clock", size=13, color="#9CA3AF")}
                          Processed in {result["processing_time"]}s — saved to history
                        </div>""")

                    elif code == 401:
                        status_bar("error", "lock", "Session expired. Sign in again.")
                        logout(); st.rerun()
                    else:
                        msg = result.get("detail", "Analysis failed. Try again.")
                        status_bar("error", "alert-circle", msg)
            else:
                st.html(f"""
                <div class="empty-state">
                  {icon("article", size=36, color="#9CA3AF")}
                  <p>Paste an article or enter a URL,<br>then run analysis to see results here.</p>
                </div>""")

    # ══════════════════════════════════════════════════════════════════
    # TAB: HISTORY
    # ══════════════════════════════════════════════════════════════════
    with tab_history:
        hdr_col, btn_col = st.columns([4, 1])
        with hdr_col:
            st.html('<div class="section-label">Past analyses</div>')
        with btn_col:
            if st.button("Refresh", use_container_width=True):
                st.rerun()

        code, data = api_get("/history")

        if code == 200:
            if not data:
                st.html(f"""
                <div class="empty-state">
                  {icon("history", size=36, color="#9CA3AF")}
                  <p>No analyses yet. Analyze an article to see your history.</p>
                </div>""")
            else:
                st.html(f"""
                <div style="font-size:0.78rem;color:#9CA3AF;margin-bottom:0.75rem">
                  {len(data)} recent analyses
                </div>""")

                for item in data:
                    ic       = TOPIC_ICONS.get(item["topic"], "tag")
                    snt_pos  = "Positive" in item["sentiment"]
                    snt_cls  = "badge-sentiment-pos" if snt_pos else "badge-sentiment-neg"
                    snt_icon = "trending-up" if snt_pos else "trending-down"

                    with st.expander(f"{item['article_title']}  ·  {item['topic'].title()}  ·  {item['created_at']}"):
                        st.html(f"""
                        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:0.65rem">
                          <span class="badge badge-topic">
                            {icon(ic, size=12)} {item["topic"].title()}
                          </span>
                          <span class="badge {snt_cls}">
                            {icon(snt_icon, size=12)}
                            {item["sentiment"].split()[0]}
                          </span>
                          <span class="badge badge-date">
                            {icon("calendar", size=11)}
                            {item["created_at"]}
                          </span>
                          <span class="badge badge-date">
                            {icon("file-text", size=11)}
                            {item["word_count"]} words
                          </span>
                          <span class="badge badge-date">
                            {item["topic_confidence"]}% confidence
                          </span>
                        </div>
                        <div class="hi-summary">{item["summary"]}</div>
                        """)

                        if st.button("Delete", key=f"del_{item['id']}"):
                            d_code, _ = api_delete(f"/history/{item['id']}")
                            if d_code == 200:
                                st.rerun()
        elif code == 401:
            status_bar("error", "lock", "Session expired. Sign in again.")
            logout(); st.rerun()
        else:
            status_bar("error", "alert-circle", "Could not load history.")


# ── Router ────────────────────────────────────────────────────────────────────
if st.session_state.token is None:
    show_auth_page()
else:
    show_app_page()