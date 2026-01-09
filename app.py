from flask import Flask, render_template, request
import os

from resume_parser import extract_text
from skill_extractor import extract_skills
from matcher import analyze_skills


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    matched = missing = skills = []
   
    if request.method == "POST":
        file = request.files["resume"]
        role = request.form["role"]

        path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(role)

        text = extract_text(path)
        skills = extract_skills(text)
        matched, missing = analyze_skills(skills, role)
        
   
    return render_template(
        "index.html",
        skills=skills,
        matched=matched,
        missing=missing
    )

if __name__ == "__main__":
    app.run(debug=True)