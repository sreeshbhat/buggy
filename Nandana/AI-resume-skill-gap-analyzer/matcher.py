from data.job_roles import JOB_ROLES

def analyze_skills(candidate_skills, role):
    required = JOB_ROLES.get(role, [])
    matched = list(set(candidate_skills) & set(required))
    missing = list(set(required) - set(candidate_skills))
    return matched, missing