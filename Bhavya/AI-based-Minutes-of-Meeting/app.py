import streamlit as st
import whisper
import nltk
import spacy
from transformers import pipeline
from datetime import datetime
import numpy as np
import soundfile as sf
from audiorecorder import audiorecorder

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI MOM Generator", layout="centered")
st.title("📝 AI-Based Minutes of Meeting Generator")

# ---------------- NLP SETUP ----------------
nltk.download("punkt")
nlp = spacy.load("en_core_web_sm")

# ---------------- LOAD MODELS (CACHED) ----------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")

@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="facebook/bart-large-cnn", device=-1)

@st.cache_resource
def load_sentiment():
    return pipeline("sentiment-analysis")

whisper_model = load_whisper()
summarizer = load_summarizer()
sentiment_model = load_sentiment()

# ---------------- CORE FUNCTIONS ----------------
def speech_to_text(audio_path):
    st.write("🔊 Transcribing audio...")
    result = whisper_model.transcribe(audio_path)
    return result["text"]

def clean_text(text):
    doc = nlp(text)
    return " ".join(sent.text.strip() for sent in doc.sents)

# -------- MEETING TYPE DETECTION --------
def detect_meeting_type(text):
    t = text.lower()

    if any(w in t for w in ["interview", "practice", "training", "guidance", "learn"]):
        return "Training / Guidance Session"

    if any(w in t for w in ["approve", "decision", "finalize", "deadline"]):
        return "Decision-Making Meeting"

    if any(w in t for w in ["plan", "roadmap", "strategy"]):
        return "Planning Meeting"

    return "General Discussion"

# -------- PROFESSIONAL SUMMARY --------
def generate_professional_summary(text, meeting_type):
    st.write("🧠 Generating structured summary...")
    summary = summarize_text(text)

    sentences = summary.split(". ")
    concise = ". ".join(sentences[5:]).strip()

    return (
        f"The meeting was conducted as a {meeting_type}. "
        f"{concise}."
    )

def summarize_text(text):
    max_chunk_length = 800
    sentences = text.split(". ")
    chunks, chunk = [], ""

    for s in sentences:
        if len(chunk) + len(s) <= max_chunk_length:
            chunk += s + ". "
        else:
            chunks.append(chunk)
            chunk = s + ". "

    if chunk:
        chunks.append(chunk)

    summaries = []
    for c in chunks:
        out = summarizer(c, max_length=120, min_length=40, do_sample=False)
        summaries.append(out[0]["summary_text"])

    return " ".join(summaries)

# -------- CLEAN TOPIC EXTRACTION --------
def extract_clean_topics(text):
    st.write("🔑 Extracting key topics...")
    bad_topics = {"a little bit", "these words", "something", "anything"}
    topics = set()

    for chunk in nlp(text).noun_chunks:
        phrase = chunk.text.lower().strip()
        if (
            len(phrase.split()) >= 10
            and phrase not in bad_topics
            and not phrase.startswith(("a ", "the ", "some "))
        ):
            topics.add(phrase)

    return list(topics)[:7]

# -------- STRICT ACTION ITEMS --------
def extract_strict_action_items(text):
    st.write("📌 Extracting action items...")
    actions = []

    for sent in nlp(text).sents:
        s = sent.text.lower()
        if any(w in s for w in ["should", "must", "need to", "required to", "practice", "prepare"]):
            actions.append(sent.text.strip())

    return actions

# -------- POST-PROCESSING VALIDATION --------
def validate_mom(summary, topics, actions, sentiment):
    # Trim summary if too long
    if len(summary.split()) > 120:
        summary = " ".join(summary.split()[:120]) + "..."

    # Remove weak topics
    topics = [
        t for t in topics
        if len(t.split()) >= 2 and not t.startswith(("a ", "the "))
    ]

    # Ensure actions are real actions
    valid_actions = []
    for a in actions:
        if any(w in a.lower() for w in ["should", "must", "practice", "prepare"]):
            valid_actions.append(a)

    # Correct sentiment if mismatch
    if any(w in summary.lower() for w in ["guidance", "confidence", "preparation", "training"]):
        sentiment = "POSITIVE"

    sentiment = "POSITIVE"

    return summary, topics, valid_actions, sentiment

# -------- FINAL MOM FORMAT --------
def generate_mom(meeting_type, summary, topics, actions, sentiment):
    mom = f"""
MINUTES OF MEETING (MOM)
------------------------
Date: {datetime.now().strftime("%d-%m-%yY")}
Time: {datetime.now().strftime("%H:%M")}

MEETING TYPE:
{meeting_type}

SUMMARY:
{summary}

KEY TOPICS DISCUSSED:
"""
    for t in topics:
        mom += f"- {t}\n"

    mom += "\nACTION ITEMS:\n"
    if actions:
        for i, a in enumerate(actions, 1):
            mom += f"{i}. {a}\n"
    else:
        mom += "No explicit action items identified.\n"

    mom += f"\nMEETING SENTIMENT: {sentiment}\n"
    return mom

# ---------------- UI ----------------
st.subheader("🎙️ Option 1: Record Live Audio")

audio = audiorecorder("Start Recording", "Stop Recording")
audio_path = None

if len(audio) > 0:
    audio_np = np.array(audio)
    sf.write("live_audio.wav", audio_np, 44100)
    audio_path = "live_audio.wav"
    st.audio(audio_path)

st.subheader("📂 Option 2: Upload Audio File")

uploaded_file = st.file_uploader("Upload MP3 or WAV", type=["mp3", "wav"])

if uploaded_file:
    with open("uploaded_audio.wav", "w") as f:
        f.write(uploaded_file.read())
    audio_path = "uploaded_audio.wav"
    st.audio(audio_path)

# ---------------- PROCESS ----------------
if audio_path and st.button("🚀 Generate MOM"):
    with st.spinner("Processing meeting..."):
        transcript = speech_to_text(audio_path)
        cleaned_text = clean_text(transcript)

        meeting_type = detect_meeting_type(cleaned_text)
        summary = generate_professional_summary(cleaned_text, meeting_type)
        topics = extract_clean_topics(cleaned_text)
        actions = extract_strict_action_items(cleaned_text)
        sentiment = sentiment_model(cleaned_text[:512])[0]["label"]

        summary, topics, actions, sentiment = validate_mom(
            summary, topics, actions, sentiment
        )

        mom_text = generate_mom(
            meeting_type, summary, topics, actions, sentiment
        )

    st.success("✅ MOM Generated Successfully")
    st.text(mom_text)

    st.download_button(
        "⬇️ Download MOM",
        mom_text,
        "output_mom.txt",
        mime="text/plain"
    )
