import unittest
import tempfile
from pathlib import Path
import app as analyzer

class StaffPulseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        analyzer.DB_PATH = Path(self.temp.name) / "test.db"
        analyzer.init_db()
        self.client = analyzer.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_dashboard_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Employee success dashboard", response.data)

    def test_employee_directory_loads(self):
        self.assertEqual(self.client.get("/employees").status_code, 200)

    def test_summary_api(self):
        response = self.client.get("/api/summary")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"employee_count", response.data)

    def test_insights_page_loads(self):
        response = self.client.get("/insights")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Metric gap analysis", response.data)

    def test_growth_plan_loads(self):
        response = self.client.get("/development_actions")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Employee growth plan", response.data)

    def test_create_and_update_development_action(self):
        with analyzer.get_db() as conn:
            employee_id = conn.execute("SELECT id FROM employees LIMIT 1").fetchone()[0]
        response = self.client.post("/development_actions", data={
            "employee_id": str(employee_id), "action_title": "Coaching session",
            "owner": "Team manager", "due_date": "2026-11-01", "notes": "Review goal gaps"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Coaching session", response.data)
        with analyzer.get_db() as conn:
            action_id = conn.execute("SELECT id FROM development_actions WHERE action_title='Coaching session'").fetchone()[0]
        response = self.client.post(f"/development_actions/{action_id}/status", data={"status":"Completed"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with analyzer.get_db() as conn:
            status = conn.execute("SELECT status FROM development_actions WHERE id=?", (action_id,)).fetchone()[0]
        self.assertEqual(status, "Completed")

    def test_csv_export(self):
        response = self.client.get("/export/employees.csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Employee ID,Full Name", response.data)

    def test_rating_bands(self):
        self.assertEqual(analyzer.rating_for(95), "Outstanding")
        self.assertEqual(analyzer.rating_for(85), "Strong")
        self.assertEqual(analyzer.rating_for(65), "Developing")
        self.assertEqual(analyzer.rating_for(45), "Needs Support")

if __name__ == "__main__":
    unittest.main()
