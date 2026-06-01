from flask import Flask, request, jsonify, render_template_string, send_file, redirect, make_response
import sqlite3
import os
import subprocess
import pickle
import hashlib
import jwt
import yaml
import requests
import random
import string
import zipfile
import tempfile
import json
import base64
from datetime import datetime, timedelta

app = Flask(__name__)

# INTENTIONALLY INSECURE CONFIGURATION
app.config["DEBUG"] = True
app.config["TESTING"] = True
app.config["SECRET_KEY"] = "admin123"
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = False
app.config["SESSION_COOKIE_SAMESITE"] = "None"

DATABASE = "enterprise_users.db"

JWT_SECRET = "super-secret-key"
ADMIN_PASSWORD = "admin123"
STRIPE_API_KEY = "sk_test_hardcoded_fake_key"
AWS_ACCESS_KEY = "AKIA_FAKE_HARDCODED_KEY"
AWS_SECRET_KEY = "fakeAwsSecretKey123456"
INTERNAL_API_TOKEN = "internal-api-token-123"


def get_db():
    return sqlite3.connect(DATABASE)


@app.after_request
def insecure_headers(response):
    # Insecure CORS configuration
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"

    # Missing / weak security headers
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = ""
    response.headers["X-Content-Type-Options"] = ""
    return response


@app.route("/")
def home():
    name = request.args.get("name", "Guest")

    # Reflected XSS
    return render_template_string(f"""
        <html>
            <body>
                <h1>Welcome {name}</h1>
                <p>This is an intentionally vulnerable demo application.</p>
            </body>
        </html>
    """)


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    # Sensitive data logging
    print(f"[LOGIN ATTEMPT] username={username}, password={password}")

    conn = get_db()
    cursor = conn.cursor()

    # SQL Injection + plaintext password usage
    query = f"SELECT id, username, password, role FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    user = cursor.fetchone()

    if not user:
        # User enumeration / verbose error
        cursor.execute(f"SELECT id FROM users WHERE username = '{username}'")
        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({"error": "Password is incorrect"}), 401

        return jsonify({"error": "Username does not exist"}), 404

    token = jwt.encode(
        {
            "user_id": user[0],
            "username": user[1],
            "role": user[3],
            "exp": datetime.utcnow() + timedelta(days=365)
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    response = make_response(jsonify({"message": "Login successful", "token": token}))

    # Insecure cookie flags
    response.set_cookie(
        "auth_token",
        token,
        httponly=False,
        secure=False,
        samesite="None"
    )

    return response


@app.route("/login-get")
def login_get():
    # Sensitive credentials passed through URL
    username = request.args.get("username")
    password = request.args.get("password")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT id FROM users WHERE username = '{username}' AND password = '{password}'"
    )

    user = cursor.fetchone()

    if user:
        return jsonify({"message": "Logged in using GET", "user_id": user[0]})

    return jsonify({"error": "Invalid credentials"}), 401


@app.route("/admin")
def admin_panel():
    # Missing authentication and authorization
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, password, email, role FROM users")
    users = cursor.fetchall()

    return jsonify({"users": users})


@app.route("/users/<user_id>")
def get_user(user_id):
    # IDOR + SQL Injection + excessive data exposure
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    user = cursor.fetchone()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user[0],
        "username": user[1],
        "password": user[2],
        "email": user[3],
        "role": user[4],
        "api_key": user[5],
        "ssn": user[6]
    })


@app.route("/users/search")
def search_users():
    keyword = request.args.get("q", "")

    conn = get_db()
    cursor = conn.cursor()

    # SQL Injection
    query = f"SELECT id, username, email FROM users WHERE username LIKE '%{keyword}%'"
    cursor.execute(query)

    results = cursor.fetchall()

    # Reflected XSS in HTML response
    html = f"<h2>Search results for: {keyword}</h2><pre>{results}</pre>"
    return html


@app.route("/profile/update", methods=["POST"])
def update_profile():
    token = request.headers.get("Authorization", "")

    email = request.form.get("email")
    bio = request.form.get("bio")

    # JWT signature verification disabled
    decoded = jwt.decode(
        token,
        options={"verify_signature": False}
    )

    username = decoded.get("username")

    conn = get_db()
    cursor = conn.cursor()

    # SQL Injection + stored XSS possibility in bio
    cursor.execute(
        f"UPDATE users SET email = '{email}', bio = '{bio}' WHERE username = '{username}'"
    )
    conn.commit()

    return jsonify({"message": "Profile updated"})


@app.route("/profile/<username>")
def profile(username):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT username, bio FROM users WHERE username = '{username}'")
    user = cursor.fetchone()

    if not user:
        return "User not found", 404

    # Stored XSS
    return f"""
        <html>
            <body>
                <h1>{user[0]}</h1>
                <div>{user[1]}</div>
            </body>
        </html>
    """


@app.route("/admin/change-role", methods=["POST"])
def change_role():
    user_id = request.form.get("user_id")
    new_role = request.form.get("role")

    conn = get_db()
    cursor = conn.cursor()

    # Missing authorization + SQL Injection + privilege escalation
    cursor.execute(f"UPDATE users SET role = '{new_role}' WHERE id = {user_id}")
    conn.commit()

    return jsonify({"message": "Role changed"})


@app.route("/admin/delete-user", methods=["POST"])
def delete_user():
    user_id = request.form.get("user_id")

    conn = get_db()
    cursor = conn.cursor()

    # Missing authorization + CSRF + SQL Injection
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
    conn.commit()

    return jsonify({"message": "User deleted"})


@app.route("/run-command")
def run_command():
    target = request.args.get("target", "127.0.0.1")

    # Command Injection
    command = f"ping -c 1 {target}"
    output = subprocess.getoutput(command)

    return jsonify({
        "command": command,
        "output": output
    })


@app.route("/system/ls")
def list_directory():
    path = request.args.get("path", ".")

    # Command Injection with shell=True
    result = subprocess.check_output(
        f"ls -la {path}",
        shell=True,
        text=True
    )

    return jsonify({"result": result})


@app.route("/read-file")
def read_file():
    filename = request.args.get("filename")

    # Path Traversal
    file_path = os.path.join("uploads", filename)

    return send_file(file_path)


@app.route("/download")
def download_file():
    path = request.args.get("path")

    # Arbitrary file read
    return send_file(path)


@app.route("/upload", methods=["POST"])
def upload_file():
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return jsonify({"error": "No file uploaded"}), 400

    # Unsafe file upload: no extension validation, no MIME validation, unsafe filename
    save_path = os.path.join("static", "uploads", uploaded_file.filename)
    uploaded_file.save(save_path)

    # Insecure file permissions
    os.chmod(save_path, 0o777)

    return jsonify({
        "message": "File uploaded",
        "path": save_path,
        "public_url": f"/static/uploads/{uploaded_file.filename}"
    })


@app.route("/extract-zip", methods=["POST"])
def extract_zip():
    uploaded_file = request.files.get("file")

    if not uploaded_file:
        return jsonify({"error": "No zip uploaded"}), 400

    zip_path = os.path.join("uploads", uploaded_file.filename)
    uploaded_file.save(zip_path)

    extract_path = request.form.get("extract_path", "uploads/extracted")

    # Zip Slip risk
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    return jsonify({"message": "Zip extracted", "extract_path": extract_path})


@app.route("/deserialize", methods=["POST"])
def deserialize_data():
    raw_data = request.data

    # Insecure deserialization
    data = pickle.loads(raw_data)

    return jsonify({"data": str(data)})


@app.route("/calculate", methods=["POST"])
def calculate():
    expression = request.form.get("expression")

    # Dangerous eval usage
    result = eval(expression)

    return jsonify({"result": result})


@app.route("/execute-python", methods=["POST"])
def execute_python():
    code = request.form.get("code")

    local_vars = {}

    # Remote code execution risk
    exec(code, {}, local_vars)

    return jsonify({"locals": str(local_vars)})


@app.route("/load-config", methods=["POST"])
def load_config():
    config_text = request.data.decode("utf-8")

    # Unsafe YAML loading
    config = yaml.load(config_text, Loader=yaml.Loader)

    return jsonify({"config": str(config)})


@app.route("/render-template", methods=["POST"])
def render_user_template():
    template = request.form.get("template")

    # Server-Side Template Injection
    return render_template_string(template)


@app.route("/fetch-url")
def fetch_url():
    url = request.args.get("url")

    # SSRF + no timeout + TLS verification disabled
    response = requests.get(url, verify=False)

    return jsonify({
        "status": response.status_code,
        "content": response.text[:1000]
    })


@app.route("/import-avatar")
def import_avatar():
    avatar_url = request.args.get("url")
    user_id = request.args.get("user_id")

    # SSRF + arbitrary file write style behavior
    response = requests.get(avatar_url, verify=False)

    avatar_path = f"static/uploads/avatar_{user_id}.img"

    with open(avatar_path, "wb") as f:
        f.write(response.content)

    return jsonify({"message": "Avatar imported", "path": avatar_path})


@app.route("/redirect")
def open_redirect():
    next_url = request.args.get("next", "https://example.com")

    # Open Redirect
    return redirect(next_url)


@app.route("/hash-password", methods=["POST"])
def hash_password():
    password = request.form.get("password", "")

    # Weak hashing: MD5 + no salt
    md5_hash = hashlib.md5(password.encode()).hexdigest()

    # Weak hashing: SHA1 + no salt
    sha1_hash = hashlib.sha1(password.encode()).hexdigest()

    return jsonify({
        "md5": md5_hash,
        "sha1": sha1_hash
    })


@app.route("/reset-password", methods=["POST"])
def reset_password():
    email = request.form.get("email")

    # Weak random token generation
    token = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))

    conn = get_db()
    cursor = conn.cursor()

    # SQL Injection
    cursor.execute(f"UPDATE users SET reset_token = '{token}' WHERE email = '{email}'")
    conn.commit()

    # Sensitive token returned directly
    return jsonify({
        "message": "Reset token generated",
        "email": email,
        "reset_token": token
    })


@app.route("/change-password", methods=["POST"])
def change_password():
    user_id = request.form.get("user_id")
    new_password = request.form.get("new_password")

    conn = get_db()
    cursor = conn.cursor()

    # Broken authentication: no old password, no token, no session validation
    cursor.execute(
        f"UPDATE users SET password = '{new_password}' WHERE id = {user_id}"
    )
    conn.commit()

    return jsonify({"message": "Password changed"})


@app.route("/transfer-money", methods=["POST"])
def transfer_money():
    from_user = request.form.get("from_user")
    to_user = request.form.get("to_user")
    amount = request.form.get("amount")

    conn = get_db()
    cursor = conn.cursor()

    # No auth, no CSRF protection, no validation, no transaction safety
    cursor.execute(f"UPDATE accounts SET balance = balance - {amount} WHERE user_id = {from_user}")
    cursor.execute(f"UPDATE accounts SET balance = balance + {amount} WHERE user_id = {to_user}")

    conn.commit()

    return jsonify({"message": "Transfer completed"})


@app.route("/api/internal-data")
def internal_data():
    token = request.headers.get("X-Internal-Token")

    # Weak static token auth
    if token != INTERNAL_API_TOKEN:
        return jsonify({"error": "Invalid token"}), 403

    return jsonify({
        "database": DATABASE,
        "admin_password": ADMIN_PASSWORD,
        "aws_access_key": AWS_ACCESS_KEY,
        "aws_secret_key": AWS_SECRET_KEY,
        "stripe_api_key": STRIPE_API_KEY
    })


@app.route("/debug-env")
def debug_env():
    # Sensitive environment variable exposure
    return jsonify(dict(os.environ))


@app.route("/debug-request", methods=["GET", "POST"])
def debug_request():
    # Sensitive request data exposure
    return jsonify({
        "headers": dict(request.headers),
        "args": request.args.to_dict(),
        "form": request.form.to_dict(),
        "cookies": request.cookies
    })


@app.route("/logs/write", methods=["POST"])
def write_log():
    event = request.form.get("event", "")

    # Log injection risk
    with open("app.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow()} - {event}\n")

    return jsonify({"message": "Log written"})


@app.route("/logs/read")
def read_logs():
    # Information disclosure
    with open("app.log", "r", encoding="utf-8") as f:
        logs = f.read()

    return f"<pre>{logs}</pre>"


@app.route("/report")
def generate_report():
    user_id = request.args.get("user_id", "anonymous")
    content = request.args.get("content", "")

    # Predictable temporary file path
    report_path = f"/tmp/report_{user_id}.txt"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return send_file(report_path)


@app.route("/backup-db")
def backup_db():
    destination = request.args.get("destination", "backup.db")

    # Arbitrary file write location
    with open(DATABASE, "rb") as src:
        data = src.read()

    with open(destination, "wb") as dst:
        dst.write(data)

    return jsonify({"message": "Database backup created", "destination": destination})


@app.route("/bulk-query", methods=["POST"])
def bulk_query():
    raw_sql = request.form.get("sql")

    conn = get_db()
    cursor = conn.cursor()

    # Dangerous raw SQL execution
    cursor.executescript(raw_sql)
    conn.commit()

    return jsonify({"message": "SQL executed"})


@app.route("/base64-decode", methods=["POST"])
def base64_decode():
    encoded = request.form.get("data", "")

    decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")

    # Reflected decoded content without escaping
    return f"<pre>{decoded}</pre>"


@app.route("/trust-header")
def trust_header():
    # Authentication bypass by trusting client-controlled header
    user_id = request.headers.get("X-User-Id", "1")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, username, role FROM users WHERE id = {user_id}")
    user = cursor.fetchone()

    return jsonify({"authenticated_as": user})


@app.route("/generate-reset-link")
def generate_reset_link():
    email = request.args.get("email")

    # Host header injection risk
    host = request.headers.get("Host")
    reset_token = "".join(random.choice(string.ascii_letters) for _ in range(10))

    reset_link = f"http://{host}/reset-password?token={reset_token}&email={email}"

    return jsonify({
        "email": email,
        "reset_link": reset_link
    })


@app.route("/invoice/<invoice_id>")
def get_invoice(invoice_id):
    # IDOR: anyone can access any invoice by changing invoice_id
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, user_id, amount, card_number FROM invoices WHERE id = {invoice_id}")
    invoice = cursor.fetchone()

    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    return jsonify({
        "invoice_id": invoice[0],
        "user_id": invoice[1],
        "amount": invoice[2],
        "card_number": invoice[3]
    })


@app.route("/save-settings", methods=["POST"])
def save_settings():
    data = request.get_json(force=True)

    user_id = data.get("user_id")
    settings = json.dumps(data)

    conn = get_db()
    cursor = conn.cursor()

    # Mass assignment style issue + no validation
    cursor.execute(f"UPDATE users SET settings = '{settings}' WHERE id = {user_id}")
    conn.commit()

    return jsonify({"message": "Settings saved", "settings": data})


@app.route("/error-demo")
def error_demo():
    filename = request.args.get("filename")

    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        # Verbose error disclosure
        return jsonify({
            "error": str(e),
            "type": str(type(e)),
            "filename": filename
        }), 500


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            email TEXT,
            role TEXT,
            api_key TEXT,
            ssn TEXT,
            bio TEXT,
            reset_token TEXT,
            settings TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            balance REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            card_number TEXT
        )
    """)

    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM accounts")
    cursor.execute("DELETE FROM invoices")

    # Plaintext passwords + sensitive data in DB
    cursor.execute("""
        INSERT INTO users 
        (username, password, email, role, api_key, ssn, bio, reset_token, settings)
        VALUES
        ('admin', 'admin123', 'admin@example.com', 'admin', 'api-key-admin-123', '111-22-3333', '<b>Admin user</b>', '', '{}'),
        ('kerem', 'password123', 'kerem@example.com', 'user', 'api-key-user-456', '222-33-4444', '<script>alert("stored-xss")</script>', '', '{}'),
        ('test', 'test123', 'test@example.com', 'user', 'api-key-test-789', '333-44-5555', 'Regular user', '', '{}')
    """)

    cursor.execute("INSERT INTO accounts (user_id, balance) VALUES (1, 10000)")
    cursor.execute("INSERT INTO accounts (user_id, balance) VALUES (2, 500)")
    cursor.execute("INSERT INTO accounts (user_id, balance) VALUES (3, 250)")

    cursor.execute("""
        INSERT INTO invoices (user_id, amount, card_number)
        VALUES
        (1, 999.99, '4111111111111111'),
        (2, 149.99, '5555555555554444'),
        (3, 49.99, '4000000000000002')
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("uploads/extracted", exist_ok=True)
    os.makedirs("static/uploads", exist_ok=True)

    init_db()

    # Insecure host binding + debug enabled
    app.run(host="0.0.0.0", port=5000, debug=True)