"""
SnapSum v4.2 — Full-stack single-file app.
FastAPI backend + HTML/CSS/JS frontend in one file.

Run:
    uvicorn app:app --reload --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import easyocr
from PIL import Image
import io
import os
import json
import hashlib
import secrets
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

SUPPORT_UPI = os.getenv("SUPPORT_UPI", "n4ge5h4@okaxis")
SUPPORT_NAME = os.getenv("SUPPORT_NAME", "Nagesha G")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "iamnagesha3871@gmail.com")

FREE_TIER_LIMIT = 25

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY missing. Add it to .env")

llm = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

USERS_FILE = "users.json"
CHATS_FILE = "chats.json"
ANALYTICS_FILE = "analytics.json"
_reader = None


def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_users(): return _load_json(USERS_FILE, {})
def save_users(u): _save_json(USERS_FILE, u)
def load_chats(): return _load_json(CHATS_FILE, {})
def save_chats(c): _save_json(CHATS_FILE, c)
def load_analytics(): return _load_json(ANALYTICS_FILE, {"page_views": 0})
def save_analytics(a): _save_json(ANALYTICS_FILE, a)


def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()


SESSIONS = {}


def call_llm(system, user, temperature=0.3):
    resp = llm.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return resp.choices[0].message.content


def current_user(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return SESSIONS.get(auth.split(" ", 1)[1])


def get_user_record(username):
    users = load_users()
    return users.get(username)


def increment_usage(username):
    users = load_users()
    if username in users:
        users[username]["uses"] = users[username].get("uses", 0) + 1
        save_users(users)


def check_usage(username):
    user = get_user_record(username)
    if not user:
        return False, 0
    used = user.get("uses", 0)
    remaining = max(0, FREE_TIER_LIMIT - used)
    return remaining > 0, remaining


app = FastAPI(title="SnapSum")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ═════════════════════════════════════════════
# CSS
# ═════════════════════════════════════════════
CSS = """
:root {
  --primary: #6366F1;
  --primary-hover: #4F46E5;
  --primary-light: #EEF2FF;
  --success: #10B981;
  --warning: #F59E0B;
  --error: #EF4444;
  --bg: #FFFFFF;
  --surface: #F8FAFC;
  --border: #E2E8F0;
  --text: #0F172A;
  --muted: #64748B;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; -webkit-font-smoothing: antialiased; }
img { max-width: 100%; height: auto; display: block; }
button { font-family: inherit; cursor: pointer; border: none; border-radius: 10px; padding: 10px 18px; font-weight: 600; font-size: 14px; transition: all 0.2s ease; }
input, textarea, select { font-family: inherit; font-size: 14px; }

.btn-primary { background: var(--primary); color: white; box-shadow: 0 1px 2px rgba(15,23,42,0.08); }
.btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99,102,241,0.28); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.btn-secondary { background: var(--surface); color: var(--text); border: 1px solid var(--border); }
.btn-secondary:hover { background: var(--primary-light); border-color: var(--primary); color: var(--primary-hover); }
.btn-ghost { background: transparent; color: var(--muted); padding: 6px 12px; }
.btn-ghost:hover { color: var(--primary); }
.btn-danger { background: var(--error); color: white; }
.btn-danger:hover { background: #DC2626; }
.btn-icon { background: transparent; border: 1px solid var(--border); color: var(--muted); padding: 6px 10px; font-size: 12px; border-radius: 8px; display: inline-flex; align-items: center; gap: 4px; }
.btn-icon:hover { background: var(--surface); color: var(--primary); border-color: var(--primary); }
.btn-icon.coming-soon { opacity: 0.55; cursor: not-allowed; }
.btn-quick { background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 7px 14px; font-size: 13px; border-radius: 20px; white-space: nowrap; }
.btn-quick:hover { background: var(--primary-light); border-color: var(--primary); color: var(--primary-hover); }

/* Navbar */
.navbar { display: flex; justify-content: space-between; align-items: center; padding: 14px 28px; border-bottom: 1px solid var(--border); background: var(--bg); position: sticky; top: 0; z-index: 100; flex-wrap: wrap; gap: 12px; }
.navbar .logo { font-weight: 800; font-size: 18px; white-space: nowrap; }
.navbar nav { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.navbar nav a:not(.btn-primary), .navbar nav button:not(.btn-primary):not(.btn-ghost) {
  padding: 8px 14px; border-radius: 8px; font-size: 14px; font-weight: 500;
  color: var(--muted); background: transparent; text-decoration: none; white-space: nowrap;
}
.navbar nav a:not(.btn-primary):hover, .navbar nav button:not(.btn-primary):hover { background: var(--surface); color: var(--text); }
.navbar nav a.active { background: var(--primary-light); color: var(--primary-hover); font-weight: 600; }
.navbar nav a.login-btn { background: var(--primary) !important; color: white !important; padding: 9px 20px !important; border-radius: 10px !important; font-weight: 600 !important; box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important; }
.navbar nav a.login-btn:hover { background: var(--primary-hover) !important; transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99,102,241,0.4) !important; }
.navbar .nav-help { color: var(--primary) !important; font-weight: 600 !important; }
.user-pill { display: flex; align-items: center; gap: 8px; padding: 6px 12px; background: var(--surface); border-radius: 20px; font-size: 13px; color: var(--text); }
.avatar { width: 26px; height: 26px; border-radius: 50%; object-fit: cover; border: 2px solid var(--primary); }
.avatar-initials { width: 26px; height: 26px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; }
.usage-badge { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; background: var(--primary-light); color: var(--primary-hover); border-radius: 12px; font-size: 12px; font-weight: 600; }
.usage-badge.low { background: #FEF3C7; color: #92400E; }
.usage-badge.empty { background: #FEE2E2; color: #991B1B; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.45;} }

.container { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }

/* Hero */
.hero { text-align: center; padding: 60px 24px; background: linear-gradient(135deg, #EEF2FF 0%, #FFFFFF 45%, #F0F9FF 100%); background-size: 200% 200%; border-radius: 20px; margin-bottom: 40px; border: 1px solid var(--border); animation: gradientShift 15s ease infinite; }
.hero h1 { font-size: clamp(28px, 5vw, 44px); margin-bottom: 12px; background: linear-gradient(135deg, var(--primary) 0%, #8B5CF6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-weight: 800; letter-spacing: -0.02em; }
.hero p { color: var(--muted); font-size: clamp(15px, 2vw, 18px); max-width: 620px; margin: 0 auto 28px; }
.hero .cta { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
@keyframes gradientShift { 0%{background-position:0% 50%;} 50%{background-position:100% 50%;} 100%{background-position:0% 50%;} }

.stats-row { display: flex; gap: 16px; justify-content: center; margin-top: 28px; flex-wrap: wrap; }
.stat-box { background: white; border: 1px solid var(--border); border-radius: 12px; padding: 14px 22px; text-align: center; }
.stat-box .num { font-size: 24px; font-weight: 800; color: var(--primary); display: block; }
.stat-box .label { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }

.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; margin-top: 20px; }
.card { background: var(--bg); border: 1px solid var(--border); border-radius: 14px; padding: 22px; transition: all 0.25s ease; animation: fadeIn 0.5s ease forwards; }
.card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px rgba(15,23,42,0.08); border-color: var(--primary); }
.card h3 { font-size: 17px; margin-bottom: 8px; }
.card p { color: var(--muted); font-size: 14px; line-height: 1.6; }
@keyframes fadeIn { from{opacity:0;transform:translateY(8px);} to{opacity:1;transform:translateY(0);} }
.section-title { font-size: 22px; font-weight: 700; margin: 32px 0 16px; letter-spacing: -0.01em; }

.info-banner { display: flex; align-items: center; gap: 10px; padding: 12px 16px; margin-bottom: 20px; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; font-size: 13px; color: #92400E; line-height: 1.5; }
.info-banner.danger { background: #FEF2F2; border-color: #FECACA; color: #991B1B; }
.info-banner .icon { font-size: 16px; flex-shrink: 0; }

/* Auth */
.auth-wrap { max-width: 420px; margin: 60px auto; background: var(--bg); border: 1px solid var(--border); border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(15,23,42,0.05); }
.auth-wrap h2 { margin-bottom: 20px; font-size: 22px; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; background: var(--surface); padding: 4px; border-radius: 10px; }
.tab { flex: 1; padding: 8px; border-radius: 8px; background: transparent; color: var(--muted); font-weight: 600; }
.tab.active { background: var(--bg); color: var(--primary); box-shadow: 0 1px 3px rgba(15,23,42,0.06); }
input, textarea, select { width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--bg); color: var(--text); transition: all 0.15s ease; margin-bottom: 12px; }
input:focus, textarea:focus, select:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }
label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.msg { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; }
.msg.error { background:#FEF2F2; color:var(--error); border:1px solid #FECACA; }
.msg.success { background:#F0FDF4; color:var(--success); border:1px solid #BBF7D0; }
.msg.info { background:var(--primary-light); color:var(--primary-hover); border:1px solid #C7D2FE; }

/* Workspace */
.workspace-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; align-items: start; }
@media (max-width: 900px) { .workspace-grid { grid-template-columns: 1fr; } }
.panel { background: var(--bg); border: 1px solid var(--border); border-radius: 14px; padding: 20px; }
.panel h3 { margin-bottom: 14px; font-size: 16px; display: flex; align-items: center; justify-content: space-between; }
.panel h3 .panel-actions { display: flex; gap: 6px; }
.img-preview { max-width: 100%; max-height: 340px; width: auto; margin: 0 auto 14px; border-radius: 10px; border: 1px solid var(--border); object-fit: contain; }
.text-preview { background: var(--surface); padding: 12px; border-radius: 8px; font-size: 13px; max-height: 260px; overflow-y: auto; white-space: pre-wrap; line-height: 1.55; border: 1px solid var(--border); }
.text-meta { color: var(--muted); font-size: 12px; margin-top: 8px; display: flex; gap: 12px; }

.lang-bar { display: flex; gap: 16px; align-items: center; margin-bottom: 20px; flex-wrap: wrap; padding: 14px 18px; background: var(--surface); border: 1px solid var(--border); border-radius: 12px; }
.lang-bar .group { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.lang-bar label { margin: 0; font-size: 13px; color: var(--muted); }
.lang-bar select { width: auto; min-width: 150px; margin-bottom: 0; padding: 8px 12px; font-size: 13px; }

/* Upload progress */
.upload-progress { display: flex; flex-direction: column; gap: 14px; padding: 28px 24px; text-align: center; background: var(--surface); border-radius: 14px; border: 1px solid var(--border); }
.upload-progress .title { font-size: 15px; font-weight: 700; }
.upload-progress .subtitle { font-size: 13px; color: var(--muted); }
.progress-bar { width: 100%; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; width: 0%; background: linear-gradient(90deg, var(--primary), #8B5CF6); border-radius: 4px; transition: width 0.3s ease; }
.progress-steps { display: flex; flex-direction: column; gap: 8px; text-align: left; font-size: 13px; }
.progress-step { display: flex; align-items: center; gap: 8px; color: var(--muted); }
.progress-step.active { color: var(--primary); font-weight: 600; }
.progress-step.done { color: var(--success); }
.step-icon { width: 18px; height: 18px; border-radius: 50%; flex-shrink: 0; border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 10px; }
.progress-step.active .step-icon { border-color: var(--primary); border-top-color: transparent; animation: spin 0.8s linear infinite; }
.progress-step.done .step-icon { background: var(--success); border-color: var(--success); color: white; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Chat */
.chat-box { border: 1px solid var(--border); border-radius: 14px; padding: 20px; background: var(--bg); display: flex; flex-direction: column; min-height: 600px; }
.chat-header { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.chat-header h3 { font-size: 16px; margin-right: auto; }
.chat-select { flex: 1; min-width: 140px; max-width: 220px; margin-bottom: 0; padding: 7px 10px; font-size: 13px; }
.quick-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid var(--border); }
.quick-actions .label { font-size: 12px; color: var(--muted); align-self: center; margin-right: 4px; }
.chat-messages { flex: 1; min-height: 340px; max-height: 520px; overflow-y: auto; margin-bottom: 12px; padding-right: 4px; display: flex; flex-direction: column; gap: 10px; }
.chat-msg { padding: 12px 16px; border-radius: 14px; max-width: 88%; font-size: 14px; line-height: 1.6; animation: slideIn 0.3s ease forwards; position: relative; word-wrap: break-word; overflow-wrap: break-word; }
.chat-msg.user { background: var(--primary-light); color: var(--primary-hover); margin-left: auto; border-bottom-right-radius: 4px; }
.chat-msg.assistant { background: var(--surface); border: 1px solid var(--border); border-bottom-left-radius: 4px; }
.chat-msg.system { background: #FFF7ED; border: 1px solid #FED7AA; color: #9A3412; font-size: 13px; max-width: 100%; text-align: center; font-weight: 500; }
.chat-msg.assistant p { margin: 0 0 8px 0; }
.chat-msg.assistant p:last-child { margin-bottom: 0; }
.chat-msg.assistant ul, .chat-msg.assistant ol { margin: 6px 0 8px 20px; }
.chat-msg.assistant li { margin-bottom: 4px; }
.chat-msg.assistant strong { font-weight: 700; color: var(--text); }
.chat-msg.assistant code { background: rgba(99,102,241,0.1); padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; font-size: 13px; }
.chat-msg.assistant pre { background: #0F172A; color: #E2E8F0; padding: 10px 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; font-size: 12.5px; }

.copy-btn { position: absolute; top: 8px; right: 8px; background: rgba(255,255,255,0.9); border: 1px solid var(--border); color: var(--muted); padding: 3px 8px; font-size: 11px; border-radius: 6px; opacity: 0; transition: all 0.15s ease; cursor: pointer; font-weight: 600; }
.chat-msg.assistant:hover .copy-btn { opacity: 1; }
.copy-btn:hover { background: var(--primary-light); color: var(--primary); border-color: var(--primary); }
.copy-btn.copied { background: var(--success); color: white; border-color: var(--success); }

.typing { display: inline-flex; gap: 4px; align-items: center; padding: 4px 0; }
.typing span { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; animation: typingDot 1.2s infinite; }
.typing span:nth-child(2) { animation-delay: 0.15s; }
.typing span:nth-child(3) { animation-delay: 0.3s; }
@keyframes typingDot { 0%, 60%, 100% { transform: translateY(0); opacity: 0.4; } 30% { transform: translateY(-6px); opacity: 1; } }

.chat-input-row { display: flex; gap: 10px; }
.chat-input-row input { margin-bottom: 0; }
@keyframes slideIn { from{opacity:0;transform:translateX(-8px);} to{opacity:1;transform:translateX(0);} }

.inline-form { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin: 8px 0; }
.inline-form label { font-size: 12px; margin-bottom: 4px; }
.inline-form select { margin-bottom: 10px; font-size: 13px; padding: 8px 10px; }
.inline-form .btn-row { display: flex; gap: 8px; margin-top: 4px; }
.inline-form .btn-row button { flex: 1; padding: 8px 14px; font-size: 13px; }
.inline-form .cancel-btn { background: transparent; border: 1px solid var(--border); color: var(--muted); }
.inline-form .cancel-btn:hover { background: var(--bg); color: var(--error); border-color: var(--error); }

.inline-confirm { background: #FEF2F2; border: 1px solid #FECACA; border-radius: 12px; padding: 14px; margin: 10px 0; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.inline-confirm .text { font-size: 13px; color: #991B1B; font-weight: 500; flex: 1; min-width: 200px; }
.inline-confirm .btns { display: flex; gap: 8px; }
.inline-confirm button { padding: 7px 14px; font-size: 13px; }
.inline-confirm .yes-btn { background: var(--error); color: white; }
.inline-confirm .yes-btn:hover { background: #DC2626; }
.inline-confirm .no-btn { background: transparent; border: 1px solid #FECACA; color: #991B1B; }

.drop { border: 2px dashed var(--border); border-radius: 14px; padding: 32px; text-align: center; background: var(--surface); cursor: pointer; transition: all 0.2s ease; }
.drop:hover, .drop.over { border-color: var(--primary); background: var(--primary-light); }
.drop p { color: var(--muted); font-size: 14px; }
.drop small { color: var(--muted); font-size: 12px; display: block; margin-top: 6px; }

.toast-container { position: fixed; top: 80px; right: 24px; z-index: 9999; display: flex; flex-direction: column; gap: 10px; pointer-events: none; }
.toast { padding: 12px 18px; border-radius: 10px; font-size: 14px; font-weight: 500; box-shadow: 0 4px 16px rgba(15,23,42,0.12); animation: toastIn 0.3s ease forwards; pointer-events: auto; max-width: 320px; }
.toast.success { background: #F0FDF4; color: var(--success); border: 1px solid #BBF7D0; }
.toast.error { background: #FEF2F2; color: var(--error); border: 1px solid #FECACA; }
.toast.info { background: var(--primary-light); color: var(--primary-hover); border: 1px solid #C7D2FE; }
.toast.leaving { animation: toastOut 0.3s ease forwards; }
@keyframes toastIn { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
@keyframes toastOut { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(40px); } }

.support-hero { text-align: center; padding: 40px 24px; background: linear-gradient(135deg, #FEF3C7 0%, #FFFFFF 50%, #FCE7F3 100%); border-radius: 20px; margin-bottom: 32px; border: 1px solid var(--border); }
.support-hero h1 { font-size: 32px; margin-bottom: 10px; font-weight: 800; background: linear-gradient(135deg, #F59E0B 0%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.support-hero p { color: var(--muted); max-width: 540px; margin: 0 auto; font-size: 15px; }
.support-card { background: var(--bg); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
.support-card h3 { margin-bottom: 12px; font-size: 17px; }
.support-card p { color: var(--muted); font-size: 14px; margin-bottom: 14px; }
.amount-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 10px; margin-bottom: 16px; }
.amount-btn { background: var(--surface); border: 2px solid var(--border); color: var(--text); padding: 14px 8px; font-size: 15px; font-weight: 700; border-radius: 12px; cursor: pointer; transition: all 0.2s ease; }
.amount-btn:hover { background: var(--primary-light); border-color: var(--primary); color: var(--primary-hover); }
.amount-btn.selected { background: var(--primary); border-color: var(--primary); color: white; }
.amount-btn.tiny { font-size: 14px; }
.upi-box { display: flex; align-items: center; gap: 12px; padding: 14px 18px; background: var(--surface); border-radius: 12px; border: 1px solid var(--border); margin-bottom: 12px; flex-wrap: wrap; }
.upi-id { font-family: 'Consolas', monospace; font-size: 15px; font-weight: 600; color: var(--primary-hover); flex: 1; word-break: break-all; }
.copy-upi-btn { background: var(--primary); color: white; padding: 8px 14px; font-size: 13px; border-radius: 8px; font-weight: 600; }
.copy-upi-btn:hover { background: var(--primary-hover); }
.copy-upi-btn.copied { background: var(--success); }
.support-note { font-size: 13px; color: var(--muted); text-align: center; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border); }

.settings-section { background: var(--bg); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin-bottom: 20px; max-width: 640px; }
.settings-section h3 { margin-bottom: 14px; font-size: 17px; }
.settings-section p { color: var(--muted); font-size: 14px; margin-bottom: 12px; }
.avatar-upload { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.avatar-large { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid var(--primary); }
.avatar-large-initials { width: 80px; height: 80px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 700; }
.danger-zone { border-color: #FECACA; background: #FEF2F2; }
.danger-zone h3 { color: #991B1B; }
.usage-meter { display: flex; align-items: center; gap: 12px; margin: 10px 0; }
.usage-meter-bar { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.usage-meter-fill { height: 100%; background: var(--primary); border-radius: 4px; transition: width 0.3s ease; }
.usage-meter-fill.low { background: var(--warning); }
.usage-meter-fill.empty { background: var(--error); }

.hidden { display: none !important; }

@media (max-width: 640px) {
  .container { padding: 20px 16px; }
  .navbar { padding: 12px 16px; }
  .hero { padding: 40px 16px; }
  .hero h1 { font-size: 28px; }
  .panel { padding: 16px; }
  .chat-messages { min-height: 240px; }
  .img-preview { max-height: 220px; }
  .card { padding: 18px; }
  .lang-bar { padding: 12px; gap: 10px; }
  .lang-bar select { min-width: 120px; }
  .quick-actions { gap: 6px; }
  .btn-quick { padding: 6px 10px; font-size: 12px; }
  .chat-header h3 { font-size: 15px; width: 100%; }
  .chat-select { max-width: 100%; }
  .toast-container { top: 70px; right: 12px; left: 12px; }
  .toast { max-width: 100%; }
  .support-hero h1 { font-size: 24px; }
  .amount-grid { grid-template-columns: repeat(3, 1fr); }
  .amount-btn { padding: 12px 6px; font-size: 13px; }
}
"""


# ═════════════════════════════════════════════
# JS
# ═════════════════════════════════════════════
JS = """
// ── Session-based auth (clears on tab close) ──
// Use sessionStorage so login disappears when the tab closes.
// Fallback: clear localStorage token if it exists (migration from older version).

// Migration: if an old localStorage token exists, delete it — we now use sessionStorage.
["snapsum_token","snapsum_user"].forEach(k => localStorage.removeItem(k));

const state = {
  token: sessionStorage.getItem("snapsum_token") || null,
  username: sessionStorage.getItem("snapsum_user") || null,
  outputLang: localStorage.getItem("snapsum_outlang") || "English",
  inputLang: localStorage.getItem("snapsum_inlang") || "English",
  extractedText: sessionStorage.getItem("snapsum_extracted") || "",
  imageDataUrl: sessionStorage.getItem("snapsum_image") || "",
  chats: [],
  currentChatId: null,
  selectedAmount: 10,
  avatar: null,
  uses: 0,
  limit: 25,
};
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

function showToast(text, kind = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `toast ${kind}`;
  toast.textContent = text;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("leaving");
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

function setToken(token, username) {
  state.token = token; state.username = username;
  if (token) {
    sessionStorage.setItem("snapsum_token", token);
    sessionStorage.setItem("snapsum_user", username);
  } else {
    sessionStorage.removeItem("snapsum_token");
    sessionStorage.removeItem("snapsum_user");
  }
}

function saveLangs() {
  localStorage.setItem("snapsum_outlang", state.outputLang);
  localStorage.setItem("snapsum_inlang", state.inputLang);
}

function saveWorkspace(text, imageDataUrl) {
  if (text) try { sessionStorage.setItem("snapsum_extracted", text); } catch (e) {}
  if (imageDataUrl) try { sessionStorage.setItem("snapsum_image", imageDataUrl); } catch (e) {}
}

function clearWorkspace() {
  sessionStorage.removeItem("snapsum_extracted");
  sessionStorage.removeItem("snapsum_image");
  state.extractedText = "";
  state.imageDataUrl = "";
}

async function api(path, opts = {}) {
  const headers = opts.headers || {};
  if (state.token) headers["Authorization"] = "Bearer " + state.token;
  const res = await fetch(path, { ...opts, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    if (res.status === 401) {
      // Session expired on server — clear and bounce to login
      setToken(null, null);
    }
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;",
  }[c]));
}

function renderMarkdown(text) {
  if (typeof marked === "undefined") return escapeHtml(text);
  try { return marked.parse(text); } catch (e) { return escapeHtml(text); }
}

function initials(name) {
  if (!name) return "?";
  return name.split(/\\s+/).map(p => p[0]).join("").slice(0, 2).toUpperCase();
}

function usageBadgeHtml() {
  const remaining = Math.max(0, state.limit - state.uses);
  let cls = "usage-badge";
  if (remaining === 0) cls += " empty";
  else if (remaining <= 5) cls += " low";
  return `<span class="${cls}">${remaining}/${state.limit} uses</span>`;
}

function renderNavbar() {
  const nav = $("#navbar");
  if (!nav) return;
  const path = location.pathname;
  let userPill = "";
  let usageHtml = "";
  if (state.username) {
    const avatarHtml = state.avatar
      ? `<img src="${state.avatar}" class="avatar" alt="avatar" />`
      : `<div class="avatar-initials">${initials(state.username)}</div>`;
    userPill = `<span class="user-pill"><span class="dot"></span>${avatarHtml}${escapeHtml(state.username)}</span>`;
    usageHtml = usageBadgeHtml();
  }
  nav.innerHTML = `
    <div class="logo">📸 SnapSum</div>
    <nav>
      <a href="/" class="${path === "/" ? "active" : ""}">Home</a>
      ${state.token ? `<a href="/workspace" class="${path === "/workspace" ? "active" : ""}">Workspace</a>` : ""}
      ${state.token ? `<a href="/settings" class="${path === "/settings" ? "active" : ""}">Settings</a>` : ""}
      <a href="/support" class="nav-help ${path === "/support" ? "active" : ""}">💛 Support</a>
      ${usageHtml}
      ${state.token
        ? `<button onclick="logout()" class="btn-ghost">Logout</button>`
        : `<a href="/login" class="login-btn">Login</a>`}
      ${userPill}
    </nav>`;
  if (state.token) fetchAccount();
}

async function fetchAccount() {
  try {
    const data = await api("/api/account");
    let changed = false;
    if (data.avatar !== state.avatar) { state.avatar = data.avatar; changed = true; }
    if (typeof data.uses === "number" && data.uses !== state.uses) { state.uses = data.uses; changed = true; }
    if (typeof data.limit === "number" && data.limit !== state.limit) state.limit = data.limit;
    if (changed) renderNavbar();
  } catch (e) {}
}

function logout() {
  setToken(null, null);
  clearWorkspace();
  location.href = "/";
}

// ── Home ──
function initHome() {
  renderNavbar();
  if (!sessionStorage.getItem("snapsum_viewed")) {
    sessionStorage.setItem("snapsum_viewed", "1");
    api("/api/analytics/view", { method: "POST" }).catch(() => {});
  }
  loadStats();
  const ctaStart = $("#cta-start");
  const ctaLogin = $("#cta-login");
  const ctaWorkspace = $("#cta-workspace");
  if (state.token) {
    if (ctaStart) ctaStart.classList.add("hidden");
    if (ctaLogin) ctaLogin.classList.add("hidden");
    if (ctaWorkspace) ctaWorkspace.classList.remove("hidden");
  } else {
    if (ctaWorkspace) ctaWorkspace.classList.add("hidden");
  }
  if (ctaStart) ctaStart.onclick = () => { location.href = state.token ? "/workspace" : "/login"; };
  if (ctaWorkspace) ctaWorkspace.onclick = () => { location.href = "/workspace"; };
}

async function loadStats() {
  try {
    const data = await fetch("/api/analytics/stats").then(r => r.json());
    const pv = $("#stat-views");
    const us = $("#stat-users");
    if (pv) pv.textContent = (data.page_views || 0).toLocaleString();
    if (us) us.textContent = (data.total_users || 0).toLocaleString();
  } catch (e) {}
}

// ── Login ──
function initLogin() {
  renderNavbar();
  if (state.token) { location.href = "/workspace"; return; }
  const tabs = $$(".tab");
  const loginForm = $("#login-form");
  const registerForm = $("#register-form");
  tabs[0].onclick = () => {
    tabs[0].classList.add("active"); tabs[1].classList.remove("active");
    loginForm.classList.remove("hidden"); registerForm.classList.add("hidden");
  };
  tabs[1].onclick = () => {
    tabs[1].classList.add("active"); tabs[0].classList.remove("active");
    registerForm.classList.remove("hidden"); loginForm.classList.add("hidden");
  };
  loginForm.onsubmit = async (e) => {
    e.preventDefault();
    const msg = $("#login-msg");
    msg.className = "msg info"; msg.textContent = "Logging in...";
    msg.classList.remove("hidden");
    try {
      const data = await api("/api/login", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: $("#login-username").value,
          password: $("#login-password").value,
        }),
      });
      setToken(data.token, data.username);
      location.href = "/workspace";
    } catch (err) {
      msg.className = "msg error"; msg.textContent = err.message;
    }
  };
  registerForm.onsubmit = async (e) => {
    e.preventDefault();
    const msg = $("#register-msg");
    msg.className = "msg info"; msg.textContent = "Creating account...";
    msg.classList.remove("hidden");
    try {
      await api("/api/register", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: $("#reg-name").value, email: $("#reg-email").value,
          username: $("#reg-username").value, password: $("#reg-password").value,
        }),
      });
      msg.className = "msg success";
      msg.textContent = "Account created. Please login.";
      showToast("Account created", "success");
    } catch (err) {
      msg.className = "msg error"; msg.textContent = err.message;
    }
  };
}

// ── Workspace ──
function initWorkspace() {
  renderNavbar();
  if (!state.token) { location.href = "/"; return; }

  const outSel = $("#output-lang");
  const inSel = $("#input-lang");
  outSel.value = state.outputLang;
  inSel.value = state.inputLang;
  outSel.onchange = (e) => { state.outputLang = e.target.value; saveLangs(); };
  inSel.onchange = (e) => { state.inputLang = e.target.value; saveLangs(); };

  const drop = $("#drop");
  const fileInput = $("#file-input");
  drop.onclick = () => fileInput.click();
  drop.ondragover = (e) => { e.preventDefault(); drop.classList.add("over"); };
  drop.ondragleave = () => drop.classList.remove("over");
  drop.ondrop = (e) => {
    e.preventDefault(); drop.classList.remove("over");
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  };
  fileInput.onchange = () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); };

  $("#chat-send").onclick = () => {
    const input = $("#chat-input");
    sendChat(input.value, "user");
    input.value = "";
  };
  $("#chat-input").onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat(e.target.value, "user");
      e.target.value = "";
    }
  };
  $$(".btn-quick").forEach((btn) => {
    btn.onclick = () => runQuickAction(btn.dataset.action);
  });
  $("#new-chat-btn").onclick = () => createNewChat(true);
  $("#clear-chat-btn").onclick = () => showClearConfirm();
  $("#download-chat-btn").onclick = () => downloadCurrentChat();
  $("#chat-selector").onchange = (e) => selectChat(e.target.value);
  $("#voice-btn").onclick = () => showToast("🎤 Voice assistant coming soon!", "info");

  // New: reset button
  const resetBtn = $("#reset-workspace-btn");
  if (resetBtn) resetBtn.onclick = () => resetWorkspace();

  // New: copy extracted text
  const copyTextBtn = $("#copy-text-btn");
  if (copyTextBtn) copyTextBtn.onclick = () => copyExtractedText(copyTextBtn);

  // Keyboard shortcut: Ctrl+K focuses chat input
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "k") {
      e.preventDefault();
      const ci = $("#chat-input");
      if (ci) ci.focus();
    }
  });

  restoreWorkspace();
  loadChats();
  updateWorkspaceLock();
}

function resetWorkspace() {
  clearWorkspace();
  state.file = null;
  $("#workspace-content").classList.add("hidden");
  $("#chat-section").classList.add("hidden");
  $("#upload-progress").classList.add("hidden");
  $("#drop").classList.remove("hidden");
  $("#img-preview").classList.add("hidden");
  $("#img-preview").src = "";
  $("#text-preview").textContent = "No text yet.";
  $("#text-meta").textContent = "";
  $("#file-input").value = "";
  renderMessages([]);
  showToast("Workspace reset", "success");
}

function copyExtractedText(btn) {
  if (!state.extractedText) { showToast("No text to copy", "info"); return; }
  navigator.clipboard.writeText(state.extractedText).then(() => {
    const orig = btn.textContent;
    btn.textContent = "✓";
    setTimeout(() => btn.textContent = orig, 1200);
    showToast("Text copied", "success");
  });
}

async function updateWorkspaceLock() {
  await fetchAccount();
  const remaining = Math.max(0, state.limit - state.uses);
  const banner = $("#limit-banner");
  const input = $("#chat-input");
  const sendBtn = $("#chat-send");
  if (remaining === 0) {
    if (banner) banner.classList.remove("hidden");
    if (input) { input.disabled = true; input.placeholder = "Limit reached — create a new account to continue"; }
    if (sendBtn) sendBtn.disabled = true;
    $$(".btn-quick").forEach((b) => b.disabled = true);
  }
}

function restoreWorkspace() {
  if (state.extractedText) {
    const preview = $("#img-preview");
    if (state.imageDataUrl) {
      preview.src = state.imageDataUrl;
      preview.classList.remove("hidden");
    }
    $("#drop").classList.add("hidden");
    $("#text-preview").textContent = state.extractedText || "(no text found)";
    updateTextMeta();
    $("#workspace-content").classList.remove("hidden");
    $("#chat-section").classList.remove("hidden");
    showToast("Previous session restored", "info");
  }
}

function updateTextMeta() {
  const t = state.extractedText || "";
  const chars = t.length;
  const words = t.trim() ? t.trim().split(/\\s+/).length : 0;
  $("#text-meta").innerHTML = `<span>${chars} characters</span><span>${words} words</span>`;
}

function showUploadProgress() {
  $("#drop").classList.add("hidden");
  $("#upload-progress").classList.remove("hidden");
  setProgressStep("upload", "active");
  setProgressStep("ocr", "");
  setProgressStep("ready", "");
  setProgressFill(5);
}
function setProgressFill(pct) {
  const fill = document.querySelector(".progress-fill");
  if (fill) fill.style.width = pct + "%";
}
function setProgressStep(name, status) {
  const el = document.querySelector(`[data-step="${name}"]`);
  if (!el) return;
  el.classList.remove("active", "done");
  if (status) el.classList.add(status);
  const icon = el.querySelector(".step-icon");
  if (icon) icon.textContent = status === "done" ? "✓" : "";
}
function hideUploadProgress() {
  const box = $("#upload-progress");
  if (box) box.classList.add("hidden");
}

function fileToDataUrl(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => resolve("");
    reader.readAsDataURL(file);
  });
}

function handleFile(file) {
  state.file = file;
  showUploadProgress();
  setProgressFill(15);
  const form = new FormData();
  form.append("file", file);
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/api/extract");
  if (state.token) xhr.setRequestHeader("Authorization", "Bearer " + state.token);
  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) setProgressFill(Math.min(40, (e.loaded / e.total) * 40));
  };
  xhr.onloadstart = () => setProgressStep("upload", "active");
  xhr.onload = async () => {
    if (xhr.status >= 200 && xhr.status < 300) {
      try {
        const data = JSON.parse(xhr.responseText);
        setProgressStep("upload", "done");
        setProgressStep("ocr", "active");
        setProgressFill(75);
        state.extractedText = data.text;
        const dataUrl = await fileToDataUrl(file);
        state.imageDataUrl = dataUrl;
        saveWorkspace(data.text, dataUrl);
        setTimeout(() => {
          setProgressFill(100);
          setProgressStep("ocr", "done");
          setProgressStep("ready", "active");
          setTimeout(() => {
            setProgressStep("ready", "done");
            setTimeout(() => {
              hideUploadProgress();
              showResults(data.text, dataUrl);
            }, 350);
          }, 250);
        }, 300);
      } catch (err) { uploadFailed(err.message); }
    } else {
      let msg = "Upload failed";
      try { msg = JSON.parse(xhr.responseText).detail || msg; } catch(e) {}
      uploadFailed(msg);
    }
  };
  xhr.onerror = () => uploadFailed("Network error");
  xhr.send(form);
}

function uploadFailed(msg) {
  hideUploadProgress();
  $("#drop").classList.remove("hidden");
  showToast("Upload failed: " + msg, "error");
}

function showResults(text, dataUrl) {
  const preview = $("#img-preview");
  preview.src = dataUrl;
  preview.classList.remove("hidden");
  $("#text-preview").textContent = text || "(no text found)";
  updateTextMeta();
  $("#workspace-content").classList.remove("hidden");
  $("#chat-section").classList.remove("hidden");
  showToast("Image processed ✓", "success");
  updateWorkspaceLock();
}

// ── Chat helpers ──
async function loadChats() {
  try {
    const data = await api("/api/chats");
    state.chats = data.chats || [];
    if (state.chats.length === 0) await createNewChat(true);
    else {
      state.currentChatId = state.chats[state.chats.length - 1].id;
      renderChatSelector();
      await loadMessages(state.currentChatId);
    }
  } catch (err) { showToast("Failed to load chats: " + err.message, "error"); }
}

function renderChatSelector() {
  const sel = $("#chat-selector");
  if (!sel) return;
  sel.innerHTML = state.chats.map((c) =>
    `<option value="${c.id}" ${c.id === state.currentChatId ? "selected" : ""}>${escapeHtml(c.title)}</option>`
  ).join("");
}

async function createNewChat(select = true) {
  try {
    const data = await api("/api/chats/new", { method: "POST" });
    state.chats.push(data);
    if (select) {
      state.currentChatId = data.id;
      renderChatSelector();
      renderMessages([]);
      showToast("New chat created", "success");
    }
    return data;
  } catch (err) { showToast("Failed to create chat: " + err.message, "error"); }
}

async function selectChat(chatId) {
  state.currentChatId = chatId;
  renderChatSelector();
  await loadMessages(chatId);
}

async function loadMessages(chatId) {
  try {
    const data = await api("/api/chats/" + chatId);
    renderMessages(data.messages || []);
  } catch (err) { showToast("Failed to load messages: " + err.message, "error"); }
}

function renderMessages(messages) {
  const box = $("#chat-messages");
  box.innerHTML = "";
  messages.forEach((m) => appendMessageToUI(m.role, m.content));
  box.scrollTop = box.scrollHeight;
}

function appendMessageToUI(role, content) {
  const box = $("#chat-messages");
  if (!box) return;
  const el = document.createElement("div");
  el.className = `chat-msg ${role}`;
  if (role === "assistant") {
    el.innerHTML = `
      <button class="copy-btn" onclick="copyMessage(this)">Copy</button>
      <div class="md-content">${renderMarkdown(content)}</div>
    `;
  } else el.textContent = content;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
}

function copyMessage(btn) {
  const parent = btn.closest(".chat-msg");
  const content = parent.querySelector(".md-content");
  const text = content ? content.innerText : parent.innerText;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = "Copied";
    btn.classList.add("copied");
    setTimeout(() => { btn.textContent = "Copy"; btn.classList.remove("copied"); }, 1500);
  });
}

function addTypingIndicator() {
  const box = $("#chat-messages");
  const el = document.createElement("div");
  el.className = "chat-msg assistant";
  el.innerHTML = `<div class="typing"><span></span><span></span><span></span></div>`;
  box.appendChild(el);
  box.scrollTop = box.scrollHeight;
  return el;
}

function showClearConfirm() {
  const box = $("#chat-messages");
  if (box.querySelector(".inline-confirm")) return;
  const wrapper = document.createElement("div");
  wrapper.className = "inline-confirm";
  wrapper.innerHTML = `
    <span class="text">Clear all messages in this chat? This can't be undone.</span>
    <div class="btns">
      <button class="no-btn" onclick="hideClearConfirm(this)">Cancel</button>
      <button class="yes-btn" onclick="confirmClearChat(this)">Clear</button>
    </div>
  `;
  box.appendChild(wrapper);
  box.scrollTop = box.scrollHeight;
}

function hideClearConfirm(btn) {
  const w = btn.closest(".inline-confirm");
  if (w) w.remove();
}

async function confirmClearChat(btn) {
  const w = btn.closest(".inline-confirm");
  if (w) w.remove();
  if (!state.currentChatId) return;
  try {
    await api("/api/chats/" + state.currentChatId + "/clear", { method: "POST" });
    renderMessages([]);
    const chat = state.chats.find(c => c.id === state.currentChatId);
    if (chat) chat.title = "New chat";
    renderChatSelector();
    showToast("Chat cleared", "success");
  } catch (err) { showToast("Failed to clear: " + err.message, "error"); }
}

async function downloadCurrentChat() {
  if (!state.currentChatId) return;
  try {
    const data = await api("/api/chats/" + state.currentChatId);
    const messages = data.messages || [];
    if (messages.length === 0) { showToast("No messages to download", "info"); return; }
    let txt = "SnapSum Chat\\n============\\nChat: " + data.title + "\\nExported: " + new Date().toLocaleString() + "\\n\\n";
    messages.forEach((m) => {
      const who = m.role === "user" ? "You" : "SnapSum";
      txt += "[" + who + "]\\n" + m.content + "\\n\\n";
    });
    const blob = new Blob([txt], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "snapsum_chat_" + state.currentChatId + ".txt";
    a.click();
    showToast("Chat downloaded", "success");
  } catch (err) { showToast("Failed to download: " + err.message, "error"); }
}

async function runQuickAction(action) {
  if (!state.extractedText) { showToast("Upload an image first", "info"); return; }
  if (state.uses >= state.limit) { showToast("Usage limit reached", "error"); return; }
  if (action === "summarize") {
    await sendChat("Summarize this", "quick", {
      system: "Summarize the image content in exactly 3 concise bullet points. Write in " + state.outputLang + ". Return ONLY the 3 bullets. Base this ONLY on the image content provided.",
      display: "✨ Summarize this",
    });
  } else if (action === "translate") {
    showTranslateForm();
  } else if (action === "explain") {
    await sendChat("Explain this", "quick", {
      system: "Explain the image content in " + state.outputLang + " using three sections: 1. WHAT it is 2. WHY it matters 3. HOW it's structured. Base this ONLY on the image content.",
      display: "🧠 Explain this",
    });
  }
}

function showTranslateForm() {
  const box = $("#chat-messages");
  if (box.querySelector(".inline-form")) return;
  const wrapper = document.createElement("div");
  wrapper.className = "inline-form";
  wrapper.innerHTML = `
    <label>Translate the image text to which language?</label>
    <select id="translate-target">
      <option>English</option><option>Hindi</option><option>Telugu</option>
      <option>Tamil</option><option>Kannada</option><option>Malayalam</option>
      <option>Marathi</option><option>Bengali</option><option>Gujarati</option>
      <option>Punjabi</option><option>Urdu</option><option>Spanish</option>
      <option>French</option><option>German</option><option>Italian</option>
      <option>Portuguese</option><option>Russian</option><option>Arabic</option>
      <option>Chinese</option><option>Japanese</option><option>Korean</option>
    </select>
    <div class="btn-row">
      <button class="cancel-btn" onclick="hideTranslateForm(this)">Cancel</button>
      <button class="btn-primary" onclick="confirmTranslate(this)">Translate</button>
    </div>
  `;
  box.appendChild(wrapper);
  box.scrollTop = box.scrollHeight;
  wrapper.querySelector("#translate-target").value = state.outputLang;
}

function hideTranslateForm(btn) {
  const w = btn.closest(".inline-form");
  if (w) w.remove();
}

async function confirmTranslate(btn) {
  const w = btn.closest(".inline-form");
  const lang = w.querySelector("#translate-target").value;
  w.remove();
  await sendChat("Translate to " + lang, "quick", {
    system: "Translate the image text into " + lang + ". Return ONLY the translation. Do not add explanations.",
    display: "🌐 Translate to " + lang,
  });
}

async function sendChat(text, kind = "user", opts = {}) {
  const q = (text || "").trim();
  if (!q && kind === "user") return;
  if (!state.extractedText) { showToast("Upload an image first", "info"); return; }
  if (state.uses >= state.limit) { showToast("Usage limit reached. Create a new account.", "error"); return; }
  if (!state.currentChatId) await createNewChat(true);

  const displayText = opts.display || q;
  appendMessageToUI("user", displayText);
  const typingEl = addTypingIndicator();

  try {
    let data;
    if (kind === "quick") {
      data = await api("/api/quick", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: state.extractedText, system_prompt: opts.system,
          chat_id: state.currentChatId, display_text: displayText,
        }),
      });
    } else {
      data = await api("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q, text: state.extractedText,
          language: state.outputLang, input_language: state.inputLang,
          chat_id: state.currentChatId,
        }),
      });
    }
    typingEl.remove();
    appendMessageToUI("assistant", data.answer || data.result);

    const chatsData = await api("/api/chats");
    state.chats = chatsData.chats || [];
    renderChatSelector();
    await fetchAccount();
    updateWorkspaceLock();
  } catch (err) {
    typingEl.remove();
    if (err.message && err.message.toLowerCase().includes("limit")) {
      appendMessageToUI("assistant", "⚠️ " + err.message);
    } else if (err.message && err.message.toLowerCase().includes("login")) {
      showToast("Session expired. Please login again.", "error");
      setToken(null, null);
      setTimeout(() => location.href = "/login", 900);
    } else {
      appendMessageToUI("assistant", "Failed: " + err.message);
    }
    showToast("Request failed: " + err.message, "error");
  }
}

// ── Settings ──
async function initSettings() {
  renderNavbar();
  if (!state.token) { location.href = "/"; return; }
  const el = $("#settings-user");
  if (el) el.textContent = state.username || "—";

  try {
    const data = await api("/api/account");
    const info = $("#settings-info");
    if (info) {
      info.innerHTML = `
        <p><strong>Name:</strong> ${escapeHtml(data.name || "—")}</p>
        <p><strong>Email:</strong> ${escapeHtml(data.email || "—")}</p>
        <p><strong>Username:</strong> ${escapeHtml(data.username || "—")}</p>
        <p><strong>Joined:</strong> ${escapeHtml((data.created || "").slice(0,10))}</p>
        <p><strong>Uses:</strong> ${data.uses || 0} / ${data.limit || 25}</p>
      `;
    }
    const meter = $("#usage-meter-fill");
    if (meter) {
      const pct = Math.min(100, ((data.uses || 0) / (data.limit || 25)) * 100);
      meter.style.width = pct + "%";
      const remaining = (data.limit || 25) - (data.uses || 0);
      if (remaining === 0) meter.classList.add("empty");
      else if (remaining <= 5) meter.classList.add("low");
    }
    const preview = $("#avatar-preview");
    if (preview) {
      if (data.avatar) {
        preview.innerHTML = `<img src="${data.avatar}" class="avatar-large" alt="avatar" />`;
        state.avatar = data.avatar;
      } else {
        preview.innerHTML = `<div class="avatar-large-initials">${initials(data.name || data.username)}</div>`;
      }
    }
  } catch (err) { showToast("Failed to load account: " + err.message, "error"); }

  const avatarInput = $("#avatar-input");
  const avatarBtn = $("#avatar-upload-btn");
  if (avatarBtn && avatarInput) {
    avatarBtn.onclick = () => avatarInput.click();
    avatarInput.onchange = async () => {
      if (!avatarInput.files[0]) return;
      const file = avatarInput.files[0];
      if (file.size > 2 * 1024 * 1024) { showToast("Image too large (max 2 MB)", "error"); return; }
      const dataUrl = await fileToDataUrl(file);
      try {
        await api("/api/account/avatar", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ avatar: dataUrl }),
        });
        state.avatar = dataUrl;
        const preview = $("#avatar-preview");
        if (preview) preview.innerHTML = `<img src="${dataUrl}" class="avatar-large" alt="avatar" />`;
        renderNavbar();
        showToast("Profile picture updated", "success");
      } catch (err) { showToast("Failed: " + err.message, "error"); }
    };
  }

  const deleteBtn = $("#delete-account-btn");
  const deleteConfirm = $("#delete-confirm");
  const cancelDelete = $("#cancel-delete");
  const confirmDelete = $("#confirm-delete");
  if (deleteBtn) deleteBtn.onclick = () => { deleteConfirm.classList.remove("hidden"); deleteBtn.classList.add("hidden"); };
  if (cancelDelete) cancelDelete.onclick = () => { deleteConfirm.classList.add("hidden"); deleteBtn.classList.remove("hidden"); };
  if (confirmDelete) confirmDelete.onclick = async () => {
    const pw = $("#delete-password").value;
    if (!pw) { showToast("Enter your password to confirm", "error"); return; }
    try {
      await api("/api/account/delete", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw }),
      });
      showToast("Account deleted", "success");
      setTimeout(() => { setToken(null, null); clearWorkspace(); location.href = "/"; }, 1200);
    } catch (err) { showToast("Failed: " + err.message, "error"); }
  };
}

// ── Support ──
function initSupport() {
  renderNavbar();
  $$(".amount-btn").forEach((btn) => {
    btn.onclick = () => {
      $$(".amount-btn").forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      state.selectedAmount = btn.dataset.amount;
    };
  });
  const defaultBtn = document.querySelector('[data-amount="10"]');
  if (defaultBtn) defaultBtn.classList.add("selected");
  const copyBtn = $("#copy-upi");
  if (copyBtn) {
    copyBtn.onclick = () => {
      const upiId = $("#upi-id").textContent.trim();
      navigator.clipboard.writeText(upiId).then(() => {
        copyBtn.textContent = "✓ Copied";
        copyBtn.classList.add("copied");
        showToast("UPI ID copied", "success");
        setTimeout(() => { copyBtn.textContent = "📋 Copy UPI"; copyBtn.classList.remove("copied"); }, 1800);
      });
    };
  }
}
"""


# ═════════════════════════════════════════════
# HTML shell
# ═════════════════════════════════════════════
def _shell(title, body, page_script):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — SnapSum</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/static/style.css" />
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>
  <div id="navbar" class="navbar"></div>
  <main>{body}</main>
  <script src="/static/app.js"></script>
  <script>{page_script}</script>
</body>
</html>"""


LANG_OPTIONS = """
<option>English</option><option>Hindi</option><option>Telugu</option>
<option>Tamil</option><option>Kannada</option><option>Malayalam</option>
<option>Marathi</option><option>Bengali</option><option>Gujarati</option>
<option>Punjabi</option><option>Urdu</option><option>Spanish</option>
<option>French</option><option>German</option><option>Italian</option>
<option>Portuguese</option><option>Russian</option><option>Arabic</option>
<option>Chinese</option><option>Japanese</option><option>Korean</option>
"""

INDEX_BODY = """
<div class="container">
  <section class="hero">
    <h1>📸 SnapSum</h1>
    <p>Turn screenshots into summaries, translations, and answers.</p>
    <div class="cta">
      <button id="cta-start" class="btn-primary">🚀 Get Started</button>
      <button id="cta-workspace" class="btn-primary hidden">🎯 Go to Workspace</button>
      <a id="cta-login" href="/login" style="text-decoration:none;"><button class="btn-secondary">🔐 Login</button></a>
    </div>
    <div class="stats-row">
      <div class="stat-box"><span class="num" id="stat-views">0</span><span class="label">Page Views</span></div>
      <div class="stat-box"><span class="num" id="stat-users">0</span><span class="label">Users</span></div>
    </div>
  </section>

  <h2 class="section-title">What you can do</h2>
  <div class="grid">
    <div class="card"><h3>🔍 Extract</h3><p>Pull text from any screenshot — chats, articles, receipts, roadmaps.</p></div>
    <div class="card"><h3>🌐 Translate</h3><p>Translate extracted text into any of 21 supported languages.</p></div>
    <div class="card"><h3>✨ Summarize</h3><p>Get a clean 3-bullet summary in your chosen language.</p></div>
    <div class="card"><h3>🧠 Explain</h3><p>Understand what, why, and how — beginner-friendly.</p></div>
    <div class="card"><h3>💬 Ask</h3><p>Chat with the image and get answers with full history.</p></div>
    <div class="card"><h3>📄 Export</h3><p>Download chat conversations as TXT.</p></div>
  </div>
</div>
"""

LOGIN_BODY = """
<div class="container">
  <div class="auth-wrap">
    <h2>Welcome to SnapSum</h2>
    <div class="tabs">
      <button class="tab active">Login</button>
      <button class="tab">Register</button>
    </div>

    <form id="login-form">
      <div id="login-msg" class="msg hidden"></div>
      <label>Username</label>
      <input id="login-username" required />
      <label>Password</label>
      <input id="login-password" type="password" required />
      <button type="submit" class="btn-primary" style="width:100%;">Login</button>
    </form>

    <form id="register-form" class="hidden">
      <div id="register-msg" class="msg hidden"></div>
      <label>Full name</label>
      <input id="reg-name" required />
      <label>Email</label>
      <input id="reg-email" type="email" required />
      <label>Username</label>
      <input id="reg-username" required />
      <label>Password</label>
      <input id="reg-password" type="password" required minlength="4" />
      <button type="submit" class="btn-primary" style="width:100%;">Create account</button>
      <p style="font-size:12px;color:var(--muted);margin-top:10px;text-align:center;">
        Free tier includes 25 uses per account. Login is session-based — closing the tab signs you out.
      </p>
    </form>
  </div>
</div>
"""

WORKSPACE_BODY = f"""
<div class="container">
  <h2 style="margin-bottom:6px;">🎯 Workspace</h2>
  <p style="color:var(--muted);margin-bottom:20px;">Upload a screenshot. Analyze it. Chat with it.</p>

  <div id="limit-banner" class="info-banner danger hidden">
    <span class="icon">⚠️</span>
    <div>
      <strong>Free tier reached.</strong> You've used all 25 requests. Create a new account to continue, or <a href="/support" style="color:inherit;text-decoration:underline;">support us</a>.
    </div>
  </div>

  <div class="info-banner">
    <span class="icon">ℹ️</span>
    <div>
      <strong>Free tier:</strong> 25 requests per account. All answers are based only on your uploaded image. <em>Tip: Ctrl+K focuses the chat input.</em>
    </div>
  </div>

  <div class="lang-bar">
    <div class="group">
      <label for="input-lang">You type in</label>
      <select id="input-lang">{LANG_OPTIONS}</select>
    </div>
    <div class="group">
      <label for="output-lang">AI responds in</label>
      <select id="output-lang">{LANG_OPTIONS}</select>
    </div>
  </div>

  <div id="drop" class="drop">
    <p>📤 Click or drag a PNG / JPG / JPEG here</p>
    <small>Max 10 MB · English text works best</small>
    <input id="file-input" type="file" accept="image/*" class="hidden" />
  </div>

  <div id="upload-progress" class="upload-progress hidden">
    <div class="title">Processing your screenshot...</div>
    <div class="subtitle">Please wait while we read the text from your image</div>
    <div class="progress-bar"><div class="progress-fill"></div></div>
    <div class="progress-steps">
      <div class="progress-step" data-step="upload"><div class="step-icon"></div><span>Uploading image</span></div>
      <div class="progress-step" data-step="ocr"><div class="step-icon"></div><span>Extracting text with OCR</span></div>
      <div class="progress-step" data-step="ready"><div class="step-icon"></div><span>Preparing workspace</span></div>
    </div>
  </div>

  <div id="workspace-content" class="workspace-grid hidden" style="margin-top:24px;">
    <div class="panel">
      <h3>
        <span>🖼️ Image &amp; Extracted Text</span>
        <div class="panel-actions">
          <button id="copy-text-btn" class="btn-icon" title="Copy extracted text">📋</button>
          <button id="reset-workspace-btn" class="btn-icon" title="New image">🔄</button>
        </div>
      </h3>
      <img id="img-preview" class="img-preview hidden" />
      <div id="text-preview" class="text-preview">No text yet.</div>
      <p id="text-meta" class="text-meta"></p>
    </div>

    <div id="chat-section" class="chat-box hidden">
      <div class="chat-header">
        <h3>💬 Chat</h3>
        <select id="chat-selector" class="chat-select"></select>
        <button id="new-chat-btn" class="btn-icon" title="New chat">➕</button>
        <button id="clear-chat-btn" class="btn-icon" title="Clear current chat">🗑️</button>
        <button id="download-chat-btn" class="btn-icon" title="Download chat">⬇️</button>
        <button id="voice-btn" class="btn-icon coming-soon" title="Voice assistant (coming soon)">🎤</button>
      </div>

      <div class="quick-actions">
        <span class="label">Quick actions:</span>
        <button class="btn-quick" data-action="summarize">✨ Summarize</button>
        <button class="btn-quick" data-action="translate">🌐 Translate</button>
        <button class="btn-quick" data-action="explain">🧠 Explain</button>
      </div>

      <div id="chat-messages" class="chat-messages"></div>
      <div class="chat-input-row">
        <input id="chat-input" placeholder="Ask anything about your image... (Ctrl+K)" />
        <button id="chat-send" class="btn-primary">Send</button>
      </div>
    </div>
  </div>
</div>
"""

SETTINGS_BODY = """
<div class="container">
  <h2 style="margin-bottom:6px;">⚙️ Settings</h2>
  <p style="color:var(--muted);margin-bottom:24px;">Account details and preferences.</p>

  <div class="settings-section">
    <h3>👤 Profile</h3>
    <div class="avatar-upload">
      <div id="avatar-preview"><div class="avatar-large-initials">?</div></div>
      <div>
        <button id="avatar-upload-btn" class="btn-secondary">📷 Change picture</button>
        <input id="avatar-input" type="file" accept="image/*" class="hidden" />
        <p style="font-size:12px;color:var(--muted);margin-top:8px;">JPG or PNG, max 2 MB</p>
      </div>
    </div>
  </div>

  <div class="settings-section">
    <h3>📊 Usage</h3>
    <div class="usage-meter"><div class="usage-meter-bar"><div id="usage-meter-fill" class="usage-meter-fill"></div></div></div>
    <p style="font-size:13px;color:var(--muted);">Free tier: 25 requests per account.</p>
  </div>

  <div class="settings-section">
    <h3>📋 Account info</h3>
    <p>Username: <strong id="settings-user">—</strong></p>
    <div id="settings-info"></div>
  </div>

  <div class="settings-section">
    <h3>🔒 Session</h3>
    <p>You're signed in for this tab only. Closing the browser tab or navigating away will sign you out automatically.</p>
  </div>

  <div class="settings-section">
    <h3>ℹ️ About</h3>
    <p>SnapSum v4.2</p>
    <p>Developed by Nagesha G</p>
    <p>Built with FastAPI, EasyOCR, and Groq.</p>
  </div>

  <div class="settings-section danger-zone">
    <h3>⚠️ Danger Zone</h3>
    <p>Deleting your account removes all your chats, data, and cannot be undone.</p>
    <button id="delete-account-btn" class="btn-danger">🗑️ Delete my account</button>
    <div id="delete-confirm" class="hidden" style="margin-top:16px;">
      <p style="color:#991B1B;font-weight:600;">Enter your password to confirm deletion:</p>
      <input id="delete-password" type="password" placeholder="Your password" />
      <div style="display:flex;gap:10px;">
        <button id="cancel-delete" class="btn-secondary">Cancel</button>
        <button id="confirm-delete" class="btn-danger">Yes, delete my account</button>
      </div>
    </div>
  </div>
</div>
"""

SUPPORT_BODY = f"""
<div class="container">
  <section class="support-hero">
    <h1>💛 Support SnapSum</h1>
    <p>SnapSum is free to use. If it saves you time, a small contribution keeps the servers running and the AI tokens flowing.</p>
  </section>

  <div class="support-card">
    <h3>☕ Buy me a coffee</h3>
    <p>Choose any amount that feels right — even ₹10 keeps us going.</p>
    <div class="amount-grid">
      <button class="amount-btn tiny" data-amount="1">₹1</button>
      <button class="amount-btn" data-amount="11">₹12</button>
      <button class="amount-btn" data-amount="21">₹21</button>
      
    </div>
    <div class="upi-box">
      <span class="upi-id" id="upi-id">{SUPPORT_UPI}</span>
      <button class="copy-upi-btn" id="copy-upi">📋 Copy UPI</button>
    </div>
    <p style="font-size:13px;color:var(--muted);margin-top:12px;">
      Open any UPI app (GPay, PhonePe, Paytm, BHIM) and pay to the ID above.
    </p>
  </div>

  <div class="support-card">
    <h3>💌 Other ways to help</h3>
    <p>
      <strong>Share SnapSum</strong> with friends, colleagues, and on social media.<br>
      <strong>Report bugs</strong> or suggest features at <strong>{SUPPORT_EMAIL}</strong><br>
      <strong>Star the repo</strong> on GitHub if you found it useful.
    </p>
  </div>

  <div class="support-note">
    Thank you for using SnapSum. Every contribution, no matter how small, means a lot.
    <br>— {SUPPORT_NAME}
  </div>
</div>
"""


# ═════════════════════════════════════════════
# ROUTES
# ═════════════════════════════════════════════
@app.get("/static/style.css")
def serve_css(): return Response(content=CSS, media_type="text/css")

@app.get("/static/app.js")
def serve_js(): return Response(content=JS, media_type="application/javascript")

@app.get("/", response_class=HTMLResponse)
def page_home(): return _shell("Home", INDEX_BODY, "document.addEventListener('DOMContentLoaded', initHome);")

@app.get("/login", response_class=HTMLResponse)
def page_login(): return _shell("Login", LOGIN_BODY, "document.addEventListener('DOMContentLoaded', initLogin);")

@app.get("/workspace", response_class=HTMLResponse)
def page_workspace(): return _shell("Workspace", WORKSPACE_BODY, "document.addEventListener('DOMContentLoaded', initWorkspace);")

@app.get("/settings", response_class=HTMLResponse)
def page_settings(): return _shell("Settings", SETTINGS_BODY, "document.addEventListener('DOMContentLoaded', initSettings);")

@app.get("/support", response_class=HTMLResponse)
def page_support(): return _shell("Support", SUPPORT_BODY, "document.addEventListener('DOMContentLoaded', initSupport);")


# ── Models ──
class RegisterIn(BaseModel):
    name: str
    email: str
    username: str
    password: str

class LoginIn(BaseModel):
    username: str
    password: str

class QuickIn(BaseModel):
    text: str
    system_prompt: str
    chat_id: str
    display_text: str

class ChatIn(BaseModel):
    question: str
    text: str
    language: str = "English"
    input_language: str = "English"
    chat_id: str

class AvatarIn(BaseModel):
    avatar: str

class DeleteIn(BaseModel):
    password: str


# ── Helpers ──
def _user_chats(chats_data, username):
    if username not in chats_data:
        chats_data[username] = {}
    return chats_data[username]


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _append_message(username, chat_id, role, content):
    chats_data = load_chats()
    user_chats = _user_chats(chats_data, username)
    if chat_id not in user_chats:
        user_chats[chat_id] = {
            "title": "New chat",
            "created": datetime.now().isoformat(),
            "messages": [],
        }
    chat = user_chats[chat_id]
    chat["messages"].append({"role": role, "content": content, "time": _now()})
    if role == "user" and chat.get("title") == "New chat":
        chat["title"] = content[:40] + ("..." if len(content) > 40 else "")
    save_chats(chats_data)


def build_qa_system_prompt(text, input_lang, output_lang):
    return f"""You are SnapSum, an AI assistant that helps users understand the content of their uploaded screenshot.

USER SETTINGS:
- User may type in: {input_lang}
- You MUST always respond in: {output_lang}

IMAGE CONTENT (extracted via OCR):
--- BEGIN IMAGE TEXT ---
{text[:8000]}
--- END IMAGE TEXT ---

YOUR TASK: Answer the user's question using ONLY the image content above.

CRITICAL RULES:
1. READ CAREFULLY. The answer is almost always in the image. OCR may have small errors — infer meaning from context.
2. CALCULATE when needed. If the user asks for bill totals, sums, counts, dates, differences — compute from image data and show the working briefly.
3. TRANSLATE NATURALLY. If the user asks in {input_lang} but the image is in another language, understand and answer in {output_lang}.
4. EXTRACT STRUCTURED DATA. If the image has tables, receipts, lists, forms — pull the data out cleanly with bullets or a simple table.
5. IF NOT IN IMAGE: Say exactly "This information is not in the image." in {output_lang}. Do not guess.
6. NEVER INVENT. No fabricated names, numbers, dates, or facts.
7. PRIVACY GUARD — do NOT reveal: passwords, PINs, OTPs, full bank account numbers, card numbers, CVV, government IDs, third-party personal contact info, private messages of others. If asked, respond: "This appears to be sensitive information. For privacy reasons, I won't share it." in {output_lang}.
8. GENERAL QUESTIONS: If the user asks "what is this" or "explain this", give a clear description of what the image shows, its purpose, and key information.
9. FORMAT with markdown: bullets, **bold** for key values, short headings. Keep it tight.
10. BE DIRECT. Skip preamble like "Based on the image...". Just answer.
11. STAY IN SCOPE. Only answer about this image's content. Redirect unrelated questions politely.
"""


# ── API routes ──
@app.post("/api/register")
def api_register(payload: RegisterIn):
    if len(payload.password) < 4:
        raise HTTPException(400, "Password must be at least 4 characters.")
    users = load_users()
    if payload.username in users:
        raise HTTPException(400, "Username already exists.")
    users[payload.username] = {
        "name": payload.name,
        "email": payload.email,
        "password": hash_pw(payload.password),
        "created": datetime.now().isoformat(),
        "avatar": "",
        "uses": 0,
    }
    save_users(users)
    return {"ok": True}


@app.post("/api/login")
def api_login(payload: LoginIn):
    users = load_users()
    user = users.get(payload.username)
    if not user or user["password"] != hash_pw(payload.password):
        raise HTTPException(401, "Invalid username or password.")
    token = secrets.token_urlsafe(24)
    SESSIONS[token] = payload.username
    return {"token": token, "username": payload.username}


@app.get("/api/account")
def api_account(request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    users = load_users()
    user = users.get(username, {})
    return {
        "username": username,
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "created": user.get("created", ""),
        "avatar": user.get("avatar", ""),
        "uses": user.get("uses", 0),
        "limit": FREE_TIER_LIMIT,
    }


@app.post("/api/account/avatar")
def api_update_avatar(payload: AvatarIn, request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    users = load_users()
    if username not in users:
        raise HTTPException(404, "User not found.")
    users[username]["avatar"] = payload.avatar
    save_users(users)
    return {"ok": True}


@app.post("/api/account/delete")
def api_delete_account(payload: DeleteIn, request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    users = load_users()
    user = users.get(username)
    if not user or user["password"] != hash_pw(payload.password):
        raise HTTPException(401, "Incorrect password.")
    del users[username]
    save_users(users)
    chats_data = load_chats()
    if username in chats_data:
        del chats_data[username]
        save_chats(chats_data)
    tokens_to_remove = [t for t, u in SESSIONS.items() if u == username]
    for t in tokens_to_remove:
        SESSIONS.pop(t, None)
    return {"ok": True}


@app.post("/api/extract")
async def api_extract(file: UploadFile = File(...)):
    data = await file.read()
    try:
        Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Invalid image file.")
    reader = get_reader()
    result = reader.readtext(data, detail=0)
    text = " ".join(result).strip()
    return {"text": text}


@app.post("/api/analytics/view")
def api_analytics_view():
    a = load_analytics()
    a["page_views"] = a.get("page_views", 0) + 1
    save_analytics(a)
    return {"ok": True}


@app.get("/api/analytics/stats")
def api_analytics_stats():
    a = load_analytics()
    users = load_users()
    return {"page_views": a.get("page_views", 0), "total_users": len(users)}


@app.get("/api/chats")
def api_list_chats(request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    chats_data = load_chats()
    user_chats = _user_chats(chats_data, username)
    out = []
    for cid, chat in user_chats.items():
        out.append({
            "id": cid,
            "title": chat.get("title", "New chat"),
            "created": chat.get("created", ""),
            "message_count": len(chat.get("messages", [])),
        })
    out.sort(key=lambda c: c["created"])
    return {"chats": out}


@app.post("/api/chats/new")
def api_new_chat(request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    chats_data = load_chats()
    user_chats = _user_chats(chats_data, username)
    cid = "chat_" + secrets.token_urlsafe(8)
    user_chats[cid] = {"title": "New chat", "created": datetime.now().isoformat(), "messages": []}
    save_chats(chats_data)
    return {"id": cid, "title": "New chat", "created": user_chats[cid]["created"], "message_count": 0}


@app.get("/api/chats/{chat_id}")
def api_get_chat(chat_id: str, request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    chats_data = load_chats()
    user_chats = _user_chats(chats_data, username)
    if chat_id not in user_chats:
        raise HTTPException(404, "Chat not found.")
    chat = user_chats[chat_id]
    return {"id": chat_id, "title": chat.get("title", "New chat"), "messages": chat.get("messages", [])}


@app.post("/api/chats/{chat_id}/clear")
def api_clear_chat(chat_id: str, request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    chats_data = load_chats()
    user_chats = _user_chats(chats_data, username)
    if chat_id not in user_chats:
        raise HTTPException(404, "Chat not found.")
    user_chats[chat_id]["messages"] = []
    user_chats[chat_id]["title"] = "New chat"
    save_chats(chats_data)
    return {"ok": True}


@app.post("/api/quick")
def api_quick(payload: QuickIn, request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    allowed, remaining = check_usage(username)
    if not allowed:
        raise HTTPException(402, "Free tier limit reached. Create a new account to continue.")
    _append_message(username, payload.chat_id, "user", payload.display_text)
    result = call_llm(payload.system_prompt, payload.text[:8000], 0.3)
    _append_message(username, payload.chat_id, "assistant", result)
    increment_usage(username)
    return {"result": result}


@app.post("/api/chat")
def api_chat(payload: ChatIn, request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(401, "Login required.")
    allowed, remaining = check_usage(username)
    if not allowed:
        raise HTTPException(402, "Free tier limit reached. Create a new account to continue.")

    _append_message(username, payload.chat_id, "user", payload.question)
    system = build_qa_system_prompt(payload.text, payload.input_language, payload.language)
    answer = call_llm(system, payload.question, 0.2)
    _append_message(username, payload.chat_id, "assistant", answer)
    increment_usage(username)
    return {"answer": answer}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)