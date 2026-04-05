from fastapi import APIRouter, Header, HTTPException
from typing import List, Optional
import sqlite3
import os

from app.models.schemas import FinancialRecordCreate, FinancialRecordResponse
from app.services.auth import get_user_role

router = APIRouter(prefix="/records", tags=["Records"])
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'finance.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH)

@router.get("/", response_model=List[FinancialRecordResponse])
def get_records(category: Optional[str] = None, type: Optional[str] = None, user_id: str = Header(None)):
    # Any valid user can read records
    role = get_user_role(user_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM financial_records WHERE 1=1"
    params = []
    
    # Add filters if they were provided in the URL query string
    if category:
        query += " AND category = ?"
        params.append(category)
    if type:
        query += " AND type = ?"
        params.append(type)
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Manually convert the raw database tuples into a list of dictionaries
    records_list = []
    for row in rows:
        record_dict = {
            "id": row[0],
            "amount": row[1],
            "type": row[2],
            "category": row[3],
            "date": row[4],
            "notes": row[5]
        }
        records_list.append(record_dict)
        
    return records_list

@router.post("/", response_model=FinancialRecordResponse, status_code=201)
def create_record(record: FinancialRecordCreate, user_id: str = Header(None)):
    # Only Admin users can create new records
    role = get_user_role(user_id)
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can create records")
        
    # Manual Validation checks
    if record.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
        
    if record.type not in ["INCOME", "EXPENSE"]:
        raise HTTPException(status_code=400, detail="Type must be INCOME or EXPENSE")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO financial_records (amount, type, category, date, notes) VALUES (?, ?, ?, ?, ?)",
        (record.amount, record.type, record.category, record.date, record.notes)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    # Return the newly created record details
    return {
        "id": new_id,
        "amount": record.amount,
        "type": record.type,
        "category": record.category,
        "date": record.date,
        "notes": record.notes
    }

@router.put("/{record_id}", response_model=FinancialRecordResponse)
def update_record(record_id: int, record: FinancialRecordCreate, user_id: str = Header(None)):
    # Only Admin users can update records
    role = get_user_role(user_id)
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can update records")
        
    # Manual Validation
    if record.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than zero")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if record exists
    cursor.execute("SELECT id FROM financial_records WHERE id = ?", (record_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found")
        
    cursor.execute(
        "UPDATE financial_records SET amount = ?, type = ?, category = ?, date = ?, notes = ? WHERE id = ?",
        (record.amount, record.type, record.category, record.date, record.notes, record_id)
    )
    conn.commit()
    conn.close()
    
    return {
        "id": record_id,
        "amount": record.amount,
        "type": record.type,
        "category": record.category,
        "date": record.date,
        "notes": record.notes
    }

@router.delete("/{record_id}", status_code=204)
def delete_record(record_id: int, user_id: str = Header(None)):
    # Only Admins can delete
    role = get_user_role(user_id)
    if role != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can delete records")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM financial_records WHERE id = ?", (record_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Record not found")
        
    cursor.execute("DELETE FROM financial_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
