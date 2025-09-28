from flask import Flask, jsonify, request
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "mits123456",   
    "database": "fort500"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

app = Flask(__name__)

@app.route("/companies", methods=["GET"])
def get_companies():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM companies ORDER BY sr_no")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route("/company/<int:sr_no>", methods=["GET"])
def get_company(sr_no):
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM companies WHERE sr_no = %s", (sr_no,))
    company = cursor.fetchone()
    if not company:
        cursor.close()
        db.close()
        return jsonify({"error": "company not found"}), 404

    # latest financials
    cursor.execute("""
        SELECT * FROM financials WHERE sr_no = %s ORDER BY run_timestamp DESC LIMIT 1
    """, (sr_no,))
    financials = cursor.fetchone() or {}

    # latest rankings
    cursor.execute("""
        SELECT * FROM rankings WHERE sr_no = %s ORDER BY run_timestamp DESC LIMIT 1
    """, (sr_no,))
    rankings = cursor.fetchone() or {}

    cursor.close()
    db.close()
    return jsonify({
        "company": company,
        "financials": financials,
        "rankings": rankings
    })

@app.route("/top/<int:n>", methods=["GET"])
def get_top_by_revenue(n):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.sr_no, c.name, f.revenue, f.profit, f.market_value
        FROM companies c
        JOIN financials f ON c.sr_no = f.sr_no
        WHERE f.run_timestamp = (
            SELECT MAX(run_timestamp) FROM financials f2 WHERE f2.sr_no = c.sr_no
        )
        ORDER BY CAST(REPLACE(REPLACE(f.revenue, ',', ''), '$', '') AS DECIMAL(20,2)) DESC
        LIMIT %s
    """, (n,))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route("/search", methods=["GET"])
def search_companies():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "query param 'q' is required"}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM companies WHERE LOWER(name) LIKE %s LIMIT 50", (f"%{q.lower()}%",))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route("/changes/<int:sr_no>", methods=["GET"])
def get_changes(sr_no):
    offset = int(request.args.get("offset", 0))
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM change_logs 
        WHERE sr_no = %s 
        ORDER BY change_time DESC 
        LIMIT 200 OFFSET %s
    """, (sr_no, offset))
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

@app.route("/latest_financials", methods=["GET"])
def latest_financials():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.sr_no, c.name, f.revenue, f.profit, f.market_value, f.employees
        FROM companies c
        JOIN financials f ON c.sr_no = f.sr_no
        WHERE f.run_timestamp = (
            SELECT MAX(run_timestamp) FROM financials f2 WHERE f2.sr_no = c.sr_no
        )
    """)
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True, port=5001)

