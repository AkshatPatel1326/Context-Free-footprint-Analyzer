"""
Context-Free Footprint Analyzer
Flask Backend — Minor Project, CSE Department
"""

import io
import csv
import sqlite3
from collections import Counter
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, send_file, make_response
)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "cfpa_secure_key_2025"

# Make Python's enumerate available in Jinja2 templates
app.jinja_env.filters['enumerate'] = enumerate

# ─────────────────────────────────────────────
# ADMIN CREDENTIALS
# ─────────────────────────────────────────────
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all required tables on startup."""
    conn = get_db()
    cur = conn.cursor()

    # Users table for regular login
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT    NOT NULL,
        email         TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL
    )""")

    # Student profiles table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT,
        skills           TEXT,
        projects         TEXT,
        certifications   TEXT,
        domain           TEXT,
        strength         TEXT,
        score            INTEGER,
        insight          TEXT,
        skill_gap        TEXT,
        suggested_role   TEXT,
        recommended_skills TEXT,
        user_id          INTEGER,
        submitted_by     TEXT
    )""")

    # Safe migrations for existing databases
    for col in ["suggested_role TEXT", "recommended_skills TEXT",
                "user_id INTEGER", "submitted_by TEXT",
                "submitted_at TEXT",
                "skill_count INTEGER DEFAULT 0",
                "project_count INTEGER DEFAULT 0",
                "cert_count INTEGER DEFAULT 0"]:
        try:
            cur.execute(f"ALTER TABLE students ADD COLUMN {col}")
        except Exception:
            pass

    conn.commit()
    conn.close()


init_db()


# ─────────────────────────────────────────────
# DATA CLEANING
# ─────────────────────────────────────────────

def clean_input(text: str) -> str:
    """
    Normalize comma-separated text input:
      • Convert to lowercase
      • Strip extra whitespace per item
      • Remove duplicate entries
    Example: 'Python, python , PYTHON' → 'python'
    """
    if not text or not text.strip():
        return ""
    raw = [item.strip().lower() for item in text.replace("\n", ",").split(",")]
    seen, unique = set(), []
    for item in raw:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return ", ".join(unique)


# ─────────────────────────────────────────────
# FEATURE EXTRACTION
# ─────────────────────────────────────────────

def extract_features(skills: str, projects: str, certifications: str) -> tuple:
    """
    Convert cleaned text inputs into structured numerical feature counts.
    Returns: (skill_count, project_count, cert_count)
    """
    skill_count   = len([s for s in skills.split(",") if s.strip()]) if skills else 0
    project_count = len(
        [p for p in projects.replace("\n", ",").split(",") if p.strip()]
    ) if projects else 0
    cert_count    = len([c for c in certifications.split(",") if c.strip()]) if certifications else 0
    return skill_count, project_count, cert_count


# ─────────────────────────────────────────────
# IMPROVEMENT TIPS ENGINE
# ─────────────────────────────────────────────

def generate_improvement_tips(skill_count: int, project_count: int,
                              cert_count: int, score: int) -> list:
    """
    Generate data-driven improvement tips from feature counts and score.
    Returns a list of actionable tip strings (empty if profile is strong).
    """
    tips = []
    if skill_count == 0:
        tips.append("No skills detected — list your core technical skills to enable accurate domain mapping.")
    elif skill_count < 3:
        tips.append(f"Only {skill_count} skill(s) listed. Aim for at least 5–8 relevant technologies to strengthen your profile.")
    if project_count == 0:
        tips.append("No projects found — even 1–2 hands-on projects significantly boost your score and employability.")
    elif project_count < 2:
        tips.append("Only 1 project detected. Adding diverse projects demonstrates practical experience.")
    if cert_count == 0:
        tips.append("No certifications listed — online certifications (Coursera, NPTEL, Google, AWS) effectively validate your expertise.")
    if score < 50:
        tips.append(f"Score of {score}/100 indicates an early-stage profile. Strengthen all three pillars: skills, projects, and certifications.")
    elif score < 70:
        tips.append(f"Score of {score}/100 is moderate. Focus on the identified skill gaps and add certifications to reach a Strong profile.")
    return tips


# ─────────────────────────────────────────────
# ANALYSIS ENGINE
# ─────────────────────────────────────────────

def analyze_profile(skills: str, projects: str, certifications: str):
    """
    Keyword-based analysis engine.
    Returns domain, score, strength, insight, skill_gap,
    suggested_role, and recommended_skills.
    """
    skills_l = skills.lower()
    projects_l = projects.lower()
    certs_l   = certifications.lower()

    # ── Domain Detection ──────────────────────────
    prog_kw   = ["python", "java", "c++", "c#", "javascript", "js", "react",
                 "node", "flask", "django", "api", "algorithm", "data structure",
                 "machine learning", "ml", "ai", "deep learning", "web dev",
                 "backend", "frontend", "full stack"]
    data_kw   = ["sql", "mysql", "postgresql", "excel", "r", "pandas",
                 "numpy", "tableau", "power bi", "analytics", "statistics",
                 "data analysis", "database", "bigquery"]
    net_kw    = ["networking", "cisco", "ccna", "network", "routing",
                 "switching", "firewall", "linux", "ubuntu", "server",
                 "cloud", "aws", "azure", "gcp", "devops", "docker", "kubernetes"]
    design_kw = ["ui", "ux", "figma", "adobe", "photoshop", "illustrator",
                 "design", "canva", "sketch", "wireframe"]

    combined = skills_l + " " + projects_l + " " + certs_l

    scores_domain = {
        "Programming & Development": sum(1 for k in prog_kw   if k in combined),
        "Data & Analytics":          sum(1 for k in data_kw   if k in combined),
        "Networking & Cloud":        sum(1 for k in net_kw    if k in combined),
        "UI/UX & Design":            sum(1 for k in design_kw if k in combined),
    }
    domain = max(scores_domain, key=scores_domain.get)
    if scores_domain[domain] == 0:
        domain = "General Technical Skills"

    # ── Score Calculation ──────────────────────────
    score = 0
    if skills.strip():         score += 30
    if projects.strip():       score += 25
    if certifications.strip(): score += 20

    # Bonus for keyword richness
    kw_count = sum(1 for k in prog_kw + data_kw + net_kw + design_kw if k in combined)
    score += min(kw_count * 3, 25)
    score = min(score, 100)

    # ── Strength ──────────────────────────────────
    if score >= 75:
        strength = "Strong Profile"
    elif score >= 50:
        strength = "Moderate Profile"
    else:
        strength = "Needs Improvement"

    # ── Insight ───────────────────────────────────
    insight_map = {
        "Programming & Development": (
            f"Your profile demonstrates solid competence in software development. "
            f"The combination of hands-on projects and certifications positions you "
            f"well for roles in application development and engineering."
        ),
        "Data & Analytics": (
            f"Your profile highlights strong data literacy. Expertise in databases "
            f"and analytical tools is highly valued in today's data-driven landscape."
        ),
        "Networking & Cloud": (
            f"Your skills in infrastructure and cloud technologies are relevant to "
            f"modern enterprise needs. Practical exposure to networking gives you a "
            f"solid foundation for cloud and IT operations roles."
        ),
        "UI/UX & Design": (
            f"Your design-oriented profile reflects creativity and user empathy. "
            f"Strong UI/UX skills are in high demand across product and tech companies."
        ),
        "General Technical Skills": (
            f"Your profile covers a broad technical foundation. Focusing on a "
            f"specific domain and deepening your certifications can significantly "
            f"strengthen your career positioning."
        ),
    }
    insight = insight_map.get(domain, insight_map["General Technical Skills"])

    # ── Skill Gap ─────────────────────────────────
    gap_map = {
        "Programming & Development": "Data Structures & Algorithms, System Design, Version Control (Git)",
        "Data & Analytics":          "Statistical Modeling, Big Data Tools, Machine Learning basics",
        "Networking & Cloud":        "Cloud Certifications (AWS/Azure), Kubernetes, Security Fundamentals",
        "UI/UX & Design":            "Prototyping Tools, User Research Methods, Accessibility Standards",
        "General Technical Skills":  "Domain Specialization, Project Portfolio, Industry Certifications",
    }
    skill_gap = gap_map.get(domain, gap_map["General Technical Skills"])

    # ── Suggested Role ────────────────────────────
    role_map = {
        "Programming & Development": "Software Developer / Backend Engineer",
        "Data & Analytics":          "Data Analyst / Business Intelligence Analyst",
        "Networking & Cloud":        "Cloud Engineer / Network Administrator",
        "UI/UX & Design":            "UI/UX Designer / Product Designer",
        "General Technical Skills":  "Technical Support / IT Generalist",
    }
    suggested_role = role_map.get(domain, "Technical Support")

    # ── Recommended Skills ────────────────────────
    rec_map = {
        "Programming & Development": "DSA, REST APIs, Git, Docker, System Design",
        "Data & Analytics":          "SQL, Python (Pandas), Tableau, ML Fundamentals",
        "Networking & Cloud":        "AWS/Azure, Linux, Docker, Network Security",
        "UI/UX & Design":            "Figma, Usability Testing, CSS, Adobe XD",
        "General Technical Skills":  "Choose a domain, build projects, earn certifications",
    }
    recommended_skills = rec_map.get(domain, rec_map["General Technical Skills"])

    return domain, score, strength, insight, skill_gap, suggested_role, recommended_skills


# ─────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/form")
def form():
    if not session.get("user_logged"):
        return redirect(url_for("user_login"))
    return render_template("form.html", user_name=session.get("user_name"))


@app.route("/submit", methods=["POST"])
def submit():
    if not session.get("user_logged"):
        return redirect(url_for("user_login"))

    name           = request.form.get("name", "").strip()

    # ── 1. Data Cleaning: normalize inputs before analysis ───────
    skills         = clean_input(request.form.get("skills", ""))
    certifications = clean_input(request.form.get("certifications", ""))
    projects       = request.form.get("projects", "").strip()  # free-text, preserve as-is

    if not name:
        return redirect(url_for("form"))

    # ── 2. Feature Extraction: text → numerical features ──────
    skill_count, project_count, cert_count = extract_features(skills, projects, certifications)

    # ── 3. Analysis Engine ─────────────────────────────
    domain, score, strength, insight, skill_gap, suggested_role, recommended_skills = \
        analyze_profile(skills, projects, certifications)

    # ── 4. Improvement Tips: data-driven, actionable feedback ──
    improvement_tips = generate_improvement_tips(skill_count, project_count, cert_count, score)

    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO students
        (name, skills, projects, certifications, domain, strength, score,
         insight, skill_gap, suggested_role, recommended_skills,
         user_id, submitted_by, submitted_at,
         skill_count, project_count, cert_count)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),?,?,?)
    """, (name, skills, projects, certifications, domain, strength, score,
          insight, skill_gap, suggested_role, recommended_skills,
          session.get("user_id"), session.get("user_name"),
          skill_count, project_count, cert_count))
    conn.commit()
    student_id = cur.lastrowid
    conn.close()

    return render_template("result.html",
        student_id=student_id,
        name=name, skills=skills, projects=projects,
        certifications=certifications, domain=domain,
        strength=strength, score=score, insight=insight,
        skill_gap=skill_gap, suggested_role=suggested_role,
        recommended_skills=recommended_skills,
        skill_count=skill_count, project_count=project_count,
        cert_count=cert_count,
        improvement_tips=improvement_tips,
        user_name=session.get("user_name"))


# ─────────────────────────────────────────────
# USER AUTH
# ─────────────────────────────────────────────

@app.route("/user/signup", methods=["GET", "POST"])
def user_signup():
    if session.get("user_logged"):
        return redirect(url_for("form"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        if not username or not email or not password:
            return render_template("user_signup.html", error="All fields are required.")
        if password != confirm:
            return render_template("user_signup.html", error="Passwords do not match.",
                                   username=username, email=email)
        if len(password) < 6:
            return render_template("user_signup.html",
                                   error="Password must be at least 6 characters.",
                                   username=username, email=email)

        conn = get_db()
        cur  = conn.cursor()
        if cur.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone():
            conn.close()
            return render_template("user_signup.html",
                                   error="An account with this email already exists.",
                                   username=username)
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (?,?,?)",
                    (username, email, generate_password_hash(password)))
        conn.commit()
        conn.close()
        return redirect(url_for("user_login", signup_success=1))

    return render_template("user_signup.html")


@app.route("/user/login", methods=["GET", "POST"])
def user_login():
    if session.get("user_logged"):
        return redirect(url_for("form"))

    success_msg = "Account created! Please log in." if request.args.get("signup_success") else None

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_logged"] = True
            session["user_id"]     = user["id"]
            session["user_name"]   = user["username"]
            session["user_email"]  = user["email"]
            return redirect(url_for("form"))

        return render_template("user_login.html", error="Invalid email or password.", email=email)

    return render_template("user_login.html", success=success_msg)


@app.route("/user/logout")
def user_logout():
    for key in ["user_logged", "user_id", "user_name", "user_email"]:
        session.pop(key, None)
    return redirect(url_for("home"))


# ─────────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────────

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if (request.form.get("username") == ADMIN_USER and
                request.form.get("password") == ADMIN_PASS):
            session["admin_logged"] = True
            return redirect(url_for("records"))
        return render_template("admin_login.html", error="Invalid credentials.")
    return render_template("admin_login.html")


@app.route("/records")
def records():
    if not session.get("admin_logged"):
        return redirect(url_for("admin"))

    search = request.args.get("search", "").strip()
    domain_filter = request.args.get("domain", "").strip()
    score_min  = request.args.get("score_min", "")
    score_max  = request.args.get("score_max", "")

    conn = get_db()
    cur  = conn.cursor()

    query  = "SELECT * FROM students WHERE 1=1"
    params = []

    if search:
        query  += " AND (name LIKE ? OR submitted_by LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if domain_filter:
        query  += " AND domain = ?"
        params += [domain_filter]
    if score_min.isdigit():
        query  += " AND score >= ?"
        params += [int(score_min)]
    if score_max.isdigit():
        query  += " AND score <= ?"
        params += [int(score_max)]

    query += " ORDER BY id DESC"
    rows   = cur.execute(query, params).fetchall()

    # Stats (always computed over ALL students, not filtered view)
    all_rows       = cur.execute("SELECT * FROM students").fetchall()
    total_students = len(all_rows)
    scores         = [r["score"] for r in all_rows if r["score"] is not None]
    avg_score      = round(sum(scores) / len(scores), 1) if scores else 0
    strong_profiles = sum(1 for s in scores if s >= 70)

    # ── Pattern Identification ──────────────────────────────
    # Default values (if no records yet)
    top_skill_labels  = []
    top_skill_values  = []
    most_common_skill = "N/A"
    low_scores = mid_scores = high_scores = 0

    if all_rows:
        # Most frequent skill across all profiles
        all_skills_flat = []
        for r in all_rows:
            if r["skills"]:
                all_skills_flat.extend(
                    [s.strip().title() for s in r["skills"].split(",") if s.strip()]
                )
        skill_freq        = Counter(all_skills_flat)
        top_skills        = skill_freq.most_common(6)
        top_skill_labels  = [s[0] for s in top_skills]
        top_skill_values  = [s[1] for s in top_skills]
        most_common_skill = top_skills[0][0] if top_skills else "N/A"

        # Score distribution buckets
        low_scores  = sum(1 for s in scores if s < 50)
        mid_scores  = sum(1 for s in scores if 50 <= s < 75)
        high_scores = sum(1 for s in scores if s >= 75)

    domain_counts = {}
    for r in all_rows:
        d = r["domain"] or "Unknown"
        domain_counts[d] = domain_counts.get(d, 0) + 1

    strength_counts = {}
    for r in all_rows:
        s = r["strength"] or "Unknown"
        strength_counts[s] = strength_counts.get(s, 0) + 1

    domains = cur.execute("SELECT DISTINCT domain FROM students WHERE domain IS NOT NULL").fetchall()
    domain_list = [d["domain"] for d in domains]

    conn.close()

    top_domain = max(domain_counts, key=domain_counts.get) if domain_counts else "N/A"

    return render_template("records.html",
        rows=rows,
        total_students=total_students,
        avg_score=avg_score,
        strong_profiles=strong_profiles,
        top_domain=top_domain,
        domain_labels=list(domain_counts.keys()),
        domain_values=list(domain_counts.values()),
        strength_labels=list(strength_counts.keys()),
        strength_values=list(strength_counts.values()),
        domain_list=domain_list,
        search=search,
        domain_filter=domain_filter,
        score_min=score_min,
        score_max=score_max,
        top_skill_labels=top_skill_labels,
        top_skill_values=top_skill_values,
        most_common_skill=most_common_skill,
        low_scores=low_scores,
        mid_scores=mid_scores,
        high_scores=high_scores)


@app.route("/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    if not session.get("admin_logged"):
        return redirect(url_for("admin"))
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("records"))


@app.route("/logout")
def logout():
    session.pop("admin_logged", None)
    return redirect(url_for("home"))


# ─────────────────────────────────────────────
# EXPORT ROUTES
# ─────────────────────────────────────────────

@app.route("/export/csv")
def export_csv():
    if not session.get("admin_logged"):
        return redirect(url_for("admin"))

    conn = get_db()
    rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["S.No", "Name", "Domain", "Score", "Strength",
                     "Skills", "Projects", "Certifications",
                     "Insight", "Skill Gap", "Suggested Role",
                     "Recommended Skills", "Submitted By"])
    for i, r in enumerate(rows, 1):
        writer.writerow([
            i, r["name"], r["domain"], r["score"], r["strength"],
            r["skills"], r["projects"], r["certifications"],
            r["insight"], r["skill_gap"], r["suggested_role"],
            r["recommended_skills"], r["submitted_by"]
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=student_profiles.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/download/pdf/<int:student_id>")
def download_pdf(student_id):

    if not session.get("admin_logged") and not session.get("user_logged"):
        return redirect(url_for("user_login"))

    conn = get_db()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()

    if not row:
        return "Student not found", 404

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=40,
        bottomMargin=40,
        leftMargin=40,
        rightMargin=40
    )

    styles = getSampleStyleSheet()

    # ---------- STYLES ----------
    title_style = ParagraphStyle(
        "title",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        "subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=20
    )

    section_title = ParagraphStyle(
        "section",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6
    )

    highlight_style = ParagraphStyle(
        "highlight",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )

    content = []

    # ---------- HEADER ----------
    content.append(Paragraph("Context-Free Footprint Analyzer", title_style))
    content.append(Paragraph("Student Profile Analysis Report", subtitle_style))

    # ---------- BASIC INFO TABLE ----------
    basic_data = [
        ["Student Name", row["name"]],
        ["Domain", row["domain"]],
        ["Profile Strength", row["strength"]],
        ["Score", f"{row['score']} / 100"],
    ]

    table = Table(basic_data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    content.append(table)
    content.append(Spacer(1, 15))

    # ---------- DETAILS ----------
    def section(title, value):
        content.append(Paragraph(title, section_title))
        content.append(Paragraph(value if value else "—", normal_style))
        content.append(Spacer(1, 6))

    section("Skills", row["skills"])
    section("Projects", row["projects"])
    section("Certifications", row["certifications"])

    # ---------- INSIGHT ----------
    content.append(Paragraph("Professional Insight", section_title))
    content.append(Paragraph(row["insight"], highlight_style))
    content.append(Spacer(1, 10))

    # ---------- CAREER ----------
    career_data = [
        ["Skill Gap", row["skill_gap"]],
        ["Suggested Role", row["suggested_role"]],
        ["Recommended Skills", row["recommended_skills"]],
    ]

    career_table = Table(career_data, colWidths=[150, 300])
    career_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    content.append(career_table)
    content.append(Spacer(1, 15))

    # ---------- FOOTER ----------
    content.append(Paragraph(
        f"Generated for: {row['submitted_by'] or 'User'}",
        ParagraphStyle("footer", fontSize=9, textColor=colors.grey)
    ))

    # ---------- BUILD ----------
    doc.build(content)

    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name=f"profile_{row['name'].replace(' ','_')}.pdf",
        mimetype="application/pdf"
    )


# ─────────────────────────────────────────────
# ADMIN DASHBOARD — PDF (all students)
# ─────────────────────────────────────────────

@app.route("/download/report")
def download_report():
    if not session.get("admin_logged"):
        return redirect(url_for("admin"))

    conn = get_db()
    rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    conn.close()

    buf  = io.BytesIO()
    doc  = SimpleDocTemplate(buf, pagesize=A4,
                              topMargin=40, bottomMargin=40,
                              leftMargin=50, rightMargin=50)
    styles = getSampleStyleSheet()

    t_style = ParagraphStyle("t", parent=styles["Title"],
                              fontSize=16, textColor=colors.HexColor("#1e3a8a"),
                              spaceAfter=4)
    s_style = ParagraphStyle("s", parent=styles["Normal"],
                              fontSize=9, textColor=colors.HexColor("#64748b"),
                              spaceAfter=16)

    content = [
        Paragraph("Context-Free Footprint Analyzer", t_style),
        Paragraph("Complete Student Report", s_style),
        Spacer(1, 6),
    ]

    table_data = [["S.No", "Name", "Domain", "Score", "Strength", "Submitted By"]]
    for i, r in enumerate(rows, 1):
        table_data.append([
            str(i), r["name"] or "—", r["domain"] or "—",
            str(r["score"]) if r["score"] is not None else "—",
            r["strength"] or "—", r["submitted_by"] or "—"
        ])

    t = Table(table_data, repeatRows=1,
              colWidths=[30, 90, 120, 40, 100, 90])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTSIZE",    (0, 0), (-1, 0), 9),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    content.append(t)

    doc.build(content)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name="all_students_report.pdf",
                     mimetype="application/pdf")



# ─────────────────────────────────────────────
# MY SUBMISSIONS  (student personal history)
# ─────────────────────────────────────────────

@app.route("/my-submissions")
def my_submissions():
    if not session.get("user_logged"):
        return redirect(url_for("user_login"))

    user_id = session.get("user_id")
    conn    = get_db()
    rows    = conn.execute(
        "SELECT * FROM students WHERE user_id = ? ORDER BY id DESC",
        (user_id,)
    ).fetchall()

    scores     = [r["score"] for r in rows if r["score"] is not None]
    avg_score  = round(sum(scores) / len(scores), 1) if scores else 0
    best_score = max(scores) if scores else 0
    conn.close()

    return render_template("my_submissions.html",
        rows=rows, total=len(rows),
        avg_score=avg_score, best_score=best_score,
        user_name=session.get("user_name"))


# ─────────────────────────────────────────────
# ABOUT PAGE
# ─────────────────────────────────────────────

@app.route("/about")
def about():
    return render_template("about.html")


# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)