import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, render_template, request, jsonify

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads a .env file in this folder, if one exists
except ImportError:
    pass  # python-dotenv not installed — fine if you're setting env vars another way

base_dir = Path(__file__).resolve().parent
db_path = base_dir / "contacts.db"
email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# --- outgoing email settings (Brevo's HTTP API — not SMTP) ---
# Render's free tier blocks outbound SMTP ports (25/465/587) entirely, so
# sending over plain HTTPS via Brevo's REST API sidesteps that restriction.
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Bleu Method")
CONTACT_TO_EMAIL = os.environ.get("CONTACT_TO_EMAIL", "junaid@bleumethod.com")
# Supports multiple recipients: set CONTACT_TO_EMAIL to a comma-separated
# list, e.g. "junaid@bleumethod.com,arsalanwagle9@gmail.com" — every
# submission gets emailed to all of them.
CONTACT_TO_EMAILS = [addr.strip() for addr in CONTACT_TO_EMAIL.split(",") if addr.strip()]

app = Flask(__name__)


def init_db():
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        con.commit()


init_db()


def send_notification_email(name, email, message):
    """
    Emails the submission to everyone in CONTACT_TO_EMAILS using Brevo's
    HTTP API (not SMTP — Render's free tier blocks outbound SMTP ports
    entirely, but this runs over plain HTTPS so it isn't affected).
    Returns True/False so a failure here never breaks the form — the
    submission is already saved in the database either way.
    """
    if not (BREVO_API_KEY and BREVO_SENDER_EMAIL):
        app.logger.warning("Brevo not configured — skipping email notification.")
        return False

    try:
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": BREVO_API_KEY,
                "accept": "application/json",
                "content-type": "application/json",
            },
            json={
                "sender": {"email": BREVO_SENDER_EMAIL, "name": BREVO_SENDER_NAME},
                "to": [{"email": addr} for addr in CONTACT_TO_EMAILS],
                "replyTo": {"email": email, "name": name},
                "subject": f"New message from {name} — bleumethod.com",
                "textContent": f"From: {name} <{email}>\n\n{message}",
            },
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as e:
        app.logger.error(f"Failed to send notification email: {e}")
        return False


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return jsonify({"ok": False, "error": "All fields are required."}), 400
    if len(name) > 120 or len(email) > 200 or len(message) > 4000:
        return jsonify({"ok": False, "error": "One of the fields is too long."}), 400
    if not email_re.match(email):
        return jsonify({"ok": False, "error": "Please enter a valid email."}), 400

    with sqlite3.connect(db_path) as con:
        con.execute(
            "INSERT INTO contacts (name, email, message, created_at) VALUES (?, ?, ?, ?)",
            (name, email, message, datetime.now(timezone.utc).isoformat()),
        )
        con.commit()

    send_notification_email(name, email, message)

    return jsonify({"ok": True})


@app.route("/api/contacts", methods=["GET"])
def list_contacts():
    """
    Simple admin view of submissions, protected by a token so it's not wide open.
    Set ADMIN_TOKEN as an environment variable, then visit:
    /api/contacts?token=YOUR_TOKEN
    """
    token = request.args.get("token", "")
    expected = os.environ.get("ADMIN_TOKEN")
    if not expected or token != expected:
        return jsonify({"ok": False, "error": "Not authorized."}), 401

    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            "SELECT id, name, email, message, created_at FROM contacts ORDER BY id DESC"
        ).fetchall()

    return jsonify({"ok": True, "contacts": [dict(r) for r in rows]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)