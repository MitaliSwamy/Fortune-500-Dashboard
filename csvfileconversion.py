import pandas as pd
import mysql.connector
import os
import warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy")

# DB config
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "mits123456",
    "database": "fort500"
}

# Ensure 'exports' folder exists
os.makedirs("exports", exist_ok=True)

# Connection
conn = mysql.connector.connect(**DB_CONFIG)

# --- Export current data ---
query = "SELECT * FROM companies"
df = pd.read_sql(query, conn)

df.to_csv("exports/companies.csv", index=False, encoding="utf-8-sig")
df.to_excel("exports/companies.xlsx", index=False, engine="openpyxl")

# --- Export change logs ---
query_logs = "SELECT * FROM change_logs"
df_logs = pd.read_sql(query_logs, conn)

df_logs.to_csv("exports/change_logs.csv", index=False, encoding="utf-8-sig")
df_logs.to_excel("exports/change_logs.xlsx", index=False, engine="openpyxl")

# Close connection
conn.close()

