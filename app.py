import streamlit as st
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
import requests

# -------------------------------------------
# CONFIG
# -------------------------------------------
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_url = st.secrets["redirect_url"]         # Example: https://yourapp.streamlit.app/
firebase_api_key = st.secrets["firebase_api_key"]

google_client = GoogleOAuth2(client_id, client_secret)

if "user" not in st.session_state:
    st.session_state.user = None


# -------------------------------------------
# GET GOOGLE TOKEN FROM CODE
# -------------------------------------------
async def get_tokens(code: str):
    return await google_client.get_access_token(code, redirect_url)


# -------------------------------------------
# GET USER INFO (NAME, EMAIL, PIC)
# Google UserInfo API
# -------------------------------------------
def get_google_profile(access_token: str):
    res = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return res.json()


# -------------------------------------------
# OPTIONAL: SIGN IN TO FIREBASE (REST)
# -------------------------------------------
def firebase_sign_in(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={firebase_api_key}"

    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": redirect_url,
        "returnSecureToken": True
    }

    return requests.post(url, json=payload).json()


# -------------------------------------------
# PROCESS GOOGLE LOGIN
# -------------------------------------------
def process_google_login():
    params = st.experimental_get_query_params()

    if "code" not in params:
        return False

    code = params["code"][0]

    # Exchange code → tokens
    token_data = asyncio.run(get_tokens(code))
    st.experimental_set_query_params()

    if "access_token" not in token_data:
        st.error("Google login failed.")
        return False

    # Get Google user profile
    profile = get_google_profile(token_data["access_token"])

    st.session_state.user = {
        "name": profile.get("name"),
        "email": profile.get("email"),
        "picture": profile.get("picture"),
        "sub": profile.get("sub"),
    }

    return True


# -------------------------------------------
# GOOGLE LOGIN BUTTON
# -------------------------------------------
def google_login_button():
    auth_url = asyncio.run(
        google_client.get_authorization_url(
            redirect_url,
            scope=[
                "openid",
                "email",
                "profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            extras_params={"access_type": "offline"}
        )
    )

    st.markdown(
        f"""
        <a href="{auth_url}" target="_self" 
        style="padding:14px 25px; background:#4285F4; color:white; 
               border-radius:8px; text-decoration:none; font-size:18px;
               font-weight:600; display:inline-block;">
            🔵 Login with Google
        </a>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------
# MAIN APP UI
# -------------------------------------------
def app():
    st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

    st.title("🔐 Login with Google")

    # If not logged in, process redirect
    if not st.session_state.user:
        login_success = process_google_login()

        if not login_success:
            google_login_button()
            return

    # Logged in → show welcome page
    user = st.session_state.user

    st.success(f"Welcome, {user['name']} 👋")
    st.image(user["picture"], width=120)

    st.write(f"**Email:** {user['email']}")
    st.write("---")
    st.write("You are successfully logged in. Redirecting to next page...")

    if st.button("➡ Go to Dashboard"):
        st.switch_page("pages/dashboard.py")

    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()


app()
