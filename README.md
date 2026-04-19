# Footprint Analyzer — Profile Evaluation System

**Footprint Analyzer** is a comprehensive, full-stack web application developed as a **Minor Project** for the Computer Science & Engineering (CSE) Department. The system evaluates student technical profiles (skills, projects, and certifications) to provide quantified scoring, domain classification, and data-driven career insights.

## 🚀 Key Features

### For Students (Users)
- **Profile Analysis:** Submit technical skills, projects, and certifications for instant evaluation.
- **Quantified Scoring:** Receive a score out of 100 based on profile richness and keyword strength.
- **Domain Classification:** Automatically identifies the primary domain (e.g., Programming, Data Analytics, UI/UX, or Networking).
- **Career Roadmap:** Identifies skill gaps and suggests specific roles and learning recommendations.
- **Professional Exports:** Download a formatted **PDF Analysis Report** for your portfolio.
- **Submission History:** Track progress over time via the "My History" dashboard.

### For Administrators
- **Centralized Dashboard:** Overview of all student submissions with real-time analytics.
- **Data Visualization:** Interactive charts (via Chart.js) showing domain distribution and profile strength.
- **Advanced Filtering:** Search and filter student records by name, domain, or score range.
- **Data Management:** View full details, delete records, or export the entire database as **CSV** or **Summary PDF**.
- **Secret Access:** A hidden "Easter Egg" on the landing page allows admins to access the login panel discreetly.

## 🛠️ Tech Stack

- **Backend:** Python / Flask
- **Database:** SQLite (Relational)
- **Frontend:** HTML5, CSS3 (Vanilla), JavaScript (ES6)
- **Data Visualization:** Chart.js
- **PDF Generation:** ReportLab
- **Authentication:** Werkzeug (Password Hashing) & Flask Sessions

## 📊 Data Analytics Pipeline

The project implements a custom context-free analysis engine:
1.  **Data Cleaning:** Normalizes input, removes duplicates, and strips whitespace.
2.  **Feature Extraction:** Converts raw text into numerical feature counts (skills, projects, certs).
3.  **Keyword Matching:** Uses a weighted keyword system to detect technical domains and calculate scores.
4.  **Pattern Identification:** Generates dynamic improvement tips based on profile weaknesses.

## ⚙️ Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd Footprint-Analyzer
    ```

2.  **Create a Virtual Environment (Optional but Recommended):**
    ```bash
    python -m venv venv
    venv\Scripts\activate  # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application:**
    ```bash
    python app.py
    ```
    The app will be available at `http://127.0.0.1:5000`.

## 📂 Project Structure

```text
├── app.py              # Main Flask Application & Analysis Engine
├── database.db         # SQLite Database (Auto-generated)
├── requirements.txt    # Project Dependencies
├── static/
│   ├── style.css       # Custom Design System & Styles
├── templates/
│   ├── index.html      # Landing Page (with Easter Egg)
│   ├── form.html       # Profile Submission Form
│   ├── result.html     # Individual Analysis Results
│   ├── records.html    # Admin Dashboard & Analytics
│   ├── my_submissions.html # User History
│   └── ... (Auth & Error pages)
└── ...
```

## 🔐 Admin Access
- **Admin Credentials:** `admin` / `admin123` (Configurable in `app.py`)
- **Easter Egg:** On the home page, click the **"Footprint Analyzer"** brand name in the navbar **5 times** to quickly jump to the Admin Login.

---
**Developed as a Minor Project — CSE Department**
