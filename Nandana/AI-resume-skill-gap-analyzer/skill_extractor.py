from data.skills import SKILLS_DB

def extract_skills(resume_text):
    found = []
    for skill in SKILLS_DB:
        if skill in resume_text:
            found.append(skill)
    return list(set(found))