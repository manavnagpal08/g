import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Google Login Test", page_icon="🔐", layout="centered")

st.title("🔐 Google Login Test (Firebase - ScreenerPro)")
st.write("Click the button below to sign in with Google and retrieve your Firebase ID Token.")

# -------------------------------------------------
# LISTEN FOR TOKEN SENT FROM FRONTEND
# -------------------------------------------------
components.html(
    """
    <script>
    // Listen for token posted from the iframe
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

# Hidden text input that triggers a Streamlit session-state update
def on_token_change():
    st.session_state["google_token"] = st.session_state["token_field"]

st.text_input(
    "hidden_token_field",
    key="token_field",
    label_visibility="hidden",
    on_change=on_token_change,
)

# -------------------------------------------------
# FRONTEND GOOGLE LOGIN BUTTON (Firebase Web SDK)
# -------------------------------------------------
firebase_html = """
<!DOCTYPE html>
<html>
<head>

<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js"></script>

<script>
  // Your Firebase Config (ScreenerPro)
  const firebaseConfig = {
    apiKey: "AIzaSyDjC7tdmpEkpsipgf9r1c3HlTO7C7BZ6Mw",
    authDomain: "screenerproapp.firebaseapp.com",
    projectId: "screenerproapp"
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
    style="
      padding: 12px 20px;
      background:#4285F4;
      color:white;
      border:none;
      border-radius:8px;
      font-size:16px;
      cursor:pointer;">
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

token = st.session_state.get("google_token")

if token:
    st.success("Google Login Successful! 🎉")
    st.write("### Here is your Firebase ID Token:")
    st.code(token)

    st.info("Next step: We will verify this token via Firebase and log the user in your app.")
else:
    st.info("Waiting for Google Login...")
