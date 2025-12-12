import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="Google Login Test", page_icon="🔐", layout="centered")

st.title("🔐 Google Login Test (Firebase)")
st.write("Click the button below to sign in using Google.")

# -------------------------------------------------
# LISTEN FOR TOKEN FROM THE FRONTEND
# -------------------------------------------------
token_placeholder = st.empty()

# Streamlit JS listener
components.html(
    """
    <script>
    window.addEventListener("message", (event) => {
        if (event.data.token) {
            const tokenInput = document.getElementById("tokenInput");
            tokenInput.value = event.data.token;
            tokenInput.dispatchEvent(new Event("change"));
        }
    });
    </script>

    <input type="text" id="tokenInput" style="display:none;">
    """,
    height=0,
)

token = st.session_state.get("google_token", None)

# Hidden text input to capture token
def on_token_change():
    st.session_state["google_token"] = st.session_state["token_field"]

st.text_input("hidden_token_field", key="token_field", label_visibility="hidden", on_change=on_token_change)

# -------------------------------------------------
# FRONTEND GOOGLE LOGIN BUTTON
# -------------------------------------------------
firebase_html = """
<!DOCTYPE html>
<html>
<head>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js"></script>

<script>
  const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  };
  firebase.initializeApp(firebaseConfig);

  function googleLogin() {
    const provider = new firebase.auth.GoogleAuthProvider();
    firebase.auth().signInWithPopup(provider)
    .then((result) => {
      result.user.getIdToken().then((token) => {
        window.parent.postMessage({token: token}, "*");
      });
    })
    .catch((error) => {
      window.parent.postMessage({error: error.message}, "*");
    });
  }
</script>
</head>

<body style="font-family: Arial; text-align: center; margin-top: 20px;">
  <button onclick="googleLogin()" 
    style="padding: 12px 20px; background:#4285F4; color:white; border:none;
           border-radius:8px; cursor:pointer; font-size:16px;">
      Sign in with Google
  </button>
</body>
</html>
"""

components.html(firebase_html, height=200)

# -------------------------------------------------
# DISPLAY LOGIN RESULT
# -------------------------------------------------
st.write("---")

if "google_token" in st.session_state and st.session_state["google_token"]:
    st.success("Google Login Successful!")
    st.code(st.session_state["google_token"], language="text")

    st.write("Now you can verify token using Firebase REST API.")

else:
    st.info("Waiting for Google login...")
