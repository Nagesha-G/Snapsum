import streamlit as st
import easyocr
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF
from datetime import datetime
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
import json

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
load_dotenv()

st.set_page_config(
    page_title="SnapSum",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# OCR language codes supported by EasyOCR (subset)
LANG_LABELS = {
    "en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil",
    "kn": "Kannada", "ml": "Malayalam", "mr": "Marathi", "bn": "Bengali",
    "gu": "Gujarati", "pa": "Punjabi", "ur": "Urdu",
    "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
    "pt": "Portuguese", "ru": "Russian", "ar": "Arabic",
    "ch_sim": "Chinese (Simplified)", "ja": "Japanese", "ko": "Korean",
}

# Output languages for translation/explanation
OUTPUT_LANGS = [
    "English", "Hindi", "Telugu", "Tamil", "Kannada", "Malayalam",
    "Marathi", "Bengali", "Gujarati", "Punjabi", "Urdu",
    "Spanish", "French", "German", "Italian", "Portuguese",
    "Russian", "Arabic", "Chinese", "Japanese", "Korean",
]

TRIAL_LIMIT = 10  # free uses per month

# ─────────────────────────────────────────────
# Clients
# ─────────────────────────────────────────────
@st.cache_resource
def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("❌ GROQ_API_KEY missing.")
        st.stop()
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

@st.cache_resource
def load_reader(langs_tuple):
    return easyocr.Reader(list(langs_tuple), gpu=False)

client = get_client()

# ─────────────────────────────────────────────
# Auth Setup
# ─────────────────────────────────────────────
CONFIG_FILE = "auth_config.yaml"

def load_auth_config():
    default = {
        "credentials": {"usernames": {}},
        "cookie": {
            "expiry_days": 30,
            "key": "snapsum_secret_key",
            "name": "snapsum_cookie",
        },
    }

    if not os.path.exists(CONFIG_FILE):
        return default

    try:
        with open(CONFIG_FILE) as f:
            loaded = yaml.load(f, Loader=SafeLoader)

        # If file is empty or malformed, fall back to default
        if not loaded or not isinstance(loaded, dict):
            return default

        # Ensure required keys exist
        if "credentials" not in loaded or "usernames" not in loaded.get("credentials", {}):
            loaded["credentials"] = {"usernames": {}}

        if "cookie" not in loaded:
            loaded["cookie"] = default["cookie"]

        return loaded
    except Exception as e:
        st.warning(f"Config load failed ({e}). Using fresh config.")
        return default

def save_auth_config(config):
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

auth_config = load_auth_config()

authenticator = stauth.Authenticate(
    auth_config["credentials"],
    auth_config["cookie"]["name"],
    auth_config["cookie"]["key"],
    auth_config["cookie"]["expiry_days"],
)

# ─────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "page": "home",
        "chats": {},  # {chat_id: {"title": str, "messages": []}}
        "current_chat": None,
        "usage_count": 0,
        "extracted_text": "",
        "uploaded_filename": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─────────────────────────────────────────────
# Helper: PDF
# ─────────────────────────────────────────────
def build_pdf(title, content, filename):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "SnapSum Report", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Source: {filename}", ln=True)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.ln(8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, content)
    return bytes(pdf.output())

# ─────────────────────────────────────────────
# Helper: Chat management
# ─────────────────────────────────────────────
def new_chat():
    chat_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    st.session_state.chats[chat_id] = {"title": "New chat", "messages": []}
    st.session_state.current_chat = chat_id
    return chat_id

def get_current_chat():
    if st.session_state.current_chat is None:
        new_chat()
    return st.session_state.chats[st.session_state.current_chat]

# ─────────────────────────────────────────────
# Sidebar: Logo + Auth + Navigation
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📸 SnapSum")
    st.caption("AI Screenshot Analyzer")
    st.divider()

    # Auth
    try:
        authenticator.login(location="sidebar")
    except Exception as e:
        st.error(e)

    auth_status = st.session_state.get("authentication_status")
    name = st.session_state.get("name")
    username = st.session_state.get("username")

    if auth_status is True:
        st.success(f"👤 {name or username}")

        # Usage counter (per session; reset on refresh)
        remaining = TRIAL_LIMIT - st.session_state.usage_count
        st.caption(f"Free uses remaining: **{remaining}/{TRIAL_LIMIT}**")

        authenticator.logout("Logout", "sidebar")

        st.divider()

        # Chat management
        st.markdown("**💬 Chats**")
        if st.button("➕ New chat", use_container_width=True):
            new_chat()
            st.rerun()

        for chat_id, chat in list(st.session_state.chats.items())[::-1]:
            label = chat["title"][:25] + ("..." if len(chat["title"]) > 25 else "")
            is_active = chat_id == st.session_state.current_chat
            if st.button(f"{'▶ ' if is_active else ''}{label}", key=chat_id, use_container_width=True):
                st.session_state.current_chat = chat_id
                st.rerun()

    elif auth_status is False:
        st.error("Username/password incorrect")
    else:
        st.warning("Please login to use SnapSum")

    st.divider()
    st.caption("v0.3 · Streamlit · EasyOCR · Groq")

# ─────────────────────────────────────────────
# Gate: Require login
# ─────────────────────────────────────────────
if st.session_state.get("authentication_status") is not True:
    # Registration form
    st.title("📸 SnapSum")
    st.subheader("Create your free account")
    st.caption(f"Free trial: {TRIAL_LIMIT} uses per month")

    with st.form("register_form"):
        new_name = st.text_input("Full name")
        new_email = st.text_input("Email")
        new_username = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Register", use_container_width=True)

        if submitted:
            if not all([new_name, new_email, new_username, new_password]):
                st.error("All fields are required.")
            elif new_username in auth_config["credentials"]["usernames"]:
                st.error("Username already exists.")
            else:
                hashed = stauth.Hasher.hash(new_password)
                auth_config["credentials"]["usernames"][new_username] = {
                    "email": new_email,
                    "name": new_name,
                    "password": hashed,
                }
                save_auth_config(auth_config)
                st.success("✅ Account created! Please login with your credentials in the sidebar.")
                st.balloons()

    st.info("👈 Already registered? Login in the sidebar.")
    st.stop()

# ─────────────────────────────────────────────
# Home Page
# ─────────────────────────────────────────────
if st.session_state.page == "home":
    st.title("📸 SnapSum")
    st.subheader("Turn screenshots into summaries, explanations, and answers.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🔍 Extract")
        st.caption("Pull text from any screenshot in English, Hindi, Telugu, Tamil, and more.")
    with col2:
        st.markdown("### 🤖 Understand")
        st.caption("AI explains what, why, and how — in your chosen language.")
    with col3:
        st.markdown("### 💬 Chat")
        st.caption("Ask questions about the image and get answers, with full chat history.")

    st.divider()

    if st.button("🚀 Get Started", type="primary", use_container_width=True):
        st.session_state.page = "workspace"
        st.rerun()

    st.stop()

# ─────────────────────────────────────────────
# Workspace Page
# ─────────────────────────────────────────────
st.title("📸 SnapSum Workspace")

# Language selector (before upload)
col_lang, col_spacer = st.columns([1, 2])
with col_lang:
    output_lang = st.selectbox(
        "Output Language",
        OUTPUT_LANGS,
        index=0,
        help="All summaries, explanations, and answers will be in this language.",
    )

# Upload
uploaded_file = st.file_uploader("Upload a screenshot", type=["png", "jpg", "jpeg"])

if not uploaded_file:
    st.info("👆 Upload a PNG or JPG to begin.")
    st.stop()

# Check trial limit
if st.session_state.usage_count >= TRIAL_LIMIT:
    st.error(f"❌ You've used all {TRIAL_LIMIT} free tries this month. Upgrade to continue.")
    st.stop()

# Process image
image = Image.open(uploaded_file)

col_left, col_right = st.columns([1, 1])

with col_left:
    st.image(image, caption="Uploaded Screenshot", use_container_width=True)

# OCR
with st.spinner("🔍 Extracting text..."):
    try:
        reader = load_reader(("en",))
        result = reader.readtext(uploaded_file.getvalue(), detail=0)
        extracted_text = " ".join(result).strip()
    except Exception as e:
        st.error(f"OCR failed: {e}")
        st.stop()

if not extracted_text:
    st.warning("⚠️ No text found. Try a clearer screenshot.")
    st.stop()

st.session_state.extracted_text = extracted_text
st.session_state.uploaded_filename = uploaded_file.name

with col_right:
    st.subheader("📝 Extracted Text")
    st.text_area("Extracted", extracted_text, height=250, label_visibility="collapsed")
    st.caption(f"{len(extracted_text)} chars · {len(extracted_text.split())} words")

# ── Translate button (next to extracted text) ──
if st.button("🌐 Translate Extracted Text"):
    with st.spinner(f"Translating to {output_lang}..."):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"You are a translator. Translate the user's text into {output_lang}. Return only the translation, no explanations."},
                    {"role": "user", "content": extracted_text},
                ],
                temperature=0.1,
            )
            translation = resp.choices[0].message.content
            st.session_state.usage_count += 1
            st.subheader(f"🌐 Translation ({output_lang})")
            st.write(translation)
            st.download_button(
                "⬇️ Download translation (.txt)",
                data=translation,
                file_name=f"snapsum_translation_{output_lang}.txt",
            )
        except Exception as e:
            st.error(f"Translation failed: {e}")

st.divider()

# ── Summarize ──
if st.button("✨ Summarize", type="primary", use_container_width=True):
    with st.spinner(f"Summarizing in {output_lang}..."):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"Summarize the text in 3 bullet points. Write in {output_lang}."},
                    {"role": "user", "content": extracted_text},
                ],
                temperature=0.3,
            )
            summary = resp.choices[0].message.content
            st.session_state.usage_count += 1
            st.subheader("📌 Summary")
            st.markdown(summary)

            col_txt, col_pdf = st.columns(2)
            with col_txt:
                st.download_button("⬇️ Download .txt", data=summary, file_name="snapsum_summary.txt")
            with col_pdf:
                st.download_button("📄 Download PDF", data=build_pdf("Summary", summary, uploaded_file.name), file_name="snapsum_summary.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Summarization failed: {e}")

# ── Explain (what/why/how) ──
if st.button("🧠 Explain (What / Why / How)", use_container_width=True):
    with st.spinner(f"Explaining in {output_lang}..."):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"You are an explainer. For the given text, explain in {output_lang}: WHAT it is, WHY it matters, and HOW it's structured. Keep it simple and beginner-friendly."},
                    {"role": "user", "content": extracted_text},
                ],
                temperature=0.4,
            )
            explanation = resp.choices[0].message.content
            st.session_state.usage_count += 1
            st.subheader("🧠 Explanation")
            st.markdown(explanation)
            st.download_button("⬇️ Download explanation (.txt)", data=explanation, file_name="snapsum_explanation.txt")
        except Exception as e:
            st.error(f"Explanation failed: {e}")

st.divider()

# ─────────────────────────────────────────────
# Chat Section (below the workspace)
# ─────────────────────────────────────────────
st.subheader("💬 Ask about this image")

if st.session_state.current_chat is None:
    new_chat()

current = get_current_chat()

# Display chat history
for msg in current["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
prompt = st.chat_input("Ask a question about the image...")

if prompt:
    # Add user message
    with st.chat_message("user"):
        st.markdown(prompt)
    current["messages"].append({"role": "user", "content": prompt})

    # Set chat title on first message
    if current["title"] == "New chat":
        current["title"] = prompt[:30]

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": f"Answer based on this image text. Reply in {output_lang}. If not present, say 'Not found in image.'\n\nTEXT:\n{st.session_state.extracted_text}"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                answer = resp.choices[0].message.content
                st.markdown(answer)
                current["messages"].append({"role": "assistant", "content": answer})
                st.session_state.usage_count += 1
            except Exception as e:
                st.error(f"Q&A failed: {e}")

# Footer
st.divider()
st.caption("SnapSum v0.3 · Built with Streamlit + EasyOCR + Groq")