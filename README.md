# 📸 SnapSum

> AI-powered screenshot analyzer. Upload any screenshot → extract text → summarize → translate → chat with it.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit&logoColor=white)
![EasyOCR](https://img.shields.io/badge/EasyOCR-OCR-green)
![Groq](https://img.shields.io/badge/Groq-LLM-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Version](https://img.shields.io/badge/version-1.0-blue)

---

## 🧠 What It Does

Drop in any screenshot — a chat, an article, a receipt, a roadmap — and SnapSum will:

1. **Extract** the text using OCR
2. **Translate** it to your chosen language
3. **Summarize** it into 3 concise bullet points
4. **Explain** what, why, and how — like a tutor
5. **Answer** your questions in a chat interface
6. **Export** everything as TXT or PDF

All wrapped in a multi-page Streamlit app with user accounts and a clean UI.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔐 **User accounts** | Register, login, and logout |
| 🏠 **Home page** | Landing screen with feature overview |
| 🌐 **21 output languages** | Hindi, Telugu, Tamil, Spanish, French, Arabic, Chinese, Japanese, and more |
| 🔍 **OCR extraction** | Reads text from PNG/JPG/JPEG screenshots |
| 🌐 **Translate button** | Translate the extracted text to any supported language |
| 🤖 **AI summarization** | 3-bullet summary in your chosen language |
| 🧠 **Explain mode** | What / Why / How breakdown of the content |
| 💬 **Chat interface** | Multi-chat Q&A with per-chat history |
| 📚 **Chat management** | Create new chats, switch between them |
| ⬇️ **Export options** | Download summaries as `.txt` or `.pdf` |
| 🎁 **Free trial** | 10 uses per session |

---

## 🎬 How It Works

```
[Your Screenshot]
       ↓ (Pillow reads image)
[Image Object]
       ↓ (EasyOCR scans pixels)
[Raw Text]
       ↓ (Groq LLM: summarize / translate / explain / answer)
[Output in chosen language]
       ↓ (Streamlit renders)
[Web Page in Browser]
```

---

## 🛠️ Tech Stack

| Layer | Tool |
|-------|------|
| UI | [Streamlit](https://streamlit.io) |
| Auth | [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator) |
| OCR | [EasyOCR](https://github.com/JaidedAI/EasyOCR) |
| LLM | [Groq](https://groq.com) — `openai/gpt-oss-120b` |
| Image | [Pillow](https://python-pillow.org) |
| PDF | [fpdf2](https://py-pdf.github.io/fpdf2/) |
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
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # macOS / Linux
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
```

> ⚠️ **Never commit `.env`.** It's already in `.gitignore`.

### 5. Run

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**.

---

## 🎯 Usage

1. **Register** a new account from the home page
2. **Login** with your credentials
3. Choose an **output language** (21 options)
4. **Upload** a screenshot
5. Use the action buttons:
   - 🌐 **Translate** — translate extracted text
   - ✨ **Summarize** — 3-bullet summary + download
   - 🧠 **Explain** — what / why / how breakdown
6. **Chat** with the image using the chat box below
7. **Create new chats** from the sidebar to organize different images

---

## 📁 Project Structure

```
Snapsum/
├── app.py                  # Main Streamlit app
├── requirements.txt        # Python dependencies
├── auth_config.yaml        # User credentials (gitignored, auto-generated)
├── .env                    # Your secrets (gitignored)
├── .gitignore
├── README.md
└── venv/                   # Virtual environment (gitignored)
```

---

## 🔒 Security

- API keys loaded from `.env` via `python-dotenv`
- User passwords hashed with bcrypt (via `streamlit-authenticator`)
- `.env` and `auth_config.yaml` are both gitignored
- No user data leaves your machine except OCR text sent to Groq's API

---

## 🗺️ Roadmap

- [x] **v0.1** — Working MVP (upload, OCR, summarize, Q&A)
- [x] **v0.2** — Sidebar, session history, download, two-column layout
- [x] **v0.3** — Multi-page UI, user auth, translation, explanation, chat
- [x] **v1.0** — Official release: user accounts, 21 languages, translate, explain, chat, PDF export
- [ ] **v1.1** — SQLite persistence (chats + usage counters survive refresh)
- [ ] **v1.2** — Batch upload (multiple images)
- [ ] **v1.3** — Streaming responses (word-by-word display)
- [ ] **v1.4** — Settings panel (model picker, temperature)
- [ ] **v2.0** — Deployment to Streamlit Cloud + public demo

---

## ⚠️ Known Limitations

- Usage counter resets on page refresh (SQLite coming in v1.1)
- Chat history is session-only (SQLite coming in v1.1)
- OCR runs in English only (translation handles output language)
- User store is a YAML file — fine for demo, not production scale

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT — free to use, modify, and share. See [LICENSE](LICENSE) if present.

---

## 🙌 Credits

Built with [Streamlit](https://streamlit.io), [EasyOCR](https://github.com/JaidedAI/EasyOCR), [Groq](https://groq.com), and [streamlit-authenticator](https://github.com/mkhorasani/Streamlit-Authenticator).

---

## ⭐ Support

If this project helped you, give it a star on GitHub — it helps others find it.