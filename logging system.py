import mysql.connector
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# ---------------- DB CONFIG ----------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "mits123456",
    "database": "fort500"
}
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# --- ensure run_logs table exists ---
cursor.execute("""
CREATE TABLE IF NOT EXISTS run_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20),
    rows_added INT,
    rows_updated INT,
    rows_deleted INT,
    error_message TEXT
)
""")
conn.commit()
# ---------------- LOGGING ----------------
def log_run(status, rows_added=0, rows_updated=0, rows_deleted=0, error_message=None):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    query = """
    INSERT INTO run_logs (status, rows_added, rows_updated, rows_deleted, error_message)
    VALUES (%s, %s, %s, %s, %s)
    """
    cursor.execute(query, (status, rows_added, rows_updated, rows_deleted, error_message))
    conn.commit()

    cursor.close()
    conn.close()
    print(f"✅ Log saved: {status} ({datetime.now()})")

# ---------------- EMAIL ALERTS ----------------
def send_email(subject, body, to_email="dummymailforwork07@gmail.com"):
    from_email = "dummymailforwork07@gmail.com"
    password = "ykol pqye bbmi dmzj"  # ⚠️ use Gmail App Password

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, password)
        server.send_message(msg)

# ---------------- SCRAPER WORKFLOW ----------------
try:
    # Example: fetch companies
    conn = mysql.connector.connect(**DB_CONFIG)
    df = pd.read_sql("SELECT * FROM companies", conn)

    # Pretend we scraped 10 new rows and updated 3
    rows_added, rows_updated, rows_deleted = 10, 3, 0

    # Save run log
    log_run("success", rows_added, rows_updated, rows_deleted)

    # (Optional) send success email
    send_email(
        "✅ Scraper Run Successful",
        f"Run at {datetime.now()}\nAdded: {rows_added}, Updated: {rows_updated}, Deleted: {rows_deleted}"
    )

    conn.close()

except Exception as e:
    error_msg = str(e)
    log_run("fail", error_message=error_msg)

    # Send failure alert
    send_email(
        "❌ Scraper Run Failed",
        f"Run at {datetime.now()}\nError: {error_msg}"
    )
