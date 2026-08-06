# 🎤 MockMate - AI Interview Coach

A sophisticated multi-agent AI system that conducts realistic mock interviews across 3 target roles with 3 distinct rounds each. Powered by **Groq API** (`llama-3.1-8b-instant` & `whisper-large-v3-turbo`), featuring personalized background-aware difficulty, voice interaction, single-question card UI, and downloadable PDF transcripts.

## 🚀 Setup and Run Instructions

### Prerequisites
- Python 3.8+
- Groq API Key ([Get a free key from console.groq.com](https://console.groq.com))

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/girish-indurkar/MockMate-Multi-agentAi-Mock-Interview-Platform.git
   cd MockMate-Multi-agentAi-Mock-Interview-Platform
   ```
2. **Set up Virtual Environment:**
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

## 🏗️ Architecture Overview

The system is built on a multi-agent orchestration architecture where different AI personas take turns interviewing the candidate. 

### What Each Agent Does
1. **Agent 1 (Technical / Product Sense Interviewer)**: Focuses on core competencies. For an SDE, this means coding, system design, and algorithms. For a PM, it means product sense and metrics.
2. **Agent 2 (HR & Behavioral Interviewer)**: Evaluates cultural fit, leadership principles, conflict resolution, and soft skills.
3. **Agent 3 (Problem-Solving / Case Study / Analytics Interviewer)**: Tests analytical thinking, unstructured problem solving, and ability to handle ambiguous edge cases.
4. **Coach Agent (Evaluator)**: Operates behind the scenes after the interview concludes. It analyzes the entire transcript to generate comprehensive, actionable feedback, highlighting strengths, areas of improvement, and a learning plan.

### Orchestration
- **`InterviewOrchestrator`**: The central state machine defined in `interview_agent.py`. It manages the flow of the interview, determining when a round ends and the next begins. It passes the conversation context from round to round so agents have memory of past answers.
- **Background-Aware Difficulty**: The orchestrator parses the candidate's background (via resume or text input) and injects this context into the agents' system prompts, ensuring they adjust their expectations (e.g., easier foundational questions for freshers, deep architecture trade-offs for seniors).
- **Streamlit Session State**: Acts as the short-term memory during the active session, tracking current round, question count, UI state, and audio cache.

## ⚖️ Key Design Decisions & Tradeoffs

1. **Groq API for LLM & Whisper**: 
   - *Decision*: Use Groq's fast inference for real-time voice and text interaction.
   - *Tradeoff*: High speed is prioritized over using a massive model with higher latency. `llama-3.1-8b-instant` provides a great balance of conversational reasoning and near-zero latency, crucial for voice interviews.
2. **Single-Question Card UI**:
   - *Decision*: Hide chat history and only display the active question to prevent UI scrolling and keep a clean interface.
   - *Tradeoff*: Reduces cognitive load and simulates a real interview environment where you focus on the current question, but prevents the candidate from re-reading past answers mid-round.
3. **Client-Side TTS & Whisper ASR**:
   - *Decision*: `gTTS` is used for text-to-speech, and Streamlit's native `audio_input` captures voice to be transcribed by Whisper.
   - *Tradeoff*: `gTTS` is simple and free, though less emotionally expressive than premium TTS services. Transcriptions are handled server-side (via API) rather than browser-side to ensure high accuracy and low overhead on the user's machine.
4. **Stateless Agents with Context Injection**:
   - *Decision*: Agents don't maintain their own persistent memory; instead, the Orchestrator injects the necessary conversation history into their prompts.
   - *Tradeoff*: Makes the system highly scalable and stateless, though it consumes more tokens per API call as the conversation grows.

## 📄 Example Interview Transcripts

Here are some abbreviated examples of how the AI adapts to different candidate profiles based on our test data.

### 1. Strong Candidate (SDE, 5 YOE)
**Profile:** 5 years backend experience at Google, strong DSA skills.
**Round:** Technical
- **Agent:** Design a LRU Cache. What's your approach?
- **Candidate:** I'd use a HashMap for O(1) lookups combined with a doubly-linked list to maintain insertion order...
- **Agent:** Good approach. How would you handle concurrency in your LRU Cache?
- **Candidate:** I'd use ReentrantReadWriteLock for thread safety. Read operations can be concurrent, but write operations need exclusive access...
- **Coach Feedback:** Excellent technical fundamentals. Deep understanding of distributed systems and scalability. Could have gone deeper into trade-offs for some design problems.

### 2. Weak Candidate (Data Scientist, Fresher)
**Profile:** Fresher, bootcamp graduate.
**Round:** Technical
- **Agent:** Can you explain the difference between supervised and unsupervised learning?
- **Candidate:** Supervised learning is when you have labels. Unsupervised is when you don't.
- **Agent:** That's correct, but quite brief. Can you give an example of an algorithm for each?
- **Candidate:** Linear regression for supervised. I don't remember any for unsupervised.
- **Coach Feedback:** Needs stronger grasp of fundamental machine learning concepts. Suggest reviewing common algorithms (K-Means, PCA) and practicing articulating technical explanations more thoroughly.

### 3. Tricky/Edge Case Candidate (PM)
**Profile:** Experienced PM transitioning from Marketing, tends to deflect technical questions.
**Round:** Product Sense
- **Agent:** How would you design a new metric to track user engagement for a newly launched feature?
- **Candidate:** I'd look at how many people tweeted about it and the general sentiment of our marketing campaigns.
- **Agent:** While marketing sentiment is useful, how would you measure in-app product engagement using our internal telemetry?
- **Candidate:** I usually leave the data logging to the engineering team. As long as users are happy, that's what matters.
- **Coach Feedback:** Candidate deflects analytical questions. Needs to demonstrate product-specific data competency rather than relying solely on marketing metrics. Must show willingness to define concrete product telemetry.
