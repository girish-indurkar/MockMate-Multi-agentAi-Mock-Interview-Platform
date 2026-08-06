"""
MockMate - Streamlit Application with Voice Support
"""

import streamlit as st
import os
from dotenv import load_dotenv
import tempfile
from interview_agent import InterviewOrchestrator
from resume_parser import extract_resume_info, format_resume_context
from io import BytesIO
import json
from gtts import gTTS
from fpdf import FPDF
from datetime import datetime

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="MockMate",
    page_icon="🎤",
    layout="wide"
)

# Agent display names per round
AGENT_LABELS = {
    "Technical": "🤖 Agent 1 — Technical Interviewer",
    "HR": "🤝 Agent 2 — HR & Behavioral Interviewer",
    "Problem-Solving": "🧠 Agent 3 — Problem-Solving Interviewer",
    "Case Study": "🧠 Agent 3 — Case Study Interviewer",
    "Product Sense": "🤖 Agent 1 — Product Sense Interviewer",
    "Analytics & Strategy": "🧠 Agent 3 — Analytics & Strategy Interviewer",
}

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], .main {
        font-family: 'Outfit', sans-serif !important;
        overflow: hidden !important;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    header[data-testid="stHeader"], footer {
        display: none !important;
    }
    
    .question-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px;
        border-radius: 20px;
        margin: 10px auto;
        max-width: 800px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.12);
    }
    
    .agent-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 16px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.10) 100%);
        border: 1px solid rgba(99, 102, 241, 0.25);
        color: #a5b4fc;
    }
    
    .question-counter {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 500;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #94a3b8;
        float: right;
    }
    
    .round-header {
        text-align: center;
        margin-bottom: 8px;
    }
    
    .feedback-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.03) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(16, 185, 129, 0.15);
        padding: 28px;
        border-radius: 16px;
        margin: 15px 0;
        box-shadow: 0 8px 32px 0 rgba(16, 185, 129, 0.05);
    }
    
    .stButton > button {
        width: 100%;
        padding: 12px 24px !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        border: none !important;
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.45) !important;
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%) !important;
        color: white !important;
    }
    .stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* Secondary buttons in sidebar */
    div[data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.08) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "api_key" not in st.session_state:
    st.session_state.api_key = os.getenv("GROQ_API_KEY")
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "current_round" not in st.session_state:
    st.session_state.current_round = 0
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
if "interview_data" not in st.session_state:
    st.session_state.interview_data = {"rounds": []}

# Helper Functions
def generate_audio_bytes(text: str) -> bytes:
    """Generate MP3 audio bytes for the given text using gTTS"""
    try:
        clean_text = text.replace("🤖", "").replace("🎤", "").replace("*", "").replace("`", "")
        tts = gTTS(text=clean_text, lang='en', tld='com')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception as e:
        st.error(f"Error in speech generation: {e}")
        return b""

def transcribe_audio_groq(audio_file) -> str:
    """Transcribe audio file using Groq's whisper-large-v3-turbo model"""
    try:
        orchestrator = st.session_state.orchestrator
        audio_bytes = audio_file.read()
        file_name = audio_file.name if hasattr(audio_file, "name") else "audio.wav"
        
        transcription = orchestrator.agent.client.audio.transcriptions.create(
            file=(file_name, audio_bytes),
            model="whisper-large-v3-turbo"
        )
        return transcription.text
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return ""

def sanitize_for_pdf(text: str) -> str:
    """Sanitize text to be safely encodable in standard FPDF Latin-1 fonts."""
    if not text:
        return ""
    char_map = {
        '“': '"', '”': '"', '‘': "'", '’': "'",
        '—': '-', '–': '-', '…': '...',
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
        'θ': 'theta', 'λ': 'lambda', 'μ': 'micro', 'π': 'pi',
        'σ': 'sigma', 'τ': 'tau', 'ω': 'omega',
        'Δ': 'Delta', 'Ω': 'Omega', '∑': 'Sum', '∏': 'Product',
        '≈': 'approx', '≠': '!=', '≤': '<=', '≥': '>=',
        '•': '*', '·': '*', '°': ' deg',
    }
    for old, new in char_map.items():
        text = text.replace(old, new)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_transcript(interview_data: dict, role: str, feedback: str, background: str = "") -> bytes:
    """Generate a clean PDF transcript of the interview."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # Title Page
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "MockMate Interview Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "", 14)
    pdf.cell(0, 10, f"Role: {sanitize_for_pdf(role)}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    if background:
        pdf.cell(0, 10, f"Background: {sanitize_for_pdf(background)}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    
    # Rounds
    for rd in interview_data.get("rounds", []):
        pdf.set_font("Helvetica", "B", 16)
        round_title = f"Round: {rd['round_name']}"
        agent_label = AGENT_LABELS.get(rd["round_name"], "")
        if agent_label:
            agent_clean = sanitize_for_pdf(agent_label).strip()
            if "Agent" in agent_clean:
                round_title += f"  ({agent_clean})"
        
        pdf.cell(0, 12, sanitize_for_pdf(round_title), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        
        questions = rd.get("questions", [])
        answers = rd.get("answers", [])
        
        for i, q in enumerate(questions):
            pdf.set_font("Helvetica", "B", 11)
            q_text = sanitize_for_pdf(f"Q{i+1}: {q}")
            pdf.multi_cell(0, 7, q_text)
            pdf.ln(2)
            
            if i < len(answers):
                pdf.set_font("Helvetica", "", 11)
                a_text = sanitize_for_pdf(f"Answer: {answers[i]}")
                pdf.multi_cell(0, 7, a_text)
            pdf.ln(6)
        
        pdf.ln(6)
    
    # Feedback Section
    if feedback:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 14, "Comprehensive Feedback", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        pdf.set_font("Helvetica", "", 11)
        clean_feedback = sanitize_for_pdf(feedback.replace("**", "").replace("*", ""))
        pdf.multi_cell(0, 7, clean_feedback)
    
    return bytes(pdf.output())


def process_answer(orchestrator, current_round, round_data, current_question, answer):
    """Process an answer submission - shared logic for voice and text modes."""
    if st.session_state.question_count < 5:
        next_q = orchestrator.answer_question(
            current_round, current_question, answer, st.session_state.question_count
        )
        round_data["questions"].append(next_q)
        round_data["answers"].append(answer)
        st.session_state.question_count += 1
    else:
        orchestrator.submit_final_answer(current_round, current_question, answer)
        round_data["answers"].append(answer)
        st.session_state.current_round += 1
        st.session_state.question_count = 0
    st.rerun()

#  Header 

if not st.session_state.interview_started:
    st.title("🎤 MockMate")
    st.subheader("Multi-Agent AI Interview Preparation Platform")
    st.markdown("Prepare for your dream role with AI-powered practice interviews!")

#  Sidebar 

with st.sidebar:
    st.title("🎤 MockMate")
    st.header("⚙️ Setup")
    
    api_key = st.session_state.api_key
    
    if not st.session_state.interview_started:
        # Role Selection
        role = st.selectbox(
            "Select Target Role",
            ["SDE", "Data Scientist", "Product Manager"],
            help="Choose the position you're preparing for"
        )
        
        # Background
        background = st.text_area(
            "Background",
            placeholder="E.g., Fresher / Student / 5 years backend engineer at Google...",
            help="Share your background — this adjusts question difficulty"
        )
        
        # Resume Upload (optional)
        resume_file = st.file_uploader(
            "Upload Resume (Optional)",
            type=["pdf", "docx"],
            help="PDF or DOCX format"
        )
        
        resume_context = ""
        if resume_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file.name)[1]) as tmp_file:
                tmp_file.write(resume_file.getbuffer())
                tmp_path = tmp_file.name
            
            try:
                resume_info = extract_resume_info(tmp_path)
                resume_context = format_resume_context(resume_info)
                st.success("✅ Resume uploaded successfully!")
            except Exception as e:
                st.error(f"Error parsing resume: {e}")
            finally:
                os.unlink(tmp_path)
        
        # Interview Type
        interview_type = st.radio(
            "Interview Type",
            ["Voice (AI speaks & you speak)", "Text (AI types & you type)"],
            help="Choose how you want to interact"
        )
        
        # Start Button
        if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
            if not api_key:
                st.error("❌ Groq API Key not found in environment variables. Please add it to your .env file!")
            else:
                st.session_state.interview_started = True
                st.session_state.role = role
                st.session_state.background = background
                st.session_state.resume_context = resume_context
                st.session_state.interview_type = interview_type
                st.session_state.orchestrator = InterviewOrchestrator(
                    api_key=api_key,
                    role=role,
                    resume_context=resume_context,
                    background=background
                )
                st.rerun()
    else:
        st.success("✅ Interview in Progress")
        st.markdown(f"**Role:** {st.session_state.role}")
        st.markdown(f"**Type:** {st.session_state.interview_type}")
        if st.session_state.get("background"):
            st.markdown(f"**Background:** {st.session_state.background}")
        difficulty = st.session_state.orchestrator.agent.difficulty if "orchestrator" in st.session_state else "—"
        st.markdown(f"**Difficulty:** {difficulty.capitalize()}")
        
        if st.button("🔄 Reset Interview", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Main Interview Loop 

if st.session_state.interview_started:
    if "orchestrator" not in st.session_state:
        st.session_state.interview_started = False
        st.rerun()
    orchestrator = st.session_state.orchestrator
    all_rounds = orchestrator.get_all_rounds()
    
    # Progress indicator
    total_questions = len(all_rounds) * 6
    answered = st.session_state.current_round * 6 + st.session_state.question_count
    progress_val = min(answered / total_questions, 1.0) if total_questions > 0 else 0.0
    st.progress(progress_val)
    
    if st.session_state.current_round < len(all_rounds):
        current_round = all_rounds[st.session_state.current_round]
        
        # Initialize round data
        if not st.session_state.interview_data["rounds"] or st.session_state.interview_data["rounds"][-1]["round_name"] != current_round:
            st.session_state.interview_data["rounds"].append({
                "round_name": current_round,
                "questions": [],
                "answers": []
            })
        
        round_data = st.session_state.interview_data["rounds"][-1]
        
        # Generate first question if needed
        if not round_data["questions"]:
            with st.spinner("🤖 Generating first question..."):
                try:
                    question = orchestrator.start_round(current_round)
                    round_data["questions"].append(question)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error generating question: {e}")
                    st.stop()
        
        current_question = round_data["questions"][st.session_state.question_count]
        agent_label = AGENT_LABELS.get(current_round, f"🤖 Interviewer — {current_round}")
        
        # Round header + Agent badge 
        st.markdown(f"<div class='round-header'><h2>Round {st.session_state.current_round + 1}: {current_round}</h2></div>", unsafe_allow_html=True)
        
        #  Question Card (single question, centered)
        st.markdown(f"""
        <div class='question-card'>
            <span class='agent-badge'>{agent_label}</span>
            <span class='question-counter'>Question {st.session_state.question_count + 1} of 6</span>
            <div style='clear:both; margin-top: 16px;'>
                <p style='font-size: 18px; line-height: 1.7;'>{current_question}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        #  Answer Controls (directly below question)
        if st.session_state.interview_type.startswith("Voice"):
            # Audio playback
            should_autoplay = False
            if st.session_state.get("last_spoken_question") != current_question:
                should_autoplay = True
                st.session_state.last_spoken_question = current_question
            elif st.session_state.get("force_replay", False):
                should_autoplay = True
                st.session_state.force_replay = False
            
            if "audio_cache" not in st.session_state:
                st.session_state.audio_cache = {}
            
            if current_question not in st.session_state.audio_cache:
                with st.spinner("Generating question audio..."):
                    audio_bytes = generate_audio_bytes(current_question)
                    st.session_state.audio_cache[current_question] = audio_bytes
            else:
                audio_bytes = st.session_state.audio_cache[current_question]
            
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3", autoplay=should_autoplay)
            
            col_replay, col_spacer = st.columns([1, 3])
            with col_replay:
                if st.button("🔊 Replay Question"):
                    st.session_state.force_replay = True
                    st.rerun()
            
            # Audio input
            audio_value = st.audio_input(
                "🎤 Record your answer",
                key=f"audio_{st.session_state.current_round}_{st.session_state.question_count}"
            )
            
            if audio_value is not None:
                if st.button("✅ Submit Voice Answer", use_container_width=True, type="primary"):
                    with st.spinner("Transcribing and processing your answer..."):
                        answer = transcribe_audio_groq(audio_value)
                        if answer:
                            st.info(f"Transcribed: *{answer}*")
                            process_answer(orchestrator, current_round, round_data, current_question, answer)
                        else:
                            st.error("❌ Could not transcribe audio. Please try again.")
        else:
            # Text mode
            answer = st.text_area(
                "✍️ Your Answer",
                height=100,
                placeholder="Type your answer here...",
                key=f"text_{st.session_state.current_round}_{st.session_state.question_count}"
            )
            
            if st.button("✅ Submit Answer", use_container_width=True, type="primary"):
                if answer and answer.strip():
                    with st.spinner("Processing answer..."):
                        process_answer(orchestrator, current_round, round_data, current_question, answer)
    
    else:
        #  Interview Complete 
        st.success("✅ Interview Complete!")
        st.header("📊 Your Feedback")
        
        # Generate feedback (cached in session state)
        if "final_feedback" not in st.session_state:
            with st.spinner("🏆 Coach Agent is generating your comprehensive feedback..."):
                try:
                    st.session_state.final_feedback = st.session_state.orchestrator.agent.get_final_feedback()
                except Exception as e:
                    st.session_state.final_feedback = f"Error generating feedback: {e}"
        
        feedback = st.session_state.final_feedback
        
        st.markdown("<div class='feedback-box'>", unsafe_allow_html=True)
        st.markdown(feedback)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # PDF Download
        st.markdown("---")
        with st.spinner("Generating PDF transcript..."):
            pdf_bytes = generate_pdf_transcript(
                st.session_state.interview_data,
                st.session_state.role,
                feedback,
                st.session_state.get("background", "")
            )
        
        st.download_button(
            "📥 Download Interview Transcript (PDF)",
            pdf_bytes,
            f"interview_{st.session_state.role}_{datetime.now().strftime('%Y%m%d')}.pdf",
            "application/pdf",
            use_container_width=True
        )
        
        # Review by Round
        st.markdown("---")
        st.subheader("📝 Review by Round")
        
        for round_data in st.session_state.interview_data["rounds"]:
            agent_lbl = AGENT_LABELS.get(round_data["round_name"], "")
            with st.expander(f"🔍 {round_data['round_name']} — {agent_lbl}"):
                for i, (q, a) in enumerate(zip(round_data["questions"], round_data["answers"])):
                    st.markdown(f"**Q{i+1}:** {q}")
                    st.markdown(f"**Your Answer:** {a}")
                    st.markdown("---")

# Footer
st.markdown("---")
st.markdown("MockMate | © 2026 All rights are reserved")
