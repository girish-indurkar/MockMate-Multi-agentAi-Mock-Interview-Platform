# 🎤 MockMate

A sophisticated multi-agent AI system that conducts realistic mock interviews across 3 target roles with 3 distinct rounds each. Powered by **Groq API** (`llama-3.1-8b-instant` & `whisper-large-v3-turbo`), featuring personalized background-aware difficulty, voice interaction, single-question card UI, and downloadable PDF transcripts.

---

## 🌟 Key Features

✅ **3 Target Roles**
- **Software Development Engineer (SDE)**
- **Data Scientist**
- **Product Manager (PM)**

✅ **3 Rounds per Role with Distinct Agents**
- **SDE:** Technical (`🤖 Agent 1`) → HR/Behavioral (`🤝 Agent 2`) → Problem-Solving (`🧠 Agent 3`)
- **Data Scientist:** Technical (`🤖 Agent 1`) → HR/Behavioral (`🤝 Agent 2`) → Case Study (`🧠 Agent 3`)
- **PM:** Product Sense (`🤖 Agent 1`) → HR/Behavioral (`🤝 Agent 2`) → Analytics & Strategy (`🧠 Agent 3`)

✅ **Background-Aware Adaptive Difficulty**
- **Automatic Experience Detection:** Parses candidate background (e.g. "fresher / student" vs "5 years backend engineer at Google").
- **Beginner Mode:** Easy to moderate questions for freshers/students with guidance and basic fundamentals.
- **Intermediate & Advanced Modes:** Deep technical probes, system design trade-offs, and practical scale questions for experienced candidates.

✅ **Clean Single-Question Card UI**
- Non-scrolling interface displaying **only the active question** in a glassmorphic card.
- Live Agent badges and Question Counters (`Question X of 6`).
- Previous Q&A stored in state/memory and reviewed upon completion.

✅ **Multi-Modal Interface (Voice & Text)**
- 🗣️ **Voice Output:** Clear MP3 audio generation using `gTTS` with client-side audio playback & caching.
- 🎤 **Voice Input:** Native browser recording using Streamlit `st.audio_input` transcribed in real-time by Groq **Whisper** (`whisper-large-v3-turbo`).
- ✍️ **Text Mode:** Standard text reading and typing support.

✅ **Comprehensive Feedback & PDF Transcripts**
- Detailed round-by-round evaluation and overall performance summary.
- Top 3 Strengths, Areas for Improvement, and Learning Plan.
- 📥 **Downloadable PDF Transcript:** Export a formatted PDF report via `fpdf2` containing complete interview history and feedback.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Streamlit Interface (UI)                    │
│   - Single-Question Card View & Agent Badges             │
│   - Browser Audio Recorder (st.audio_input) & Player     │
│   - Resume & Background Parser                           │
│   - PDF Transcript Generator (fpdf2)                     │
└────────────────────────────┬─────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────┐
│               Interview Orchestrator                      │
│   - Manages 3 rounds & turn-based question flow           │
│   - Tracks state & background difficulty context          │
│   - Calls Evaluator & Coach Agents                        │
└────────────────────────────┬─────────────────────────────┘
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Agent 1      │      │ Agent 2      │      │ Agent 3      │
│ Technical /  │      │ HR &         │      │ Problem-     │
│ Product Sense│      │ Behavioral   │      │ Solving / Case│
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
              ┌─────────────────────────────┐
              │          Groq API           │
              │ - llama-3.1-8b-instant      │
              │ - whisper-large-v3-turbo    │
              └─────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Groq API Key ([Get a free key from console.groq.com](https://console.groq.com))

### Installation

1. **Clone / Navigate to the repository:**
```bash
git clone https://github.com/girish-indurkar/MockMate-Multi-agentAi-Mock-Interview-Platform.git
cd MockMate-Multi-agentAi-Mock-Interview-Platform
```

2. **Set up Virtual Environment (Optional but recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment:**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=gsk_your_groq_api_key_here
   ```

5. **Launch the Application:**
   ```bash
   streamlit run app.py
   ```
   Open your browser at `http://localhost:8501`.

---

## 📖 Usage Guide

### Step 1: Setup Interview
1. Select your target role (**SDE**, **Data Scientist**, or **PM**).
2. Specify your **Background** (e.g., `"Fresher / Computer Science Student"` or `"5 years Backend Engineer"`).
3. (Optional) Upload your resume (**PDF** or **DOCX**).
4. Choose **Voice Mode** or **Text Mode**.
5. Click **🚀 Start Interview**.

### Step 2: Conduct Interview
- Each role consists of 3 distinct rounds (6 questions per round).
- Read/listen to the current question card with the active Agent badge.
- Submit your answer via voice recording or text.
- The system automatically progresses to the next question.

### Step 3: Feedback & Export
- Receive structured coaching report at the end of the interview.
- Download the complete interview report as a **PDF document** or JSON file.

---

## 📝 File Structure

```
ai-mock-interview-coach/
├── app.py                      # Streamlit UI & single-question orchestrator interface
├── interview_agent.py          # Multi-agent orchestrator & background difficulty logic
├── prompts.py                  # Role-specific & round-specific system prompts
├── resume_parser.py            # PDF / DOCX resume parsing utility
├── requirements.txt            # Python dependencies (Streamlit, Groq, gTTS, fpdf2, etc.)
├── .env                        # Environment variables (GROQ_API_KEY)
├── example_interviews.json    # Sample transcript datasets
└── README.md                  # Project documentation
```

---

## 🔧 Dependencies

- `streamlit>=1.45` — Web app framework
- `groq>=0.20` — Fast LLM & Whisper API client
- `python-dotenv>=1.1` — Environment variable loader
- `PyPDF2>=3.0.1` — PDF parser
- `python-docx>=1.1.0` — Word document parser
- `requests>=2.32` — HTTP client
- `gTTS>=2.5.0` — Google Text-to-Speech audio synthesis
- `fpdf2>=2.8.0` — PDF report generator

---

## 📜 License

This project is open-source and available for educational and practice purposes.

*MockMate Platform | © 2026 All rights reserved*
