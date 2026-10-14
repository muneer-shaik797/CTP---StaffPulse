# StaffPulse — Employee Performance & Growth Analyzer

StaffPulse is a workplace performance analytics prototype built with Python, Flask, SQLite, HTML, CSS, and JavaScript. It adapts the original student progress workflow to employee performance, attendance, KPI review, and manager-led development actions.

## Features
- Employee directory with employee ID, name, and department.
- Dashboard with average KPI score, attendance, review flags, employee comparison charts, and score distribution.
- KPI records for Goal Delivery, Work Quality, Teamwork, Communication, and Initiative.
- Employee profile with KPI history and attendance records.
- Performance insights that surface lower-scoring KPI areas.
- Rule-based review flags when KPI average is below 60% or attendance is below 75%.
- Employee growth plan: create a development action, assign an owner, set a due date, add notes, and track Open / In progress / Completed status.
- CSV export and JSON summary endpoint.

## Run on Windows
```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. A separate `data/employee_performance.db` database is created and seeded with demonstration employees the first time the app runs.

## Routes
- `/` dashboard
- `/employees` employee directory
- `/employees/<id>` employee KPI and attendance report
- `/insights` KPI gap analysis and review queue
- `/development_actions` development action planner
- `/export/employees.csv` CSV report
- `/api/summary` JSON summary

## Algorithm
This prototype uses arithmetic aggregation and rule-based logic. KPI attainment is calculated as total score divided by total target score. Attendance is days present divided by working days. An employee is flagged for review if the KPI average is below 60% or attendance is below 75%. This is not a trained machine-learning model, and thresholds should be aligned with company policy.

## Tests
```bash
python -m unittest -v
```

This is a demonstration prototype. Add authentication, role-based access, CSRF protection, audit logging, secure secrets, and appropriate employee-data privacy controls before real deployment. Performance indicators should support fair coaching and be reviewed in context, not used as an automated employment decision.
