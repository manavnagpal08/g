import streamlit as st
import requests
import urllib.parse

st.set_page_config(page_title="Google Login", page_icon="🔐", layout="centered")

# ---------------------------------------------
# Load Secrets
# ---------------------------------------------
CLIENT_ID = st.secrets["google_client_id"]
CLIENT_SECRET = st.secrets["google_client_secret"]
REDIRECT_URI = st.secrets["redirect_uri"]
FIREBASE_API_KEY = st.secrets["firebase_api_key"]

if "user" not in st.session_state:
    st.session_state.user = None


# ---------------------------------------------
# Step 1: Build Google OAuth URL
# ---------------------------------------------
def get_google_auth_url():
    base = "https://accounts.google.com/o/oauth2/v2/auth"

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }

    return base + "?" + urllib.parse.urlencode(params)


# ---------------------------------------------
# Step 2: Exchange CODE -> TOKENS
# ---------------------------------------------
def exchange_code_for_tokens(code):
    token_url = "https://oauth2.googleapis.com/token"

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    res = requests.post(token_url, data=data)
    return res.json()


# ---------------------------------------------
# Step 3: Get GOOGLE User Info
# ---------------------------------------------
def get_google_profile(access_token):
    res = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return res.json()


# ---------------------------------------------
# Step 4: Firebase Sign-In with Google Token
# ---------------------------------------------
def firebase_sign_in(id_token):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"

    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": REDIRECT_URI,
        "returnIdpCredential": True,
        "returnSecureToken": True,
    }

    return requests.post(url, json=payload).json()


# ---------------------------------------------
# Step 5: Process Redirect from Google
# ---------------------------------------------
def process_google_redirect():
    params = st.experimental_get_query_params()
    if "code" not in params:
        return False

    code = params["code"][0]

    # Exchange for tokens
    tokens = exchange_code_for_tokens(code)

    if "access_token" not in tokens:
        st.error("Login failed: Could not get access token.")
        return False

    # Clear params from URL
    st.experimental_set_query_params()

    # Get profile from Google
    profile = get_google_profile(tokens["access_token"])

    # Firebase login (optional but gives UID)
    firebase_res = firebase_sign_in(tokens["id_token"])

    # Save user info in session
    st.session_state.user = {
        "name": profile.get("name"),
        "email": profile.get("email"),
        "picture": profile.get("picture"),
        "uid": firebase_res.get("localId"),
    }

    return True


# ---------------------------------------------
# MAIN UI
# ---------------------------------------------
st.title("🔐 Login with Google (Redirect Flow - Works 100%)")

# If user not logged in → handle redirect OR show login button
if not st.session_state.user:
    # Attempt to handle redirect
    if not process_google_redirect():
        auth_url = get_google_auth_url()

        # Show Google Login Button
        st.markdown(
            f"""
            <a href="{auth_url}" target="_self"
               style="padding:12px 20px;background:#4285F4;color:white;
                      border-radius:8px;text-decoration:none;font-size:18px;">
               🔵 Sign in with Google
            </a>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

# ---------------------------------------------
# After Login: Welcome Screen
# ---------------------------------------------
user = st.session_state.user

st.success(f"Welcome {user['name']} 👋")

if user["picture"]:
    st.image(user["picture"], width=120)

st.write(f"**Email:** {user['email']}")
st.write(f"**UID:** {user.get('uid')}")

if st.button("Logout"):
    st.session_state.user = None
    st.rerun()
