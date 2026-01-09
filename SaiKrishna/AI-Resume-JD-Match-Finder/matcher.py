from skill_extractor import extract_skills
from experience_extractor import extract_experience_years

def calculate_match(resume_text, job_text):
    # --- Skill extraction ---
    resume_skills = set(extract_skills(resume_text))
    job_skills = set(extract_skills(job_text))

    matched = resume_skills.intersection(job_skills)
    missing = resume_skills - job_skills

    # --- Skill score ---
    skill_score = (len(matched) / len(job_skills)) * 100

    # --- Experience extraction ---
    resume_exp = extract_experience_years(resume_text)
    job_exp = extract_experience_years(job_text)

    # --- Experience score ---
    if job_exp == 0:
        exp_score = 100  # no requirement mentioned
    elif resume_exp >= job_exp:
        exp_score = 100
    else:
        exp_score = (resume_exp / job_exp) * 100

    # --- Final weighted score ---
    final_score = round((0.3 * skill_score) + (0.7 * exp_score), 2)

    explanation = {
        "matched_skills": list(matched),
        "missing_skills": list(missing),
        "resume_experience": resume_exp,
        "required_experience": job_exp,
        "experience_match": round(exp_score, 2)
    }

    return final_score, explanation
