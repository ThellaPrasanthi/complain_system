from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

# =========================
# CONFIG
# =========================
SECRET_KEY = "complain-secret-key"
DB_NAME = "complaints.db"

# =========================
# DATABASE HELPERS
# =========================
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            email TEXT,
            phone TEXT,
            category TEXT,
            title TEXT,
            description TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# AUTH DECORATOR
# =========================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token missing"}), 401

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = payload
        except:
            return jsonify({"message": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated

# =========================
# HEALTH CHECK
# =========================
@app.route("/")
def home():
    return {"status": "Backend running with SQLite + Auth"}

# =========================
# LOGIN
# =========================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    # DEMO USERS (hardcoded)
    users = {
        "admin": {"password": "admin123", "role": "admin"},
        "user": {"password": "user123", "role": "user"}
    }

    if username not in users or users[username]["password"] != password:
        return jsonify({"message": "Invalid credentials"}), 401

    payload = {
        "username": username,
        "role": users[username]["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=6)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return jsonify({
        "token": token,
        "role": users[username]["role"]
    })

# =========================
# CREATE COMPLAINT
# =========================
@app.route("/api/complaints", methods=["POST"])
@token_required
def create_complaint():
    data = request.json
    user = request.user

    conn = get_db()
    conn.execute("""
        INSERT INTO complaints
        (username, name, email, phone, category, title, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["username"],
        data["name"],
        data["email"],
        data["phone"],
        data["category"],
        data["title"],
        data["description"],
        "Pending"
    ))
    conn.commit()
    conn.close()

    return {"message": "Complaint added"}, 201

# =========================
# READ COMPLAINTS
# =========================
@app.route("/api/complaints", methods=["GET"])
@token_required
def get_complaints():
    user = request.user
    conn = get_db()

    if user["role"] == "admin":
        rows = conn.execute("SELECT * FROM complaints").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM complaints WHERE username = ?",
            (user["username"],)
        ).fetchall()

    conn.close()

    return jsonify([
        {
            "id": f"CMP{row['id']:03d}",
            "username": row["username"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "category": row["category"],
            "title": row["title"],
            "description": row["description"],
            "status": row["status"]
        }
        for row in rows
    ])

# =========================
# UPDATE STATUS (ADMIN ONLY)
# =========================
@app.route("/api/complaints/<cid>", methods=["PUT"])
@token_required
def update_status(cid):
    user = request.user
    if user["role"] != "admin":
        return {"message": "Access denied"}, 403

    real_id = int(cid.replace("CMP", ""))
    status = request.json["status"]

    conn = get_db()
    conn.execute(
        "UPDATE complaints SET status=? WHERE id=?",
        (status, real_id)
    )
    conn.commit()
    conn.close()

    return {"message": "Status updated"}

# =========================
# DELETE COMPLAINT (ADMIN ONLY)
# =========================
@app.route("/api/complaints/<cid>", methods=["DELETE"])
@token_required
def delete_complaint(cid):
    user = request.user
    if user["role"] != "admin":
        return {"message": "Access denied"}, 403

    real_id = int(cid.replace("CMP", ""))

    conn = get_db()
    conn.execute("DELETE FROM complaints WHERE id=?", (real_id,))
    conn.commit()
    conn.close()

    return {"message": "Deleted"}

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
