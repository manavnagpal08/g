import streamlit as st
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
import requests

# -----------------------------
# DEBUG HELPER
# -----------------------------
def debug(msg, data=None):
    st.write(f"🟡 DEBUG: {msg}")
    if data is not None:
        st.json(data)

# -----------------------------
# GOOGLE OAuth2 Setup
# -----------------------------
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_url = st.secrets["redirect_url"]

google_client = GoogleOAuth2(client_id, client_secret)

FIREBASE_API_KEY = st.secrets["firebase_api_key"]

if "email" not in st.session_state:
    st.session_state.email = None

############################################
# 1. Exchange OAuth CODE → Google Tokens
############################################
async def get_tokens(code: str):
    debug("Exchanging CODE for Google tokens...", {"code": code})
    try:
        token_data = await google_client.get_access_token(code, redirect_url)
        debug("Google Token Response", token_data)
        return token_data
    except Exception as e:
        st.error(f"❌ ERROR exchanging Google token: {e}")
        return None

############################################
# 2. Get Google Profile Email
############################################
async def get_user_info(access_token: str):
    debug("Getting Google user info...", {"access_token": access_token})
    try:
        user_id, user_email = await google_client.get_id_email(access_token)
        debug("Google User Info", {"user_id": user_id, "email": user_email})
        return user_id, user_email
    except Exception as e:
        st.error(f"❌ ERROR getting Google user info: {e}")
        return None, None

############################################
# 3. Firebase REST API Sign-In with Google
############################################
def firebase_signin_with_google(id_token: str):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"

    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": redirect_url,
        "returnSecureToken": True
    }

    debug("Sending payload to Firebase Sign-In", payload)

    try:
        res = requests.post(url, json=payload)
        json_res = res.json()
        debug("Firebase REST API Response", json_res)
        return json_res
    except Exception as e:
        st.error(f"❌ Firebase sign-in REST error: {e}")
        return None

############################################
# PROCESS LOGIN FLOW
############################################
def process_google_login():
    params = st.experimental_get_query_params()
    debug("URL Query Params", params)

    code = params.get("code")
    if not code:
        debug("No 'code' found in URL. User has not logged in yet.")
        return False

    code = code[0]
    debug("Google Returned CODE", code)

    token_data = asyncio.run(get_tokens(code))
    if not token_data:
        st.error("❌ Google token_data is EMPTY.")
        return False

    if "access_token" not in token_data:
        st.error("❌ Google did NOT return access_token")
        return False

    st.experimental_set_query_params()  # Clear the URL
    debug("Cleared URL Parameters")

    # Get user info
    _, email = asyncio.run(get_user_info(token_data["access_token"]))

    if not email:
        st.error("❌ Could not retrieve Google email.")
        return False

    debug("Google Email Retrieved", email)

    # Firebase REST Sign-In
    firebase_res = firebase_signin_with_google(token_data["id_token"])

    if firebase_res is None:
        st.error("❌ Firebase returned NULL")
        return False

    if "error" in firebase_res:
        st.error(f"🔥 Firebase Error: {firebase_res['error']}")
        return False

    if "email" in firebase_res:
        st.session_state.email = firebase_res["email"]
        st.session_state.firebase_uid = firebase_res.get("localId")
        st.session_state.firebase_token = firebase_res.get("idToken")

        debug("Firebase Login Success", firebase_res)
        return True

    st.error("❌ Firebase did NOT return email")
    debug("Unexpected Firebase response", firebase_res)
    return False

############################################
# GOOGLE LOGIN BUTTON
############################################
def google_login_button():
    debug("Generating Google Authorization URL...")

    auth_url = asyncio.run(
        google_client.get_authorization_url(
            redirect_url,
            scope=["email", "profile"],
            extras_params={"access_type": "offline"}
        )
    )

    debug("Google Authorization URL", auth_url)

    st.markdown(
        f"""
        <a href="{auth_url}" target="_self"
           style="padding:12px 20px;background:#4285F4;color:white;
                  border-radius:8px;text-decoration:none;font-size:16px;">
           🔵 Login with Google
        </a>
        """,
        unsafe_allow_html=True,
    )

############################################
# MAIN APP
############################################
def app():
    st.title("🔐 Google Login + Firebase (REST API ONLY) — DEBUG MODE")
    
    debug("Session State", dict(st.session_state))

    if not st.session_state.email:
        logged_in = process_google_login()

        if not logged_in:
            google_login_button()
            return

    # Logged In
    st.success(f"Logged in as {st.session_state.email}")

    st.write("Firebase UID:", st.session_state.get("firebase_uid"))
    st.write("Firebase Token:", st.session_state.get("firebase_token"))

    if st.button("Logout"):
        st.session_state.email = None
        st.rerun()

app()
