from flask import Flask, render_template, request, redirect, session, send_file
import config
import hashlib
import io
import pandas as pd

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Used for session management

# -------------------------
# Admin Login Page
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        conn = config.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ? AND PasswordHash = ?", (username, hashed_password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = username
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# -------------------------
# Logout
# -------------------------
@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect("/login")

# -------------------------
# Home (redirects to /students)
# -------------------------
@app.route("/")
def index():
    if 'username' not in session:
        return redirect("/login")
    return redirect("/students")

# -------------------------
# View Students + Search
# -------------------------
@app.route("/students", methods=["GET", "POST"])
def view_students():
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()

    search_term = request.args.get("search", "")

    if search_term:
        query = """
            SELECT StudentID, FirstName, LastName, DOB, Email, Phone, Gender, Address
            FROM Students
            WHERE FirstName LIKE ? OR LastName LIKE ? OR Email LIKE ?
        """
        like_term = f"%{search_term}%"
        cursor.execute(query, (like_term, like_term, like_term))
    else:
        cursor.execute("SELECT * FROM Students")

    students = cursor.fetchall()
    conn.close()
    return render_template("students.html", students=students, search=search_term)

# -------------------------
# Add Student
# -------------------------
@app.route("/add_student", methods=["GET", "POST"])
def add_student():
    if 'username' not in session:
        return redirect("/login")

    if request.method == "POST":
        data = request.form
        conn = config.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Students (FirstName, LastName, DOB, Email, Phone, Gender, Address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['FirstName'], data['LastName'], data['DOB'],
            data['Email'], data['Phone'], data['Gender'], data['Address']
        ))
        conn.commit()
        conn.close()
        return redirect("/students")
    return render_template("add_student.html")

# -------------------------
# Edit Student
# -------------------------
@app.route("/edit_student/<int:id>", methods=["GET", "POST"])
def edit_student(id):
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.form
        cursor.execute("""
            UPDATE Students
            SET FirstName=?, LastName=?, DOB=?, Email=?, Phone=?, Gender=?, Address=?
            WHERE StudentID=?
        """, (
            data['FirstName'], data['LastName'], data['DOB'],
            data['Email'], data['Phone'], data['Gender'], data['Address'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect("/students")

    cursor.execute("SELECT * FROM Students WHERE StudentID=?", (id,))
    row = cursor.fetchone()
    conn.close()

    student = {
        "StudentID": row.StudentID,
        "FirstName": row.FirstName,
        "LastName": row.LastName,
        "DOB": row.DOB.strftime("%Y-%m-%d") if hasattr(row.DOB, 'strftime') else row.DOB,
        "Email": row.Email,
        "Phone": row.Phone,
        "Gender": row.Gender,
        "Address": row.Address
    }

    return render_template("edit_student.html", student=student)

# -------------------------
# Delete Student
# -------------------------
@app.route("/delete_student/<int:id>")
def delete_student(id):
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Students WHERE StudentID=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/students")

# -------------------------
# Export Students to Excel
# -------------------------
@app.route("/export")
def export_students():
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    df = pd.read_sql("SELECT * FROM Students", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Students')
    output.seek(0)

    return send_file(output, download_name="students.xlsx", as_attachment=True)

# -------------------------
# GRADES MODULE
# -------------------------

# View Grades for a student
@app.route("/grades/<int:student_id>")
def grades(student_id):
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT FirstName, LastName FROM Students WHERE StudentID=?", (student_id,))
    student = cursor.fetchone()

    cursor.execute("SELECT * FROM Grades WHERE StudentID=?", (student_id,))
    grades = cursor.fetchall()

    conn.close()
    return render_template("grades.html", student=student, grades=grades, student_id=student_id)

# Add Grade
@app.route("/add_grade/<int:student_id>", methods=["GET", "POST"])
def add_grade(student_id):
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.form
        cursor.execute("""
            INSERT INTO Grades (StudentID, Subject, Score, Grade, ExamDate)
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_id, data['Subject'], data['Score'], data['Grade'], data['ExamDate']
        ))
        conn.commit()
        conn.close()
        return redirect(f"/grades/{student_id}")

    # Fetch student name
    cursor.execute("SELECT FirstName, LastName FROM Students WHERE StudentID=?", (student_id,))
    student = cursor.fetchone()
    conn.close()
    return render_template("add_grade.html", student=student, student_id=student_id)

# Edit Grade
@app.route("/edit_grade/<int:grade_id>", methods=["GET", "POST"])
def edit_grade(grade_id):
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        data = request.form
        cursor.execute("""
            UPDATE Grades
            SET Subject=?, Score=?, Grade=?, ExamDate=?
            WHERE GradeID=?
        """, (
            data['Subject'], data['Score'], data['Grade'], data['ExamDate'], grade_id
        ))
        conn.commit()
        cursor.execute("SELECT StudentID FROM Grades WHERE GradeID=?", (grade_id,))
        student_id = cursor.fetchone().StudentID
        conn.close()
        return redirect(f"/grades/{student_id}")

    cursor.execute("SELECT * FROM Grades WHERE GradeID=?", (grade_id,))
    grade = cursor.fetchone()
    conn.close()
    return render_template("edit_grade.html", grade=grade)

# Delete Grade
@app.route("/delete_grade/<int:grade_id>")
def delete_grade(grade_id):
    if 'username' not in session:
        return redirect("/login")

    conn = config.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT StudentID FROM Grades WHERE GradeID=?", (grade_id,))
    student_id = cursor.fetchone().StudentID
    cursor.execute("DELETE FROM Grades WHERE GradeID=?", (grade_id,))
    conn.commit()
    conn.close()
    return redirect(f"/grades/{student_id}")

# -------------------------
# Start the server
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

