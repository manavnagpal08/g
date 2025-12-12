import streamlit as st
import requests
from streamlit.components.v1 import html

st.set_page_config(page_title="Google Login", page_icon="🔐", layout="centered")

GOOGLE_CLIENT_ID = st.secrets["google_client_id"]
FIREBASE_API_KEY = st.secrets["firebase_api_key"]

if "user" not in st.session_state:
    st.session_state.user = None

st.title("🔐 Login with Google — One Tap (No Redirect)")


# -------------------------------------------
# GOOGLE ONE-TAP WIDGET (SAFE VERSION)
# -------------------------------------------
one_tap_template = """
<script src="https://accounts.google.com/gsi/client" async defer></script>

<div id="g_id_onload"
     data-client_id="CLIENT_ID_REPLACE"
     data-context="signin"
     data-ux_mode="popup"
     data-callback="onGoogleLogin">
</div>

<div class="g_id_signin"
     data-type="standard"
     data-size="large"
     data-theme="outline"
     data-text="signin_with"
     data-shape="rectangular"
     data-logo_alignment="left">
</div>

<script>
function onGoogleLogin(response) {
    window.parent.postMessage(
        { "google_token": response.credential },
        "*"
    );
}
</script>
"""

one_tap_html = one_tap_template.replace("CLIENT_ID_REPLACE", GOOGLE_CLIENT_ID)

html(one_tap_html, height=350)


# -------------------------------------------
# RECEIVE GOOGLE TOKEN FROM JS → STREAMLIT
# -------------------------------------------
def receive_google_token():
    from streamlit_javascript import st_javascript

    token = st_javascript("""
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        let stored = sessionStorage.getItem("g_token");

        window.addEventListener("message", (e) => {
            if(e.data.google_token){
                sessionStorage.setItem("g_token", e.data.google_token);
            }
        });

        await sleep(1000);
        return sessionStorage.getItem("g_token");
    """)

    return token


token = receive_google_token()
if token and "google_token" not in st.session_state:
    st.session_state.google_token = token


# -------------------------------------------
# FIREBASE REST LOGIN
# -------------------------------------------
def firebase_login(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": "http://localhost",
        "returnSecureToken": True
    }
    return requests.post(url, json=payload).json()


# -------------------------------------------
# PROCESS LOGIN
# -------------------------------------------
if st.session_state.get("google_token") and not st.session_state.user:
    res = firebase_login(st.session_state.google_token)

    if "email" in res:
        st.session_state.user = {
            "email": res["email"],
            "name": res.get("displayName"),
            "picture": res.get("photoUrl")
        }


# -------------------------------------------
# SHOW USER PROFILE
# -------------------------------------------
if st.session_state.user:
    st.success(f"Welcome {st.session_state.user['name']} 👋")

    if st.session_state.user.get("picture"):
        st.image(st.session_state.user["picture"], width=120)

    st.write(f"**Email:** {st.session_state.user['email']}")

    if st.button("Logout"):
        sessionStorage = st.session_state
        st.session_state.user = None
        st.session_state.google_token = None
        st.rerun()
