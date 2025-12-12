import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials, exceptions
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2

# -----------------------------
# 🔥 FIREBASE ADMIN INITIALIZE
# -----------------------------
# Load Firebase credential from Streamlit Secrets
if "firebase_key" not in st.secrets:
    st.error("❌ ERROR: Firebase key missing in Streamlit secrets!")
    st.stop()

cred = credentials.Certificate(st.secrets["firebase_key"])

try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

# -----------------------------
# 🔥 GOOGLE OAUTH CONFIG
# -----------------------------
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]

# IMPORTANT: Add this redirect URL to Google Cloud Console
redirect_url = st.secrets.get("redirect_url", "http://localhost:8501/")

client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)

# -----------------------------
# SESSION STATE SETUP
# -----------------------------
if "email" not in st.session_state:
    st.session_state.email = None


# -----------------------------
# 🔥 ASYNC HELPERS
# -----------------------------
async def get_access_token(code: str):
    return await client.get_access_token(code, redirect_url)

async def get_user_info(token: str):
    user_id, user_email = await client.get_id_email(token)
    return user_id, user_email


# -----------------------------
# 🔥 PROCESS GOOGLE LOGIN RETURN
# -----------------------------
def process_google_login():
    try:
        params = st.experimental_get_query_params()
        code = params.get("code")

        if code:
            code = code[0]

            token_data = asyncio.run(get_access_token(code))
            st.experimental_set_query_params()  # Clear query params

            if "access_token" in token_data:
                _, email = asyncio.run(get_user_info(token_data["access_token"]))

                if email:
                    try:
                        user = auth.get_user_by_email(email)
                    except exceptions.FirebaseError:
                        user = auth.create_user(email=email)

                    st.session_state.email = user.email
                    return user.email

        return None

    except Exception as e:
        st.error(f"Google login error: {str(e)}")
        return None


# -----------------------------
# 🔥 GOOGLE LOGIN BUTTON
# -----------------------------
def google_login_button():
    authorization_url = asyncio.run(client.get_authorization_url(
        redirect_url,
        scope=["email", "profile"],
        extras_params={"access_type": "offline"},
    ))

    st.markdown(
        f"""
        <a href="{authorization_url}" target="_self"
            style="padding: 14px 24px;
                   background: #4285F4;
                   color: white;
                   border-radius: 8px;
                   font-size: 18px;
                   text-decoration: none;
                   font-weight: bold;">
            🔵 Login with Google
        </a>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# 🔥 MAIN APP
# -----------------------------
def app():
    st.title("🔐 Google Login (Firebase + Streamlit)")

    # If not logged in → check URL for token
    if not st.session_state.email:
        process_google_login()

    # Show login button if still not logged in
    if not st.session_state.email:
        google_login_button()
        return

    # Logged in user area
    st.success(f"Logged in as: **{st.session_state.email}**")

    if st.button("Logout"):
        st.session_state.email = None
        st.rerun()


app()
