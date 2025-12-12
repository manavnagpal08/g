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
    window.addEventListener("message", (event) => {
        if (event.data.token) {
            const tokenInput = document.getElementById("tokenInput");
            tokenInput.value = event.data.token;
            tokenInput.dispatchEvent(new Event("change"));
        }
        if (event.data.error) {
            const errInput = document.getElementById("errorInput");
            errInput.value = event.data.error;
            errInput.dispatchEvent(new Event("change"));
        }
    });
    </script>

    <input type="text" id="tokenInput" style="display:none;">
    <input type="text" id="errorInput" style="display:none;">
    """,
    height=0,
)

# Session update logic
def on_token_change():
    st.session_state["google_token"] = st.session_state["token_field"]

def on_error_change():
    st.session_state["google_error"] = st.session_state["error_field"]

st.text_input("hidden_token_field", key="token_field", label_visibility="hidden", on_change=on_token_change)
st.text_input("hidden_error_field", key="error_field", label_visibility="hidden", on_change=on_error_change)

# -------------------------------------------------
# GOOGLE LOGIN BUTTON (WITH POPUP FIX)
# -------------------------------------------------

firebase_html = """
<!DOCTYPE html>
<html>
<head>

<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js"></script>

<script>
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
      padding: 12px 22px;
      background:#4285F4;
      color:white;
      border:none;
      border-radius:8px;
      font-size:17px;
      cursor:pointer;
      font-weight:600;">
      🔵 Sign in with Google
  </button>
</body>
</html>
"""

components.html(
    firebase_html,
    height=260,
    width=350,
    scrolling=False,
    sandbox="allow-scripts allow-same-origin allow-popups allow-forms",
    allow="popup"
)

# -------------------------------------------------
# DISPLAY RESULT
# -------------------------------------------------
st.write("---")

if "google_error" in st.session_state and st.session_state["google_error"]:
    st.error("Google Login Failed:\n" + st.session_state["google_error"])

if "google_token" in st.session_state and st.session_state["google_token"]:
    st.success("🎉 Google Login Successful!")
    st.write("### Your Firebase ID Token:")
    st.code(st.session_state["google_token"])
else:
    st.info("Waiting for Google Login...")
