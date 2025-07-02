import pyodbc

def get_connection():
    conn_str = (
        "Driver={SQL Server};"
        "Server=IN-6JRQ8S3;"           # ✅ verified via sqlcmd
        "Database=StudentManagementSystem;"  # ✅ check that this DB exists
        "Trusted_Connection=yes;"     # ✅ works with Windows Authentication
    )
    return pyodbc.connect(conn_str)
