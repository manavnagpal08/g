import streamlit as st
import streamlit.components.v1 as components
import base64
import tempfile

st.set_page_config(page_title="Google Login Test", page_icon="🔐")

st.title("🔐 Google Login Test (Firebase - ScreenerPro)")
st.write("Click the button below to sign in with Google and retrieve your Firebase ID Token.")

# /////////////////////////////////
# FRONTEND HTML (Stored in temp file)
# /////////////////////////////////

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

<style>
button {
    padding: 14px 24px;
    background: #4285F4;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    cursor: pointer;
    font-weight: bold;
}
</style>

</head>
<body>
    <button onclick="googleLogin()">Sign in with Google</button>
</body>
</html>
"""

# Write HTML to a temporary file
with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as f:
    f.write(firebase_html)
    temp_file_path = f.name

# /////////////////////////////////
# IFRAME INSTEAD OF HTML COMPONENT
# /////////////////////////////////

components.iframe(
    src=f"file://{temp_file_path}",
    height=200,
)

# /////////////////////////////////
# CAPTURE TOKEN OR ERROR
# /////////////////////////////////

components.html(
    """
    <script>
    window.addEventListener("message", (event) => {
        const input = document.getElementById("tokenInput");
        input.value = event.data.token || event.data.error || "";
        input.dispatchEvent(new Event("change"));
    });
    </script>
    <input type="text" id="tokenInput" style="display:none;">
    """,
    height=0
)

def on_change():
    st.session_state["google_result"] = st.session_state["input_res"]

st.text_input("hidden", key="input_res", label_visibility="hidden", on_change=on_change)

# Output
st.write("---")

result = st.session_state.get("google_result")

if result:
    if "ey" in result:  # Firebase token always begins with "ey..."
        st.success("🎉 Google Login Successful!")
        st.code(result)
    else:
        st.error("❌ Login Failed: " + result)
else:
    st.info("Waiting for Google login...")
