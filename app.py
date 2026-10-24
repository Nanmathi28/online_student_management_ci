import os
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def get_db_path(app):
    return app.config["DATABASE"]


def connect_db(app):
    connection = sqlite3.connect(get_db_path(app))
    connection.row_factory = sqlite3.Row
    return connection


def init_db(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    with connect_db(app) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        # Migrate the original classroom-demo schema when an existing local DB is reused.
        student_columns = {
            row[1] for row in db.execute("PRAGMA table_info(students)").fetchall()
        }
        if student_columns and "prn" not in student_columns:
            db.execute("ALTER TABLE students RENAME TO students_legacy")

        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                prn TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL
            )
        """)

        legacy_exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='students_legacy'"
        ).fetchone()
        if legacy_exists:
            legacy_rows = db.execute(
                "SELECT id, name, course FROM students_legacy ORDER BY id"
            ).fetchall()
            for row in legacy_rows:
                db.execute(
                    "INSERT OR IGNORE INTO students (name, prn, department) VALUES (?, ?, ?)",
                    (row["name"], f"LEGACY-{row['id']}", row["course"] or "Not Specified"),
                )
            db.execute("DROP TABLE students_legacy")
        existing = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing == 0:
            db.executemany(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                [
                    ("admin", generate_password_hash("admin123"), "Admin"),
                    ("staff", generate_password_hash("staff123"), "Staff"),
                ],
            )


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-secret"),
        DATABASE=str(Path(app.instance_path) / "students.db"),
    )
    if test_config:
        app.config.update(test_config)

    init_db(app)

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("students"))
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            with connect_db(app) as db:
                user = db.execute(
                    "SELECT * FROM users WHERE username = ?", (username,)
                ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                flash("Login successful.", "success")
                return redirect(url_for("students"))
            flash("Invalid username or password.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("login"))

    @app.route("/students")
    @login_required
    def students():
        with connect_db(app) as db:
            records = db.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
        return render_template("students.html", students=records)

    @app.route("/students/add", methods=["GET", "POST"])
    @login_required
    def add_student():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            prn = request.form.get("prn", "").strip().upper()
            department = request.form.get("department", "").strip()
            if not all([name, prn, department]):
                flash("Student name, PRN, and department are required.", "error")
                return render_template("student_form.html", student=None)
            try:
                with connect_db(app) as db:
                    db.execute(
                        "INSERT INTO students (name, prn, department) VALUES (?, ?, ?)",
                        (name, prn, department),
                    )
            except sqlite3.IntegrityError:
                flash("A student with that PRN already exists.", "error")
                return render_template("student_form.html", student=None)
            flash("Student added successfully.", "success")
            return redirect(url_for("students"))
        return render_template("student_form.html", student=None)

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_student(student_id):
        with connect_db(app) as db:
            student = db.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            ).fetchone()
            if student is None:
                abort(404)
            if request.method == "POST":
                name = request.form.get("name", "").strip()
                prn = request.form.get("prn", "").strip().upper()
                department = request.form.get("department", "").strip()
                if not all([name, prn, department]):
                    flash("Student name, PRN, and department are required.", "error")
                    return render_template("student_form.html", student=student)
                try:
                    db.execute(
                        "UPDATE students SET name=?, prn=?, department=? WHERE id=?",
                        (name, prn, department, student_id),
                    )
                except sqlite3.IntegrityError:
                    flash("A student with that PRN already exists.", "error")
                    return render_template("student_form.html", student=student)
                flash("Student updated successfully.", "success")
                return redirect(url_for("students"))
        return render_template("student_form.html", student=student)

    @app.route("/students/<int:student_id>/delete", methods=["POST"])
    @login_required
    def delete_student(student_id):
        with connect_db(app) as db:
            db.execute("DELETE FROM students WHERE id = ?", (student_id,))
        flash("Student deleted successfully.", "success")
        return redirect(url_for("students"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
