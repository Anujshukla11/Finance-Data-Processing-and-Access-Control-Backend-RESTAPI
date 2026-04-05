"""
Comprehensive Test Suite for the Finance Dashboard API.

Tests cover:
1. Root endpoint
2. Authentication & Role-Based Access Control (RBAC)
3. Financial Records CRUD (Create, Read, Update, Delete)
4. Filtering records by category and type
5. Dashboard summary aggregation
6. Input validation (negative amounts, invalid types, missing fields)
7. Edge cases (non-existent records, missing headers)
"""

import pytest
import os
import sqlite3
from fastapi.testclient import TestClient

# Ensure we use a separate test database so we don't corrupt real data
TEST_DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'database')
TEST_DB_PATH = os.path.join(TEST_DB_DIR, 'finance.db')

from app.main import app

client = TestClient(app)

# User IDs mapped to roles (as seeded in the database):
#   1 -> Viewer
#   2 -> Analyst
#   3 -> Admin
VIEWER_HEADER  = {"user-id": "1"}
ANALYST_HEADER = {"user-id": "2"}
ADMIN_HEADER   = {"user-id": "3"}


# ==================================================================
# 1. ROOT ENDPOINT
# ==================================================================
class TestRootEndpoint:
    def test_root_redirects_to_docs(self):
        """The root endpoint should redirect users to the /docs page."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 307]
        assert "/docs" in response.headers["location"]


# ==================================================================
# 2. AUTHENTICATION & RBAC
# ==================================================================
class TestAuthentication:
    def test_missing_user_id_header_returns_401(self):
        """Requests without a user-id header should be rejected."""
        response = client.get("/records/")
        assert response.status_code == 401

    def test_invalid_user_id_returns_401(self):
        """A user-id that doesn't exist in the DB should be rejected."""
        response = client.get("/records/", headers={"user-id": "999"})
        assert response.status_code == 401

    def test_viewer_cannot_create_record(self):
        """Viewer role should be forbidden from creating records."""
        payload = {
            "amount": 100.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post("/records/", json=payload, headers=VIEWER_HEADER)
        assert response.status_code == 403

    def test_analyst_cannot_create_record(self):
        """Analyst role should be forbidden from creating records."""
        payload = {
            "amount": 100.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post("/records/", json=payload, headers=ANALYST_HEADER)
        assert response.status_code == 403

    def test_viewer_cannot_update_record(self):
        """Viewer role should be forbidden from updating records."""
        payload = {
            "amount": 200.0,
            "type": "INCOME",
            "category": "Updated",
            "date": "2024-01-01"
        }
        response = client.put("/records/1", json=payload, headers=VIEWER_HEADER)
        assert response.status_code == 403

    def test_viewer_cannot_delete_record(self):
        """Viewer role should be forbidden from deleting records."""
        response = client.delete("/records/1", headers=VIEWER_HEADER)
        assert response.status_code == 403

    def test_viewer_cannot_access_dashboard(self):
        """Viewer role should be forbidden from seeing the dashboard."""
        response = client.get("/dashboard/summary", headers=VIEWER_HEADER)
        assert response.status_code == 403


# ==================================================================
# 3. READ RECORDS (All Roles)
# ==================================================================
class TestReadRecords:
    def test_viewer_can_read_records(self):
        """Viewer should be able to GET all records."""
        response = client.get("/records/", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # seeded data should exist

    def test_analyst_can_read_records(self):
        """Analyst should be able to GET all records."""
        response = client.get("/records/", headers=ANALYST_HEADER)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_admin_can_read_records(self):
        """Admin should be able to GET all records."""
        response = client.get("/records/", headers=ADMIN_HEADER)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_records_have_correct_shape(self):
        """Each record should have id, amount, type, category, date, notes."""
        response = client.get("/records/", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        for record in data:
            assert "id" in record
            assert "amount" in record
            assert "type" in record
            assert "category" in record
            assert "date" in record
            assert "notes" in record  # notes can be None


# ==================================================================
# 4. FILTERING RECORDS
# ==================================================================
class TestFilterRecords:
    def test_filter_by_category(self):
        """Filtering by category should return only matching records."""
        response = client.get("/records/?category=Salary", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        for record in data:
            assert record["category"] == "Salary"

    def test_filter_by_type_income(self):
        """Filtering by type=INCOME should return only income records."""
        response = client.get("/records/?type=INCOME", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        for record in data:
            assert record["type"] == "INCOME"

    def test_filter_by_type_expense(self):
        """Filtering by type=EXPENSE should return only expense records."""
        response = client.get("/records/?type=EXPENSE", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        for record in data:
            assert record["type"] == "EXPENSE"

    def test_filter_by_nonexistent_category_returns_empty(self):
        """Filtering by a category that doesn't exist should return an empty list."""
        response = client.get("/records/?category=NonExistent", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert data == []


# ==================================================================
# 5. CREATE RECORDS (Admin Only)
# ==================================================================
class TestCreateRecord:
    def test_admin_can_create_record(self):
        """Admin should be able to create a new financial record."""
        payload = {
            "amount": 500.0,
            "type": "INCOME",
            "category": "Bonus",
            "date": "2024-03-15",
            "notes": "Quarterly bonus"
        }
        response = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 500.0
        assert data["type"] == "INCOME"
        assert data["category"] == "Bonus"
        assert data["date"] == "2024-03-15"
        assert data["notes"] == "Quarterly bonus"
        assert "id" in data

    def test_create_record_without_notes(self):
        """Creating a record without optional notes should work."""
        payload = {
            "amount": 75.0,
            "type": "EXPENSE",
            "category": "Utilities",
            "date": "2024-03-20"
        }
        response = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 201
        data = response.json()
        assert data["notes"] is None

    def test_create_record_negative_amount_rejected(self):
        """Negative amounts should be rejected with a 400 error."""
        payload = {
            "amount": -100.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 400

    def test_create_record_zero_amount_rejected(self):
        """Zero amounts should be rejected with a 400 error."""
        payload = {
            "amount": 0.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 400

    def test_create_record_invalid_type_rejected(self):
        """Invalid record type should be rejected with a 400 error."""
        payload = {
            "amount": 100.0,
            "type": "TRANSFER",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 400


# ==================================================================
# 6. UPDATE RECORDS (Admin Only)
# ==================================================================
class TestUpdateRecord:
    def test_admin_can_update_record(self):
        """Admin should be able to update an existing record."""
        # First create a record to update
        create_payload = {
            "amount": 100.0,
            "type": "EXPENSE",
            "category": "Food",
            "date": "2024-04-01",
            "notes": "Before update"
        }
        create_resp = client.post("/records/", json=create_payload, headers=ADMIN_HEADER)
        assert create_resp.status_code == 201
        record_id = create_resp.json()["id"]

        # Now update it
        update_payload = {
            "amount": 150.0,
            "type": "EXPENSE",
            "category": "Dining",
            "date": "2024-04-01",
            "notes": "After update"
        }
        response = client.put(f"/records/{record_id}", json=update_payload, headers=ADMIN_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 150.0
        assert data["category"] == "Dining"
        assert data["notes"] == "After update"

    def test_update_nonexistent_record_returns_404(self):
        """Updating a record that doesn't exist should return 404."""
        payload = {
            "amount": 100.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.put("/records/99999", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 404

    def test_update_record_negative_amount_rejected(self):
        """Updating with a negative amount should be rejected."""
        payload = {
            "amount": -50.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.put("/records/1", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 400

    def test_analyst_cannot_update_record(self):
        """Analyst role should be forbidden from updating records."""
        payload = {
            "amount": 100.0,
            "type": "INCOME",
            "category": "Test",
            "date": "2024-01-01"
        }
        response = client.put("/records/1", json=payload, headers=ANALYST_HEADER)
        assert response.status_code == 403


# ==================================================================
# 7. DELETE RECORDS (Admin Only)
# ==================================================================
class TestDeleteRecord:
    def test_admin_can_delete_record(self):
        """Admin should be able to delete an existing record."""
        # Create a record to delete
        payload = {
            "amount": 10.0,
            "type": "EXPENSE",
            "category": "Disposable",
            "date": "2024-05-01",
            "notes": "To be deleted"
        }
        create_resp = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert create_resp.status_code == 201
        record_id = create_resp.json()["id"]

        # Delete it
        response = client.delete(f"/records/{record_id}", headers=ADMIN_HEADER)
        assert response.status_code == 204

    def test_delete_nonexistent_record_returns_404(self):
        """Deleting a record that doesn't exist should return 404."""
        response = client.delete("/records/99999", headers=ADMIN_HEADER)
        assert response.status_code == 404

    def test_analyst_cannot_delete_record(self):
        """Analyst role should be forbidden from deleting records."""
        response = client.delete("/records/1", headers=ANALYST_HEADER)
        assert response.status_code == 403


# ==================================================================
# 8. DASHBOARD SUMMARY (Analyst & Admin)
# ==================================================================
class TestDashboard:
    def test_analyst_can_access_dashboard(self):
        """Analyst should be able to GET the dashboard summary."""
        response = client.get("/dashboard/summary", headers=ANALYST_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expense" in data
        assert "net_balance" in data
        assert "expenses_by_category" in data

    def test_admin_can_access_dashboard(self):
        """Admin should also be able to GET the dashboard summary."""
        response = client.get("/dashboard/summary", headers=ADMIN_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data

    def test_dashboard_net_balance_is_correct(self):
        """Net balance should equal total_income minus total_expense."""
        response = client.get("/dashboard/summary", headers=ANALYST_HEADER)
        assert response.status_code == 200
        data = response.json()
        expected_net = round(data["total_income"] - data["total_expense"], 2)
        assert data["net_balance"] == expected_net

    def test_dashboard_expenses_by_category_structure(self):
        """Each entry in expenses_by_category should have category and total."""
        response = client.get("/dashboard/summary", headers=ANALYST_HEADER)
        assert response.status_code == 200
        data = response.json()
        for entry in data["expenses_by_category"]:
            assert "category" in entry
            assert "total" in entry
            assert isinstance(entry["total"], (int, float))

    def test_dashboard_values_are_numeric(self):
        """All summary values should be numeric."""
        response = client.get("/dashboard/summary", headers=ANALYST_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total_income"], (int, float))
        assert isinstance(data["total_expense"], (int, float))
        assert isinstance(data["net_balance"], (int, float))


# ==================================================================
# 9. EDGE CASES & ROBUSTNESS
# ==================================================================
class TestEdgeCases:
    def test_missing_required_fields_returns_422(self):
        """Submitting a record without required fields should return 422 (Validation Error)."""
        payload = {"amount": 100.0}  # missing type, category, date
        response = client.post("/records/", json=payload, headers=ADMIN_HEADER)
        assert response.status_code == 422

    def test_empty_body_returns_422(self):
        """Submitting an empty body on POST should return 422."""
        response = client.post("/records/", json={}, headers=ADMIN_HEADER)
        assert response.status_code == 422

    def test_get_records_with_both_filters(self):
        """Filtering with both category and type at the same time should work."""
        response = client.get("/records/?category=Salary&type=INCOME", headers=VIEWER_HEADER)
        assert response.status_code == 200
        data = response.json()
        for record in data:
            assert record["category"] == "Salary"
            assert record["type"] == "INCOME"

    def test_dashboard_without_auth_returns_401(self):
        """Dashboard without user-id should return 401."""
        response = client.get("/dashboard/summary")
        assert response.status_code == 401
