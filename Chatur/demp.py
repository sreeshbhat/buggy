import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

# -------------------- SETUP --------------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("GROQ_API_KEY missing in .env")
    # st.stop()

client = Groq(api_key=API_KEY)
MODEL = "llama-3.3-70b-versatile"

st.set_page_config(page_title="AI Question Paper Generator")
st.title("🧠 AI Question Paper Generator")

# -------------------- HELPERS --------------------
def detect_language_from_topic(topic: str):
    t = topic.lower()
    if "java" in t:
        return "Java"
    if "python" in t:
        return "Python"
    if "c++" in t:
        return "C++"
    if "c " in t or t.endswith(" c"):
        return "C"
    return None

def is_valid_code(code: str, language: str) -> bool:
    if len(code.strip()) < 20:
        return False

    patterns = {
        "Python": ["def ", ":"],
        "Java": ["class ", "public", ";"],
        "C": ["#include", ";"],
        "C++": ["#include", "using namespace", ";"]
    }
    return any(p in code for p in patterns.get(language, [])) and "main" in code

# -------------------- SESSION STATE --------------------
if "quiz" not in st.session_state:
    st.session_state.quiz = None
if "mcq_done" not in st.session_state:
    st.session_state.mcq_done = False
if "code_done" not in st.session_state:
    st.session_state.code_done = False

# -------------------- USER INPUT --------------------
username = st.text_input("Username")
topic = st.text_input("Topic")
num_mcq = st.number_input("Number of MCQs", 0, 10, 5)
num_code = st.number_input("Number of Coding Questions", 0, 5, 1)

if not username or not topic:
    st.stop()

# -------------------- GENERATE QUIZ --------------------
if st.button("Generate Quiz"):
    st.session_state.mcq_done = False
    st.session_state.code_done = False

    mcqs = []
    codes = []

    # ---------- MCQs ----------
    if num_mcq > 0:
        mcq_prompt = f"""
        Generate {num_mcq} MCQs on "{topic}"
        Format strictly:
        Q1. Question
        A) ...
        B) ...
        C) ...
        D) ...
        Correct: B
        """
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": mcq_prompt}]
        )

        q, opts, corr = None, [], None
        for line in res.choices[0].message.content.splitlines():
            line = line.strip()
            if line.startswith("Q"):
                if q:
                    mcqs.append({"q": q, "opts": opts, "corr": corr})
                q, opts = line, []
            elif line[:2] in ["A)", "B)", "C)", "D)"]:
                opts.append(line)
            elif line.startswith("Correct:"):
                corr = line.split(":")[1].strip()
        if q:
            mcqs.append({"q": q, "opts": opts, "corr": corr})

    # ---------- CODING ----------
    if num_code > 0:
        code_prompt = f"""
        Generate {num_code} coding questions on "{topic}"

        Format:
        ---Problem---
        Statement: ...
        ExpectedLogic: ...
        """
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": code_prompt}]
        )

        for p in res.choices[0].message.content.split("---Question---"):
            if "Statement:" not in p:
                continue
            stmt = p.split("Statement:")[1].split("ExpectedLogic:")[0].strip()
            logic = p.split("ExpectedLogic:")[1].strip()
            codes.append({"stmt": stmt, "logic": logic})

    st.session_state.quiz = {"mcqs": mcqs, "codes": codes}

# -------------------- DISPLAY QUIZ --------------------
if st.session_state.quiz:

    # ===== MCQs =====
    st.markdown("## 📘 MCQs")

    with st.form("mcq_form"):
        for i, q in enumerate(st.session_state.quiz["mcqs"]):
            st.markdown(f"**{q['q']}**")
            st.radio(
                "Choose one:",
                q["opts"],
                index=None,
                key=f"mcq_{i}"
            )
        submit_mcq = st.form_submit_button("Submit MCQs")

    if submit_mcq:
        score = 0
        for i, q in enumerate(st.session_state.quiz["mcqs"]):
            ans = st.session_state.get(f"mcq_{i}")
            if ans:
                if ans == q["corr"]:
                    st.success(f"Q{i+1}: Correct ✅")
                    score += 1
                else:
                    st.error(f"Q{i+1}: Wrong ❌ | Correct Answer: {q['corr']}")
        st.info(f"MCQ Score: {score}/{len(st.session_state.quiz['mcqs'])}")
        st.session_state.mcq_done = True

    # ===== CODING =====
    st.markdown("## 💻 Coding Questions")

    locked_language = detect_language_from_topic(topic)

    for i, prob in enumerate(st.session_state.quiz["codes"]):
        st.markdown(f"**Q{i+1}. {prob['stmt']}**")

        if locked_language:
            language = locked_language
            st.markdown(f"**Language:** {language}")
        else:
            language = st.selectbox(
                "Select Language",
                ["Python", "Java", "C", "C++"],
                key=f"lang_{i}"
            )

        user_code = st.text_area(
            "Write your code:",
            height=200,
            key=f"user_code_{i}"
        )

        if st.button("Evaluate Code", key=f"eval_{i}"):

            if not is_valid_code(user_code, language):
                st.error("❌ Invalid or insufficient code. Please write meaningful code.")
                continue

            eval_prompt = f"""
            You are a STRICT programming evaluator.

            Problem:
            {prob['stmt']}

            Expected Logic:
            {prob['logic']}

            User Language:
            {language}

            User Code:
            {user_code}

            Evaluate and respond EXACTLY in this format:

            Result: PASS or FAIL

            Analysis:
            - Explain where the user's code is correct or incorrect
            - Mention missing logic or mistakes clearly

            Correct Approach:
            - Step-by-step explanation of correct logic

            Reference Solution ({language}):
            - Provide a clean, correct implementation
            """

            res = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": eval_prompt}]
            )

            st.markdown("### 🧠 AI Evaluation Report")
            st.write(res.choices[0].message.content)
            st.session_state.code_done = True

    # ===== FINAL =====
    if st.session_state.mcq_done and (
        not st.session_state.quiz["codes"] or st.session_state.code_done
    ):
        st.success(f"🎉 Quiz Completed by")
