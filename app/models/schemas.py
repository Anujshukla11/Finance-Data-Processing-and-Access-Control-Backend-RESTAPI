from pydantic import BaseModel
from typing import Optional
from enum import Enum

class RoleEnum(str, Enum):
    viewer = 'Viewer'
    analyst = 'Analyst'
    admin = 'Admin'

class RecordType(str, Enum):
    income = 'INCOME'
    expense = 'EXPENSE'

class FinancialRecordCreate(BaseModel):
    amount: float
    type: str # Should be 'INCOME' or 'EXPENSE'
    category: str
    date: str # Format should be YYYY-MM-DD
    notes: Optional[str] = None

class FinancialRecordResponse(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    date: str
    notes: Optional[str] = None
