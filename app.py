import streamlit as st
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
import requests

# -----------------------------
# GOOGLE OAuth2 Setup
# -----------------------------
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_url = st.secrets["redirect_url"]   # e.g., http://localhost:8501/

google_client = GoogleOAuth2(client_id, client_secret)

FIREBASE_API_KEY = st.secrets["firebase_api_key"]


if "email" not in st.session_state:
    st.session_state.email = None


# -----------------------------
# 1. Exchange OAuth code → Google access token
# -----------------------------
async def get_tokens(code: str):
    return await google_client.get_access_token(code, redirect_url)


# -----------------------------
# 2. Get Google user info (ID + email)
# -----------------------------
async def get_user_info(access_token: str):
    user_id, email = await google_client.get_id_email(access_token)
    return user_id, email


# -----------------------------
# 3. Sign in to Firebase using Google Token (REST)
# -----------------------------
def firebase_signin_with_google(id_token: str):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"

    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": redirect_url,
        "returnSecureToken": True
    }

    res = requests.post(url, json=payload)
    return res.json()


# -----------------------------
# PROCESS LOGIN (after redirect)
# -----------------------------
def process_google_login():
    params = st.experimental_get_query_params()
    code = params.get("code")

    if code:
        code = code[0]

        # 1. Exchange code → tokens
        token_data = asyncio.run(get_tokens(code))

        st.experimental_set_query_params()  # Clear URL

        if "access_token" in token_data:

            # 2. Get Google email
            _, email = asyncio.run(get_user_info(token_data["access_token"]))

            # 3. Sign in with Firebase (REST)
            firebase_res = firebase_signin_with_google(token_data["id_token"])

            if "email" in firebase_res:
                st.session_state.email = firebase_res["email"]
                st.session_state.firebase_id = firebase_res["localId"]
                st.session_state.firebase_token = firebase_res["idToken"]

                return True

    return False


# -----------------------------
# SHOW LOGIN BUTTON
# -----------------------------
def google_login_button():
    auth_url = asyncio.run(
        google_client.get_authorization_url(
            redirect_url,
            scope=["email", "profile"],
            extras_params={"access_type": "offline"}
        )
    )

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


# -----------------------------
# APP UI
# -----------------------------
def app():
    st.title("🔐 Google Login + Firebase (REST API Only)")

    if not st.session_state.email:
        process_google_login()

    if not st.session_state.email:
        google_login_button()
        return

    # Logged in
    st.success(f"Logged in as {st.session_state.email}")

    st.write("Firebase User ID:", st.session_state.firebase_id)
    st.write("Firebase Token:", st.session_state.firebase_token)

    if st.button("Logout"):
        st.session_state.email = None
        st.rerun()


app()
