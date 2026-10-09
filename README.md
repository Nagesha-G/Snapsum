---
title: SnapSum
emoji: 📸
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---
# 📸 SnapSum

> Turn screenshots into summaries, translations, and answers.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![EasyOCR](https://img.shields.io/badge/EasyOCR-OCR-green)
![Groq](https://img.shields.io/badge/Groq-LLM-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Version](https://img.shields.io/badge/version-4.2-blue)

---

## 🧠 What It Does

SnapSum is a full-stack web app that reads any screenshot and helps you understand it.

1. **Extract** — Pulls text from any screenshot using OCR
2. **Summarize** — Delivers a clean 3-bullet summary
3. **Translate** — Converts content into 21 languages
4. **Explain** — Breaks down the content as WHAT / WHY / HOW
5. **Chat** — Answers your questions about the image
6. **Export** — Downloads chat conversations as `.txt`

Every answer is grounded in the uploaded image. If something isn't in the image, SnapSum says so. If it's sensitive (passwords, IDs, OTPs), SnapSum refuses to reveal it.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖼️ **Screenshot OCR** | Reads text from PNG/JPG/JPEG with real-time progress |
| 🌐 **21 output languages** | Hindi, Telugu, Tamil, Spanish, French, Arabic, Chinese, Japanese, Korean, and more |
| ✨ **3-bullet summaries** | Clean, consistent summaries every time |
| 🧠 **Explain mode** | Beginner-friendly WHAT / WHY / HOW breakdown |
| 💬 **Image-aware chat** | Ask anything — SnapSum only answers from the image |
| 📊 **Bill calculations** | Ask "what's the total?" on a receipt — SnapSum computes it |
| 🔒 **Privacy guard** | Refuses OTPs, bank numbers, IDs, third-party contact info |
| 📚 **Chat persistence** | Chats saved per user — survive refresh |
| 🔐 **Session auth** | Login is tab-scoped; closing the tab signs you out |
| 👤 **User accounts** | Register, login, profile picture upload, delete account |
| 📊 **Usage tracking** | 25 free requests per account, live count in navbar |
| ⬇️ **Export chats** | Download any chat as a `.txt` file |
| 🎨 **Modern UI** | Clean indigo-on-white design, responsive on mobile |
| ⌨️ **Keyboard shortcut** | `Ctrl+K` focuses chat input |
| 💛 **Support page** | UPI donations from ₹10 upward |

---

## 🎬 How It Works

```
[Your Screenshot]
       ↓
[Pillow reads image]
       ↓
[EasyOCR extracts text]
       ↓
[Groq LLM: summarize / translate / explain / answer]
       ↓
[Live web UI in the browser]
```

**Architecture:** One Python file — FastAPI serves both the backend API and the HTML/CSS/JS frontend. No build step, no Node.js, no separate frontend repo.

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| Backend | [FastAPI](https://fastapi.tiangolo.com) |
| Server | [Uvicorn](https://www.uvicorn.org) |
| OCR | [EasyOCR](https://github.com/JaidedAI/EasyOCR) |
| LLM | [Groq](https://groq.com) — `openai/gpt-oss-120b` |
| Image | [Pillow](https://python-pillow.org) |
| Markdown rendering | [marked.js](https://marked.js.org) |
| Config | [python-dotenv](https://github.com/theskumar/python-dotenv) |

---

## 📦 Setup

### 1. Clone the repo

```bash
git clone https://github.com/Nagesha-G/Snapsum.git
cd Snapsum
```

### 2. Create a virtual environment

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (Git Bash) / macOS / Linux:**
```bash
python -m venv venv
source venv/Scripts/activate     # Windows Git Bash
# source venv/bin/activate       # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Get a free key at **[console.groq.com/keys](https://console.groq.com/keys)**.

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b

# Optional — customize the support page
SUPPORT_UPI=yourname@upi
SUPPORT_NAME=Your Name
SUPPORT_EMAIL=support@snapsum.app
```

> ⚠️ **Never commit `.env`.** It's already in `.gitignore`.

### 5. Run

```bash
uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000**

> First OCR run downloads ~100 MB of EasyOCR models — takes 30–60 seconds. Subsequent runs are instant.

---

## 🎯 Usage

1. **Register** an account from the Login page
2. **Login** — session persists until you close the tab
3. Choose **input language** (what you type) and **output language** (how AI responds)
4. **Upload** a screenshot — watch the progress bar
5. Use the **chat quick actions**:
   - ✨ **Summarize** — 3 bullets
   - 🌐 **Translate** — pick target language
   - 🧠 **Explain** — WHAT / WHY / HOW
6. **Ask anything** in the chat — answers come from the image only
7. **Export** the chat as `.txt` from the ⬇️ button
8. **Switch chats** with the dropdown, or start a new one with ➕

---

## 🚀 Version History

| Version | Highlights |
|---------|-----------|
| **v0.1** | Working MVP — upload, OCR, summarize, Q&A |
| **v0.2** | Sidebar, session history, download summary |
| **v0.3** | Multi-page UI, user auth, translation, explanation |
| **v0.4** | SQLite-ready architecture, PDF export |
| **v1.0** | First public release — user accounts, 21 languages |
| **v2.0** | Modular structure, top navbar, modern UI |
| **v3.0** | Full-stack rewrite — FastAPI + HTML/CSS/JS in one file |
| **v3.3** | Markdown rendering, chat persistence, multiple chats |
| **v3.4** | Upload progress, support page, voice placeholder |
| **v4.0** | Profile pictures, delete account, inline forms |
| **v4.1** | Image-focused AI, privacy guard, usage limits |
| **v4.2** | Session auth, ₹10 tier, copy/reset buttons, Ctrl+K |

---

## 📁 Project Structure

```
Snapsum/
├── app.py                    # Entire app — FastAPI + HTML + CSS + JS
├── requirements.txt          # Python dependencies
├── .env                      # Your secrets (gitignored)
├── .gitignore
├── README.md
├── users.json                # User accounts (gitignored, auto-generated)
├── chats.json                # Chat history (gitignored, auto-generated)
├── analytics.json            # Page views (gitignored, auto-generated)
└── venv/                     # Virtual environment (gitignored)
```

---

## 🔒 Security

- API keys loaded from `.env` via `python-dotenv`
- Passwords hashed with SHA-256
- `.env`, `users.json`, `chats.json`, `analytics.json` are all gitignored
- **Session tokens** stored in `sessionStorage` — cleared when tab closes
- **Privacy guard** in the AI prompt refuses to reveal OTPs, bank numbers, IDs, third-party contact info
- Answers are strictly scoped to the uploaded image

---

## 🔐 How Session Auth Works

SnapSum uses **`sessionStorage`** instead of `localStorage`:

| Storage | Cleared when |
|---------|-------------|
| `localStorage` | User manually clears, or never |
| `sessionStorage` | **Tab closes** ✅ |

Closing the browser tab signs you out automatically. Reopening → fresh session → Home page.

---

## 🤖 AI Behavior

SnapSum's system prompt enforces these rules:

1. **Read carefully** — the answer is almost always in the image
2. **Calculate** — bills, sums, counts, differences computed from image data
3. **Translate naturally** — you can ask in one language, get answers in another
4. **Extract structured data** — tables, receipts, forms rendered as bullets
5. **Refuse privacy violations** — OTPs, PINs, IDs never revealed
6. **Say "not in image"** — no guessing, no fabrication
7. **Stay in scope** — redirect unrelated questions politely

---

## 🗺️ Roadmap

- [x] **v1.0** — First release
- [x] **v2.0** — Modern UI
- [x] **v3.0** — Full-stack rewrite
- [x] **v4.0** — Profile management
- [x] **v4.1** — Image-focused AI + privacy guard
- [x] **v4.2** — Session auth + polish
- [ ] **v4.3** — Voice assistant (Whisper + TTS)
- [ ] **v4.4** — SQLite database
- [ ] **v4.5** — Multi-image batch processing
- [ ] **v5.0** — Public SaaS launch

---

## ⚠️ Known Limitations

- OCR is English-only (translation handles output language)
- Usage counter is per account, not per day
- Free tier: 25 requests per account
- No email verification (open registration)
- Analytics stores page views only — no tracking

---

## 🐛 Report Issues

Found a bug or have a feature request? Open an issue at:
**https://github.com/Nagesha-G/Snapsum/issues**

Or email: **support@snapsum.app**

---

## 💛 Support

SnapSum is free to use. If it saves you time, a small contribution helps keep the servers running.

- **UPI ID:** `nagesha@upi`
- **Amount:** ₹10 or more, whatever feels right

Or simply:
- ⭐ Star the repo
- 🐦 Share on social media
- 📧 Send feedback

---

## 📄 License

MIT — free to use, modify, and share.

---

## 🙌 Credits

Built with [FastAPI](https://fastapi.tiangolo.com), [EasyOCR](https://github.com/JaidedAI/EasyOCR), [Groq](https://groq.com), and [marked.js](https://marked.js.org).

Developed by **Nagesha G**

---

<div align="center">

**If SnapSum helped you, give it a ⭐ on GitHub.**

</div>