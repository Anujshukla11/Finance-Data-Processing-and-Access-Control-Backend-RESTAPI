from fastapi import APIRouter, Header, HTTPException
import sqlite3
import os

from app.services.auth import get_user_role

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'finance.db')

@router.get("/summary")
def get_dashboard_summary(user_id: str = Header(None)):
    # Both Analysts and Admins can see the dashboard
    role = get_user_role(user_id)
    if role not in ["Analyst", "Admin"]:
        raise HTTPException(status_code=403, detail="Only Analysts or Admins can view the dashboard")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate Total Income
    cursor.execute("SELECT SUM(amount) FROM financial_records WHERE type = 'INCOME'")
    total_income_row = cursor.fetchone()
    total_income = total_income_row[0] if total_income_row[0] is not None else 0.0
    
    # Calculate Total Expenses
    cursor.execute("SELECT SUM(amount) FROM financial_records WHERE type = 'EXPENSE'")
    total_expense_row = cursor.fetchone()
    total_expense = total_expense_row[0] if total_expense_row[0] is not None else 0.0
    
    net_balance = total_income - total_expense
    
    # Get spending per category using GROUP BY
    cursor.execute("SELECT category, SUM(amount) FROM financial_records WHERE type = 'EXPENSE' GROUP BY category")
    category_rows = cursor.fetchall()
    
    # Convert raw database output rows to a list of dictionaries for JSON
    category_totals = []
    for row in category_rows:
        category_dict = {
            "category": row[0],
            "total": row[1]
        }
        category_totals.append(category_dict)
    
    conn.close()
    
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_balance": round(net_balance, 2),
        "expenses_by_category": category_totals
    }
