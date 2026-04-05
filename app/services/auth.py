from fastapi import HTTPException
import sqlite3
import os

# Connect to the database inside the same directory structure
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'finance.db')

def get_user_role(user_id: str):
    """
    Look up the user in the database based on their ID.
    This simulates a simple login system without the complexity of JWT tokens.
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="Please provide a user-id header")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query to find the role of the user
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    
    conn.close()

    # If row is None or empty, the user does not exist
    if not row:
        raise HTTPException(status_code=401, detail="Invalid user ID")

    # Return the role (which is the first item in the tuple)
    return row[0]
