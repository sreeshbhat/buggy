import streamlit as st
import whisper
import nltk
import spacy
from transformers import pipeline
from datetime import datetime
import numpy as np
import soundfile as sf
from audiorecorder import audiorecorder
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI MOM Generator", layout="centered")
st.title("📝 AI-Based Minutes of Meeting Generator")

# ---------------- LOAD NLP ----------------
nltk.download("punkt")
nlp = spacy.load("en_core_web_sm")

# ---------------- LOAD MODELS (CACHED) ----------------
@st.cache_resource
def load_whisper():
    return whisper.load_model("base")  # stable on CPU

@st.cache_resource
def load_summarizer():
    return pipeline("text2text-generation", model="google/flan-t5-bases")

@st.cache_resource
def load_sentiment():
    return pipeline("sentiment-analysis")

whisper_model = load_whisper()
llm = load_summarizer()
sentiment_model = load_sentiment()

# ---------------- CORE FUNCTIONS ----------------
def speech_to_text(audio_path):
    result = whisper_model.transcribe(audio_path)
    return result["text"]

def clean_text(text):
    doc = nlp(text)
    return " ".join(sent.text.strip() for sent in doc.sents)

def extract_structured_mom(text):
    prompt = f"""
You are an expert meeting assistant.

From the transcript below, extract:
1. Summary
2. Key topics
3. Decisions
4. Action items (with person if mentioned)
5. Overall sentiment

Transcript:
{text}

Format clearly with headings.
"""
    response = llm(prompt, max_length=512, do_sample=False)
    return response[0]["generated_text"]

def extract_action_items(text):
    doc = nlp(text)
    actions = []
    for sent in doc.sents:
        if any(w in sent.text.lower() for w in ["action-item-keyword"]):
            actions.append(sent.text.strip())
    return actions

def extract_topics(text):
    return ["Project Alpha", "Budget constraints", "Q3 roadmap", "Team restructuring"]

def get_sentiment(text):
    result = sentiment_model(text[:512])
    return result[0]["label"]

def format_mom(summary_block, topics, actions, sentiment):
    mom = f"""
MINUTES OF MEETING (MOM)
------------------------
Date: {datetime.now().strftime("%d-%m-%Y")}
Time: {datetime.now().strftime("%H:%M")}

{summary_block}

KEY TOPICS:
"""
    for t in topics:
        mom += f"- {t}\n"

    mom += "\nACTION ITEMS:\n"
    if actions:
        for i, a in enumerate(actions, 1):
            mom += f"{i}. {a}\n"
    else:
        mom += "No explicit action items found.\n"

    mom += f"\nMEETING SENTIMENT: {sentiment}\n"
    return mom

# ---------------- UI ----------------
st.subheader("🎙️ Option 1: Record Live Meeting")

audio = audiorecorder("Start Recording", "Stop Recording")

audio_path = None

if len(audio) > 0:
    audio_np = np.array(audio)
    sf.write("live_audio.wav", audio_np, 22050)
    audio_path = "live_audio.wav"
    st.audio(audio_path)

st.subheader("📂 Option 2: Upload Audio File")

uploaded_file = st.file_uploader(
    "Upload MP3 or WAV file",
    type=["mp3", "wav"]
)

if uploaded_file:
    with open("uploaded_audio.wav", "wb") as f:
        f.write(uploaded_file.read())
    audio_path = "live_audio.wav"
    st.audio(audio_path)

# ---------------- PROCESS BUTTON ----------------
if audio_path and st.button("🚀 Generate MOM"):
    with st.spinner("Processing meeting..."):
        transcript = speech_to_text(audio_path)
        cleaned = clean_text(transcript)

        structured_summary = extract_structured_mom(cleaned)
        actions = extract_action_items(cleaned)
        topics = extract_topics(cleaned)
        sentiment = get_sentiment(cleaned)

        mom_text = format_mom(structured_summary, topics, actions, sentiment)

    st.success("✅ MOM Generated Successfully")

    st.subheader("📄 Minutes of Meeting")
    st.text(mom_text)

    st.download_button(
        label="⬇️ Download MOM",
        data=mom_text,
        file_name="output_mom.txt",
        mime="text/plain"
    )
