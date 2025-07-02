import pyodbc

try:
    conn = pyodbc.connect(
    "Driver={SQL Server};"
    "Server=localhost;"
    "Database=StudentManagementSystem;"
    "Trusted_Connection=yes;"
    )

    print("✅ Connection successful!")
except Exception as e:
    print("❌ Connection failed:", e)
