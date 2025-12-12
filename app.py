import streamlit as st
import requests
from streamlit.components.v1 import html

st.set_page_config(page_title="Google Login", page_icon="🔐", layout="centered")

GOOGLE_CLIENT_ID = st.secrets["google_client_id"]
FIREBASE_API_KEY = st.secrets["firebase_api_key"]

if "user" not in st.session_state:
    st.session_state.user = None
if "google_token" not in st.session_state:
    st.session_state.google_token = None

st.title("🔐 Login with Google — Streamlit Safe Version")


# ------------------------------------------------------
# 1. GOOGLE ONE TAP CODE (No f-string, No JS errors)
# ------------------------------------------------------
google_html = f"""
<script src="https://accounts.google.com/gsi/client" async defer></script>

<div id="g_id_onload"
     data-client_id="{GOOGLE_CLIENT_ID}"
     data-context="signin"
     data-ux_mode="popup"
     data-callback="googleCallback">
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
function googleCallback(response) {{
    // Send the token to Streamlit
    window.parent.postMessage(
        {{ type: "GOOGLE_LOGIN", token: response.credential }},
        "*"
    );
}}
</script>
"""

html(google_html, height=350)


# ------------------------------------------------------
# 2. LISTEN FOR GOOGLE TOKEN VIA postMessage
# ------------------------------------------------------
message_listener = """
<script>
window.addEventListener("message", (event) => {
    if (event.data.type === "GOOGLE_LOGIN") {
        const token = event.data.token;
        const streamlitEvent = new CustomEvent("streamlit:google_token", {{
            detail: token
        }});
        window.parent.document.dispatchEvent(streamlitEvent);
    }
});
</script>
"""

html(message_listener, height=0)


# ------------------------------------------------------
# 3. CAPTURE TOKEN INSIDE STREAMLIT
# ------------------------------------------------------
def catch_google_token():
    return st.experimental_get_query_params().get("google_token", [None])[0]


# component to attach event to streamlit
token_script = """
<script>
document.addEventListener("streamlit:google_token", (event) => {
    const token = event.detail;
    const url = new URL(window.location);

    url.searchParams.set("google_token", token);
    window.location.href = url.toString();
});
</script>
"""

html(token_script, height=0)

google_token = catch_google_token()

if google_token:
    st.session_state.google_token = google_token


# ------------------------------------------------------
# 4. FIREBASE LOGIN
# ------------------------------------------------------
def firebase_login_with_google(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": "https://localhost",  # unused but required
        "returnSecureToken": True
    }
    return requests.post(url, json=payload).json()


# ------------------------------------------------------
# 5. PROCESS LOGIN
# ------------------------------------------------------
if st.session_state.google_token and not st.session_state.user:
    res = firebase_login_with_google(st.session_state.google_token)

    if "email" in res:
        st.session_state.user = {
            "email": res["email"],
            "name": res.get("displayName", "User"),
            "picture": res.get("photoUrl", None),
        }

        # Remove token from URL
        st.experimental_set_query_params()


# ------------------------------------------------------
# 6. SHOW USER INFO
# ------------------------------------------------------
if st.session_state.user:
    st.success(f"Welcome {st.session_state.user['name']} 👋")

    if st.session_state.user["picture"]:
        st.image(st.session_state.user["picture"], width=120)

    st.write(f"**Email:** {st.session_state.user['email']}")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.google_token = None
        st.experimental_set_query_params()
        st.rerun()
