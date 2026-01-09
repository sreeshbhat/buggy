import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq

# -------------------- SETUP --------------------
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    st.error("GROQ_API_KEY missing in .env")
    st.stop()

client = Groq(api_key=API_KEY)
MODEL = "llama-3.1-70b-versatile"

st.set_page_config(page_title="AI Question Paper Generator")
st.title("🧠 AI Question Paper Generator")

# -------------------- HELPERS --------------------
def detect_language_from_topic(topic: str):
    t = topic.lower()
    if "javascript" in t:
        return "Java"
    if "python" in t:
        return "Python"
    if "c++" in t:
        return "C++"
    if "c " in t or t.endswith(" c"):
        return "C"
    return None


def looks_like_attempt(code: str) -> bool:
    """
    Very light check:
    - empty or very small input = no attempt
    - otherwise treat as attempt
    """
    return len(code.strip()) >= 8


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
            if line.startswith("A"):
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
        ExpectedLogic: Describe the solution idea in words (not code).
        """

        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": code_prompt}]
        )

        for p in res.choices[0].message.content.split("---Problem---"):
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
            st.radio("Choose one:", q["opts"], index=None, key=f"mcq_{i}")
        submit_mcq = st.form_submit_button("Submit MCQs")

    if submit_mcq:
        score = 0
        for i, q in enumerate(st.session_state.quiz["mcqs"]):
            ans = st.session_state.get(f"mcq_{i}")
            if ans and ans.startswith(q["corr"]):
                st.success(f"Q{i+1}: Correct ✅")
                # score += 1
            else:
                st.error(f"Q{i+1}: Wrong ❌ | Correct: {q['corr']}")
        st.info(f"MCQ Score: {score}/{len(st.session_state.quiz['mcqs'])}")
        st.session_state.mcq_done = True

    # ===== CODING =====
    st.markdown("## 💻 Coding Questions")

    locked_language = detect_language_from_topic(topic)

    for i, prob in enumerate(st.session_state.quiz["codes"]):
        st.markdown(f"**Q{i+1}. {prob['stmt']}**")

        language = locked_language or st.selectbox(
            "Select Language",
            ["Python", "Java", "C", "C++"],
            key=f"lang_{i}"
        )

        st.markdown(f"**Language:** {language}")

        user_code = st.text_area(
            "Write your code (or try anything):",
            height=220,
            key=f"user_code_{i}"
        )

        if st.button("Evaluate Code", key=f"eval_{i}"):

            attempted = looks_like_attempt(user_code)

            if not attempted:
                # Evaluation mode
                eval_prompt = f"""
                You are an expert programming evaluator.

                RULES:
                - Judge ONLY logical correctness
                - Program-style and function-style both allowed
                - Variable names, formatting, and type hints do NOT matter
                - If logic solves the problem → PASS
                - Otherwise → FAIL

                Problem:
                {prob['stmt']}

                Expected Logic:
                {prob['logic']}

                User Language: {language}

                User Code:
                {user_code}

                Respond EXACTLY in this format:

                Result: PASS or FAIL
                Issue:
                - Explanation

                Correct Solution ({language}):
                <correct code>
                """
            else:
                # Help / Tutor mode
                eval_prompt = f"""
                You are a friendly programming tutor.

                The user is a beginner and could not write correct code.

                TASK:
                - Explain how to approach the problem step-by-step
                - Then show a correct solution in {language}
                - Be encouraging and simple

                Problem:
                {prob['stmt']}

                Expected Logic:
                {prob['logic']}

                User Input:
                {user_code}

                Respond EXACTLY in this format:

                Guidance:
                - Step-by-step explanation

                Correct Solution ({language}):
                <correct code>
                """

            res = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": eval_prompt}]
            )

            st.markdown("### 🧠 AI Feedback")
            st.code(res.choices[0].message.content)
            st.session_state.code_done = True

    # ===== FINAL =====
    if st.session_state.mcq_done and (
        not st.session_state.quiz["codes"] or st.session_state.code_done
    ):
        st.success(f"🎉 Quiz Completed by {username}")
