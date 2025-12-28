from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import jwt, datetime
from functools import wraps

app = Flask(__name__)
CORS(app)

DB_NAME = "complaints.db"
SECRET_KEY = "secret123"   # you can change later

# ---------- DB helper ----------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Create tables ----------
def init_db():
    conn = get_db()

    # complaints table (YOUR ORIGINAL)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            category TEXT,
            title TEXT,
            description TEXT,
            status TEXT
        )
    """)

    # users table (NEW for auth)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)

    # default users
    conn.execute("""
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES 
        ('admin', 'admin123', 'admin'),
        ('user', 'user123', 'user')
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return {"status": "Backend running with SQLite + Auth"}

# ---------- AUTH HELPERS ----------
def token_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization")
            if not token:
                return {"message": "Token missing"}, 401
            try:
                data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                if role and data["role"] != role:
                    return {"message": "Access denied"}, 403
            except:
                return {"message": "Invalid token"}, 401
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ---------- LOGIN ----------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (data["username"], data["password"])
    ).fetchone()

    conn.close()

    if not user:
        return {"message": "Invalid credentials"}, 401

    token = jwt.encode({
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }, SECRET_KEY, algorithm="HS256")

    return {
        "token": token,
        "role": user["role"]
    }

# ---------- CREATE (USER) ----------
@app.route("/api/complaints", methods=["POST"])
@token_required()
def create_complaint():
    data = request.json
    conn = get_db()

    conn.execute("""
        INSERT INTO complaints
        (name, email, phone, category, title, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
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

# ---------- READ (USER + ADMIN) ----------
@app.route("/api/complaints", methods=["GET"])
@token_required()
def get_complaints():
    conn = get_db()
    rows = conn.execute("SELECT * FROM complaints").fetchall()
    conn.close()

    return jsonify([
        {
            "id": f"CMP{row['id']:03d}",
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

# ---------- UPDATE (ADMIN ONLY) ----------
@app.route("/api/complaints/<cid>", methods=["PUT"])
@token_required("admin")
def update_status(cid):
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

# ---------- DELETE (ADMIN ONLY) ----------
@app.route("/api/complaints/<cid>", methods=["DELETE"])
@token_required("admin")
def delete_complaint(cid):
    real_id = int(cid.replace("CMP", ""))

    conn = get_db()
    conn.execute("DELETE FROM complaints WHERE id=?", (real_id,))
    conn.commit()
    conn.close()

    return {"message": "Deleted"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
