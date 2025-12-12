import streamlit as st
import requests

st.set_page_config(page_title="Google Login", page_icon="🔐", layout="centered")

GOOGLE_CLIENT_ID = st.secrets["google_client_id"]
FIREBASE_API_KEY = st.secrets["firebase_api_key"]

if "user" not in st.session_state:
    st.session_state.user = None

st.title("🔐 Login with Google — No Redirects, No 403")

# ---------------------------------------------
# GOOGLE ONE TAP JS WIDGET
# ---------------------------------------------
onetap_js = f"""
<script src="https://accounts.google.com/gsi/client" async defer></script>

<div id="g_id_onload"
     data-client_id="{GOOGLE_CLIENT_ID}"
     data-context="signin"
     data-ux_mode="popup"
     data-login_uri=""
     data-auto_prompt="false"
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

st.components.v1.html(onetap_js, height=300)


# ---------------------------------------------
# RECEIVE TOKEN FROM JS
# ---------------------------------------------
message = st.experimental_get_query_params()

# Streamlit does NOT capture postMessage → use a workaround:
google_token = st.session_state.get("google_token")

def receive_google_token():
    from streamlit_javascript import st_javascript

    token = st_javascript("""
        const sleep = ms => new Promise(r => setTimeout(r, ms));
        let received = null;

        window.addEventListener("message", (e) => {
            if(e.data.google_token){
                received = e.data.google_token;
                sessionStorage.setItem("g_token", received);
            }
        });

        await sleep(1000);

        return sessionStorage.getItem("g_token");
    """)
    return token

if google_token is None:
    google_token = receive_google_token()
    if google_token:
        st.session_state.google_token = google_token


# ---------------------------------------------
# If Google Token exists → use Firebase REST API to get user info
# ---------------------------------------------
def firebase_login(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": "http://localhost",
        "returnSecureToken": True
    }
    return requests.post(url, json=payload).json()


if st.session_state.get("google_token"):
    firebase_user = firebase_login(st.session_state.google_token)

    if "email" in firebase_user:
        st.session_state.user = {
            "email": firebase_user["email"],
            "name": firebase_user.get("displayName"),
            "picture": firebase_user.get("photoUrl")
        }

# ---------------------------------------------
# SHOW LOGGED IN USER
# ---------------------------------------------
if st.session_state.user:
    st.success(f"Welcome, {st.session_state.user['name']} 👋")
    if st.session_state.user["picture"]:
        st.image(st.session_state.user["picture"], width=120)

    st.write(f"**Email:** {st.session_state.user['email']}")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()
