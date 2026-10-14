from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "employee_performance.db"
app = Flask(__name__)
app.secret_key = "staffpulse-local-demo-change-before-deployment"

METRICS = ["Goal Delivery", "Work Quality", "Teamwork", "Communication", "Initiative"]

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                score REAL NOT NULL CHECK(score >= 0),
                target_score REAL NOT NULL CHECK(target_score > 0),
                review_period TEXT NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                days_present INTEGER NOT NULL CHECK(days_present >= 0),
                working_days INTEGER NOT NULL CHECK(working_days > 0),
                review_period TEXT NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS development_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                action_title TEXT NOT NULL,
                owner TEXT NOT NULL,
                due_date TEXT NOT NULL,
                notes TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Open' CHECK(status IN ('Open','In progress','Completed')),
                created_at TEXT NOT NULL,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
        """)
        conn.commit()
        # Seed demonstration records only when the database is empty.
        count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        if count == 0:
            demo = [
                ("EMP-1001", "Aarav Kumar", "Engineering"),
                ("EMP-1002", "Meera Reddy", "Human Resources"),
                ("EMP-1003", "Rohan Das", "Customer Support"),
                ("EMP-1004", "Ananya Rao", "Sales & Marketing"),
            ]
            for row in demo:
                conn.execute("INSERT INTO employees(employee_code,full_name,department,created_at) VALUES(?,?,?,?)",
                             (*row, datetime.now().isoformat(timespec="seconds")))
            employee_ids = {r["employee_code"]: r["id"] for r in conn.execute("SELECT id,employee_code FROM employees")}
            sample_performance_records = [
                ("EMP-1001","Goal Delivery",86,100,"Q3 2026"),("EMP-1001","Work Quality",91,100,"Q3 2026"),
                ("EMP-1001","Teamwork",78,100,"Q3 2026"),("EMP-1001","Communication",82,100,"Q3 2026"),
                ("EMP-1001","Initiative",84,100,"Q3 2026"),
                ("EMP-1002","Goal Delivery",75,100,"Q3 2026"),("EMP-1002","Work Quality",82,100,"Q3 2026"),
                ("EMP-1002","Teamwork",88,100,"Q3 2026"),("EMP-1002","Communication",79,100,"Q3 2026"),
                ("EMP-1002","Initiative",85,100,"Q3 2026"),
                ("EMP-1003","Goal Delivery",52,100,"Q3 2026"),("EMP-1003","Work Quality",61,100,"Q3 2026"),
                ("EMP-1003","Teamwork",58,100,"Q3 2026"),("EMP-1003","Communication",63,100,"Q3 2026"),
                ("EMP-1003","Initiative",67,100,"Q3 2026"),
                ("EMP-1004","Goal Delivery",91,100,"Q3 2026"),("EMP-1004","Work Quality",88,100,"Q3 2026"),
                ("EMP-1004","Teamwork",94,100,"Q3 2026"),("EMP-1004","Communication",90,100,"Q3 2026"),
                ("EMP-1004","Initiative",89,100,"Q3 2026"),
            ]
            for code, metric_name, score, maximum, review_period in sample_performance_records:
                conn.execute("INSERT INTO performance_records(employee_id,metric_name,score,target_score,review_period) VALUES(?,?,?,?,?)",
                             (employee_ids[code], metric_name, score, maximum, review_period))
            sample_attendance = [
                ("EMP-1001",47,50,"Q3 2026"),("EMP-1002",44,50,"Q3 2026"),
                ("EMP-1003",36,50,"Q3 2026"),("EMP-1004",48,50,"Q3 2026")
            ]
            for code, attended, conducted, review_period in sample_attendance:
                conn.execute("INSERT INTO attendance(employee_id,days_present,working_days,review_period) VALUES(?,?,?,?)",
                             (employee_ids[code], attended, conducted, review_period))
            conn.commit()

def rating_for(percent):
    if percent >= 90: return "Outstanding"
    if percent >= 80: return "Strong"
    if percent >= 70: return "Effective"
    if percent >= 60: return "Developing"
    return "Needs Support"

def dashboard_data():
    with get_db() as conn:
        employees = conn.execute("SELECT * FROM employees ORDER BY full_name").fetchall()
        performance_records = conn.execute("""
            SELECT m.*, s.employee_code, s.full_name
            FROM performance_records m JOIN employees s ON s.id=m.employee_id
        """).fetchall()
        attendance = conn.execute("""
            SELECT a.*, s.employee_code, s.full_name
            FROM attendance a JOIN employees s ON s.id=a.employee_id
        """).fetchall()
    employee_summaries = []
    for s in employees:
        sm = [m for m in performance_records if m["employee_id"] == s["id"]]
        sa = [a for a in attendance if a["employee_id"] == s["id"]]
        pct = (sum(m["score"] for m in sm) / sum(m["target_score"] for m in sm) * 100) if sm else 0
        att = (sum(a["days_present"] for a in sa) / sum(a["working_days"] for a in sa) * 100) if sa else 0
        employee_summaries.append({
            "id": s["id"], "employee_code": s["employee_code"], "full_name": s["full_name"],
            "department": s["department"], "average": round(pct, 1), "rating": rating_for(pct),
            "attendance": round(att, 1), "status": "Review" if pct < 60 or att < 75 else "On track",
            "recommendation": "Manager check-in and performance plan" if pct < 60 and att < 75 else ("Create a performance improvement plan" if pct < 60 else ("Discuss attendance barriers" if att < 75 else "Maintain current performance goals"))
        })
    return employees, employee_summaries

@app.route("/")
def index():
    employees, summaries = dashboard_data()
    avg = round(sum(s["average"] for s in summaries)/len(summaries),1) if summaries else 0
    att = round(sum(s["attendance"] for s in summaries)/len(summaries),1) if summaries else 0
    at_risk = sum(s["status"] == "Review" for s in summaries)
    with get_db() as conn:
        total_performance_records = conn.execute("SELECT COUNT(*) FROM performance_records").fetchone()[0]
        open_actions = conn.execute("SELECT COUNT(*) FROM development_actions WHERE status != 'Completed'").fetchone()[0]
        latest_actions = conn.execute("""SELECT i.*, s.full_name, s.employee_code FROM development_actions i
            JOIN employees s ON s.id=i.employee_id ORDER BY CASE i.status WHEN 'Open' THEN 0 WHEN 'In progress' THEN 1 ELSE 2 END, i.due_date LIMIT 4""").fetchall()
    return render_template("index.html", summaries=summaries, total=len(employees), avg=avg, att=att, at_risk=at_risk, total_performance_records=total_performance_records, open_actions=open_actions, latest_actions=latest_actions)

@app.route("/employees")
def employees_page():
    employees, summaries = dashboard_data()
    return render_template("employees.html", summaries=summaries)

@app.route("/employees/add", methods=["POST"])
def add_employee():
    code = request.form.get("employee_code","").strip()
    full_name = request.form.get("full_name","").strip()
    department = request.form.get("department","").strip()
    if not code or not full_name or not department:
        flash("Please complete all employee fields.", "error")
        return redirect(url_for("employees_page"))
    try:
        with get_db() as conn:
            conn.execute("INSERT INTO employees(employee_code,full_name,department,created_at) VALUES(?,?,?,?)",
                         (code, full_name, department, datetime.now().isoformat(timespec="seconds")))
            conn.commit()
        flash("Employee added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("Employee ID already exists. Use a unique ID.", "error")
    return redirect(url_for("employees_page"))

@app.route("/employees/<int:employee_id>")
def employee_detail(employee_id):
    with get_db() as conn:
        employee = conn.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
        performance_records = conn.execute("SELECT * FROM performance_records WHERE employee_id=? ORDER BY review_period,metric_name", (employee_id,)).fetchall()
        attendance = conn.execute("SELECT * FROM attendance WHERE employee_id=? ORDER BY review_period", (employee_id,)).fetchall()
    if not employee:
        flash("Employee record not found.", "error")
        return redirect(url_for("employees_page"))
    total_performance_records = sum(m["score"] for m in performance_records)
    target_score = sum(m["target_score"] for m in performance_records)
    average = round(total_performance_records/target_score*100,1) if target_score else 0
    att_total = sum(a["days_present"] for a in attendance)
    att_max = sum(a["working_days"] for a in attendance)
    att_pct = round(att_total/att_max*100,1) if att_max else 0
    return render_template("employee_detail.html", employee=employee, performance_records=performance_records, attendance=attendance,
                           average=average, rating=rating_for(average), att_pct=att_pct)

@app.route("/performance_records/add", methods=["POST"])
def add_performance_record():
    try:
        employee_id=int(request.form["employee_id"]); metric_name=request.form["metric_name"].strip()
        score_value=float(request.form["score"]); maximum=float(request.form["target_score"])
        review_period=request.form["review_period"].strip()
        if score_value < 0 or maximum <= 0 or score_value > maximum or not metric_name or not review_period:
            raise ValueError
        with get_db() as conn:
            conn.execute("INSERT INTO performance_records(employee_id,metric_name,score,target_score,review_period) VALUES(?,?,?,?,?)",
                         (employee_id,metric_name,score_value,maximum,review_period)); conn.commit()
        flash("Performance metric added successfully.", "success")
    except (ValueError, KeyError, sqlite3.IntegrityError):
        flash("Invalid performance entry. Check the employee, metric, review period, and score range.", "error")
    return redirect(request.referrer or url_for("employees_page"))

@app.route("/attendance/add", methods=["POST"])
def add_attendance():
    try:
        employee_id=int(request.form["employee_id"]); attended=int(request.form["days_present"])
        conducted=int(request.form["working_days"]); review_period=request.form["review_period"].strip()
        if attended < 0 or conducted <= 0 or attended > conducted or not review_period:
            raise ValueError
        with get_db() as conn:
            conn.execute("INSERT INTO attendance(employee_id,days_present,working_days,review_period) VALUES(?,?,?,?)",
                         (employee_id,attended,conducted,review_period)); conn.commit()
        flash("Attendance record added.", "success")
    except (ValueError, KeyError, sqlite3.IntegrityError):
        flash("Invalid attendance entry. Days present cannot exceed working days.", "error")
    return redirect(request.referrer or url_for("employees_page"))


@app.route("/insights")
def insights_page():
    employees, summaries = dashboard_data()
    with get_db() as conn:
        metric_name_rows = conn.execute("""
            SELECT metric_name, ROUND(SUM(score) * 100.0 / SUM(target_score), 1) AS average,
                   COUNT(DISTINCT employee_id) AS employee_count
            FROM performance_records GROUP BY metric_name ORDER BY average ASC, metric_name
        """).fetchall()
        weakest = metric_name_rows[0] if metric_name_rows else None
    review_employees = [s for s in summaries if s["status"] == "Review"]
    return render_template("insights.html", metrics=metric_name_rows, weakest=weakest,
                           review_employees=review_employees, summaries=summaries)


@app.route("/development_actions", methods=["GET", "POST"])
def development_actions_page():
    if request.method == "POST":
        try:
            employee_id = int(request.form["employee_id"])
            title = request.form.get("action_title", "").strip()
            owner = request.form.get("owner", "").strip()
            due_date = request.form.get("due_date", "").strip()
            notes = request.form.get("notes", "").strip()
            if not title or not owner or not due_date:
                raise ValueError
            with get_db() as conn:
                exists = conn.execute("SELECT id FROM employees WHERE id=?", (employee_id,)).fetchone()
                if not exists:
                    raise ValueError
                conn.execute("INSERT INTO development_actions(employee_id,action_title,owner,due_date,notes,status,created_at) VALUES(?,?,?,?,?,'Open',?)",
                             (employee_id, title, owner, due_date, notes, datetime.now().isoformat(timespec="seconds")))
                conn.commit()
            flash("Support action added to the development action planner.", "success")
        except (ValueError, KeyError, sqlite3.IntegrityError):
            flash("Please complete the action details and choose a valid employee.", "error")
        return redirect(url_for("development_actions_page"))
    with get_db() as conn:
        employees = conn.execute("SELECT id, employee_code, full_name FROM employees ORDER BY full_name").fetchall()
        actions = conn.execute("""SELECT i.*, s.full_name, s.employee_code FROM development_actions i
            JOIN employees s ON s.id=i.employee_id ORDER BY CASE i.status WHEN 'Open' THEN 0 WHEN 'In progress' THEN 1 ELSE 2 END, i.due_date, i.id DESC""").fetchall()
    return render_template("development_actions.html", employees=employees, actions=actions)

@app.route("/development_actions/<int:action_id>/status", methods=["POST"])
def update_development_action_status(action_id):
    status = request.form.get("status", "")
    if status not in {"Open", "In progress", "Completed"}:
        flash("Choose a valid action status.", "error")
    else:
        with get_db() as conn:
            cur = conn.execute("UPDATE development_actions SET status=? WHERE id=?", (status, action_id))
            conn.commit()
        flash("Action status updated." if cur.rowcount else "Action not found.", "success" if cur.rowcount else "error")
    return redirect(url_for("development_actions_page"))

@app.route("/export/employees.csv")
def export_employees_csv():
    _, summaries = dashboard_data()
    lines = ["Employee ID,Full Name,Department,Average Percentage,Rating,Attendance Percentage,Status,Recommended Action"]
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee ID", "Full Name", "Department", "Average Percentage", "Rating", "Attendance Percentage", "Status", "Recommended Action"])
    for s in summaries:
        writer.writerow([s["employee_code"], s["full_name"], s["department"], s["average"], s["rating"], s["attendance"], s["status"], s["recommendation"]])
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=staffpulse-employee-report.csv"})

@app.route("/api/summary")
def api_summary():
    employees, summaries = dashboard_data()
    return jsonify({"employee_count": len(employees), "employees": summaries})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
