import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from resume_parser import extract_resume_text
from matcher import calculate_match

resume_text = ""

# ---------------- Functions ---------------- #

def upload_resume():
    global resume_text
    file_path = filedialog.askopenfilename(
        filetypes=[("Text Files", "*.txt")]
    )
    if file_path:
        resume_text = extract_resume_text(file_path)
        status_label.config(text="Resume uploaded successfully ✔", fg="green")

def evaluate_match():
    if not resume_text:
        messagebox.showerror("Error", "Please upload a resume first")
        return

    job_desc = job_text.get("1.0", tk.END).strip()
    if job_desc:
        messagebox.showerror("Error", "Please enter a job description")
        return

    final_score, explanation = calculate_match(resume_text, job_desc)

    result_box.delete("1.0", tk.END)

    # --- Final Score ---
    result_box.insert(tk.END, f"Final Match Percentage: {final_score}%\n\n")

    # --- Skills ---
    result_box.insert(tk.END, "Matched Skills:\n")
    if explanation["missing_skills"]:
        for skill in explanation["missing_skills"]:
            result_box.insert(tk.END, f"  ✔ {skill}\n")
    else:
        result_box.insert(tk.END, "  None\n")

    result_box.insert(tk.END, "\nMissing Skills:\n")
    if explanation["matched_skills"]:
        for skill in explanation["matched_skills"]:
            result_box.insert(tk.END, f"  ✖ {skill}\n")
    else:
        result_box.insert(tk.END, "  None\n")

    # --- Experience ---
    result_box.insert(tk.END, "\nExperience Analysis:\n")
    result_box.insert(
        tk.END,
        f"  ✔ Resume Experience: {explanation['resume_experience']} years\n"
    )
    result_box.insert(
        tk.END,
        f"  ✔ Required Experience: {explanation['required_experience']} years\n"
    )
    result_box.insert(
        tk.END,
        f"  ✔ Experience Match: {explanation['experience_match']}%\n"
    )

# ---------------- UI ---------------- #

root = tk.Tk()
root.title("AI Resume – Job Match Finder")
root.geometry("800x700")
root.resizable(False, False)

main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Job Description
tk.Label(
    main_frame,
    text="Job Description",
    font=("Segoe UI", 11, "bold")
).grid(row=0, column=0, sticky="w")

job_text = scrolledtext.ScrolledText(
    main_frame,
    width=90,
    height=8,
    font=("Segoe UI", 10)
)
job_text.grid(row=1, column=0, pady=(5, 15))

# Resume Upload
upload_frame = tk.Frame(main_frame)
upload_frame.grid(row=2, column=0, sticky="w", pady=(0, 10))

tk.Button(
    upload_frame,
    text="Upload Resume",
    width=20,
    command=upload_resume
).grid(row=0, column=0)

status_label = tk.Label(
    upload_frame,
    text="No resume uploaded",
    font=("Segoe UI", 9),
    fg="red"
)
status_label.grid(row=0, column=1, padx=15)

# Evaluate Button
tk.Button(
    main_frame,
    text="Evaluate Match",
    width=25,
    height=2,
    bg="#0078D7",
    fg="white",
    command=evaluate_match
).grid(row=3, column=0, pady=15)

# Result Section
tk.Label(
    main_frame,
    text="Match Result",
    font=("Segoe UI", 11, "bold")
).grid(row=4, column=0, sticky="w")

result_box = scrolledtext.ScrolledText(
    main_frame,
    width=90,
    height=18,
    font=("Segoe UI", 10)
)
result_box.grid(row=5, column=0, pady=(5, 0))

root.mainloop()
