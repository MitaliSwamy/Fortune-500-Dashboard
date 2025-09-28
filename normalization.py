import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "mits123456",     
    "database": "fort500"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def create_normalized_tables():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS fort500")
    cursor.execute("USE fort500")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        sr_no INT PRIMARY KEY,
        name VARCHAR(255)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS financials (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sr_no INT,
        revenue VARCHAR(50),
        rev_per VARCHAR(50),
        profit VARCHAR(50),
        prof_per VARCHAR(50),
        asset VARCHAR(50),
        market_value VARCHAR(50),
        employees VARCHAR(50),
        run_timestamp DATETIME,
        FOREIGN KEY (sr_no) REFERENCES companies(sr_no)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rankings (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sr_no INT,
        rank_change_1000 VARCHAR(50),
        rank_change_500 VARCHAR(50),
        run_timestamp DATETIME,
        FOREIGN KEY (sr_no) REFERENCES companies(sr_no)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS change_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        sr_no INT,
        table_name VARCHAR(50),
        column_name VARCHAR(100),
        old_value TEXT,
        new_value TEXT,
        change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sr_no) REFERENCES companies(sr_no)
    )
    """)

    db.commit()
    cursor.close()
    db.close()
    print("Normalized tables.")


def migrate_from_flat_table():
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("USE fort500")

    # check if tblfort500 exists
    cursor.execute("SHOW TABLES LIKE 'tblfort500'")
    if cursor.fetchone() is None:
        print("No tblfort500 found; skipping migration.")
        cursor.close()
        db.close()
        return

    cursor.execute("SELECT * FROM tblfort500")
    rows = cursor.fetchall()
    if not rows:
        print("tblfort500 is empty; nothing to migrate.")
        cursor.close()
        db.close()
        return

    for r in rows:
        sr_no = r['sr_no']
        name = r['name']

        # insert company if not exists
        cursor.execute("SELECT sr_no FROM companies WHERE sr_no = %s", (sr_no,))
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO companies (sr_no, name) VALUES (%s, %s)", (sr_no, name))

        # insert financials row
        cursor.execute("""
            INSERT INTO financials (sr_no, revenue, rev_per, profit, prof_per, asset, market_value, employees, run_timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            sr_no, r['revenue'], r['rev_per'], r['profit'], r['prof_per'], r['asset'], r['market_value'], r['employees'], datetime.now()
        ))

        # insert rankings row
        cursor.execute("""
            INSERT INTO rankings (sr_no, rank_change_1000, rank_change_500, run_timestamp)
            VALUES (%s,%s,%s,%s)
        """, (sr_no, r['rank_change_1000'], r['rank_change_500'], datetime.now()))

    db.commit()
    cursor.close()
    db.close()
    print(f"Migrated {len(rows)} rows from tblfort500 into normalized schema.")


def store_scraped_rows(data_rows, run_ts=None):
    """
    Insert a new run of scraped rows (list of rows in the same format you used):
    data_rows: list of lists or list of dicts. Expected list order:
        [sr_no, name, revenue, rev_per, profit, prof_per, asset, market_value, rank_change_1000, employees, rank_change_500]
    run_ts: optional datetime; if not provided, uses datetime.now()

    For each row:
     - ensure company exists in companies
     - fetch latest financials & rankings (if any) and log differences into change_logs
     - insert a new row into financials and rankings with run_timestamp=run_ts
    """
    if run_ts is None:
        run_ts = datetime.now()

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("USE fort500")

    col_names = ["sr_no", "name", "revenue", "rev_per", "profit", "prof_per", "asset", "market_value", "rank_change_1000", "employees", "rank_change_500"]

    for row in data_rows:
        # normalize input to dict
        if isinstance(row, list) or isinstance(row, tuple):
            row_dict = dict(zip(col_names, row))
        elif isinstance(row, dict):
            row_dict = row
        else:
            continue

        sr_no = row_dict['sr_no']
        name = row_dict['name']

        # Ensure company present
        cursor.execute("SELECT sr_no, name FROM companies WHERE sr_no = %s", (sr_no,))
        company = cursor.fetchone()
        if not company:
            cursor.execute("INSERT INTO companies (sr_no, name) VALUES (%s,%s)", (sr_no, name))
        else:
            # if name changed, log it and update
            if str(company['name']) != str(name):
                cursor.execute("""
                    INSERT INTO change_logs (sr_no, table_name, column_name, old_value, new_value)
                    VALUES (%s, %s, %s, %s, %s)
                """, (sr_no, 'companies', 'name', company['name'], name))
                cursor.execute("UPDATE companies SET name = %s WHERE sr_no = %s", (name, sr_no))

        # Fetch latest financials for comparisons
        cursor.execute("""
            SELECT * FROM financials WHERE sr_no = %s ORDER BY run_timestamp DESC LIMIT 1
        """, (sr_no,))
        latest_fin = cursor.fetchone()

        # Compare financial columns and log changes
        fin_cols = ['revenue', 'rev_per', 'profit', 'prof_per', 'asset', 'market_value', 'employees']
        if latest_fin:
            for col in fin_cols:
                old_val = latest_fin.get(col)
                new_val = row_dict.get(col)
                if str(old_val) != str(new_val):
                    cursor.execute("""
                        INSERT INTO change_logs (sr_no, table_name, column_name, old_value, new_value)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (sr_no, 'financials', col, str(old_val), str(new_val)))

        # Insert new financials row
        cursor.execute("""
            INSERT INTO financials (sr_no, revenue, rev_per, profit, prof_per, asset, market_value, employees, run_timestamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (sr_no, row_dict['revenue'], row_dict['rev_per'], row_dict['profit'], row_dict['prof_per'],
              row_dict['asset'], row_dict['market_value'], row_dict['employees'], run_ts))

        # Rankings: compare & insert
        cursor.execute("""
            SELECT * FROM rankings WHERE sr_no = %s ORDER BY run_timestamp DESC LIMIT 1
        """, (sr_no,))
        latest_rank = cursor.fetchone()
        for col in ['rank_change_1000', 'rank_change_500']:
            old_val = latest_rank.get(col) if latest_rank else None
            new_val = row_dict.get(col)
            if str(old_val) != str(new_val):
                cursor.execute("""
                    INSERT INTO change_logs (sr_no, table_name, column_name, old_value, new_value)
                    VALUES (%s,%s,%s,%s,%s)
                """, (sr_no, 'rankings', col, str(old_val), str(new_val)))

        cursor.execute("""
            INSERT INTO rankings (sr_no, rank_change_1000, rank_change_500, run_timestamp)
            VALUES (%s,%s,%s,%s)
        """, (sr_no, row_dict['rank_change_1000'], row_dict['rank_change_500'], run_ts))

    db.commit()
    cursor.close()
    db.close()
    print(f"Inserted {len(data_rows)} rows into normalized schema (financials + rankings).")


if __name__ == "__main__":
    # Run migration & create tables
    create_normalized_tables()
    migrate_from_flat_table()
