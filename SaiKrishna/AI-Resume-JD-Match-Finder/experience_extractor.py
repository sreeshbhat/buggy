import re

def extract_experience_years(text):
    text = text.lower()

    # common patterns like "2 years", "3+ years", "1.5 years"
    matches = re.findall(r'(\d+)\s*years', text)

    if not matches:
        return 0.0

    # take the maximum experience mentioned
    years = [float(match[0]) for match in matches]
    return min(years)
