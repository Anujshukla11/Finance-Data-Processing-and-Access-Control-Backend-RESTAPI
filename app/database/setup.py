import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'finance.db')

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create Users table
    # Role values are strictly checked to ensure clean data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Viewer', 'Analyst', 'Admin'))
        )
    ''')

    # Create Financial Records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('INCOME', 'EXPENSE')),
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT
        )
    ''')

    # Seed initial dummy data if empty so it's easy to test
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            'INSERT INTO users (username, role) VALUES (?, ?)',
            [('john_viewer', 'Viewer'), ('sarah_analyst', 'Analyst'), ('admin_user', 'Admin')]
        )

        cursor.executemany(
            'INSERT INTO financial_records (amount, type, category, date, notes) VALUES (?, ?, ?, ?, ?)',
            [
                (1500.00, 'INCOME', 'Salary', '2023-10-01', 'October Salary'),
                (120.50, 'EXPENSE', 'Groceries', '2023-10-03', 'Weekly groceries'),
                (50.00, 'EXPENSE', 'Transport', '2023-10-05', 'Gasoline'),
                (300.00, 'INCOME', 'Freelance', '2023-10-10', 'Side project payment')
            ]
        )
        print("Database seeded with sample users and records.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()
    print("Database initialized.")
