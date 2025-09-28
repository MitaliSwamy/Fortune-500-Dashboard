import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime


# 1. Scrape Data

driver = webdriver.Chrome()
driver.get("https://fortune.com/ranking/fortune500/")

button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@data-cy='search-action']"))
)
# Scroll into view first
driver.execute_script("arguments[0].scrollIntoView(true);", button)

# Now click via JS to avoid interception by overlays
driver.execute_script("arguments[0].click();", button)

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//table/tbody/tr"))
)

rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

data = []
for row in rows:
    try:
        row_data = [
            int(row.find_element(By.XPATH, './td[1]').text),   # sr_no
            row.find_element(By.XPATH, './td[2]').text,       # name
            row.find_element(By.XPATH, './td[3]').text,       # revenue
            row.find_element(By.XPATH, './td[4]').text,       # rev_per
            row.find_element(By.XPATH, './td[5]').text,       # profit
            row.find_element(By.XPATH, './td[6]').text,       # prof_per
            row.find_element(By.XPATH, './td[7]').text,       # asset
            row.find_element(By.XPATH, './td[8]').text,       # market_value
            row.find_element(By.XPATH, './td[9]').text,       # rank_change_1000
            row.find_element(By.XPATH, './td[10]').text,      # employees
            row.find_element(By.XPATH, './td[11]').text       # rank_change_500
        ]
        data.append(row_data)
    except Exception as e:
        print("Skipping row due to error:", e)

driver.quit()


# 2. MySQL Connection

db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="mits123456", 
    database="fort500"
)
cursor = db.cursor()

# main table exists
cursor.execute("""
CREATE TABLE IF NOT EXISTS tblfort500 (
    sr_no INT PRIMARY KEY,
    name VARCHAR(255),
    revenue VARCHAR(50),
    rev_per VARCHAR(50),
    profit VARCHAR(50),
    prof_per VARCHAR(50),
    asset VARCHAR(50),
    market_value VARCHAR(50),
    rank_change_1000 VARCHAR(50),
    employees VARCHAR(50),
    rank_change_500 VARCHAR(50)
)
""")

# New table for logging changes
cursor.execute("""
CREATE TABLE IF NOT EXISTS change_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    sr_no INT,
    field VARCHAR(50),
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    timestamp DATETIME,
    FOREIGN KEY (sr_no) REFERENCES tblfort500(sr_no)
)
""")


# 3. Insert or Detect Changes

for row in data:
    sr_no = row[0]
    cursor.execute("SELECT * FROM tblfort500 WHERE sr_no = %s", (sr_no,))
    existing = cursor.fetchone()

    if not existing:
        # New company → insert fresh
        cursor.execute("""
        INSERT INTO tblfort500 (
            sr_no, name, revenue, rev_per, profit, prof_per, asset, 
            market_value, rank_change_1000, employees, rank_change_500
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, row)
    else:
        # Compare field by field
        col_names = [
            "sr_no", "name", "revenue", "rev_per", "profit", "prof_per",
            "asset", "market_value", "rank_change_1000", "employees", "rank_change_500"
        ]
        for i, col in enumerate(col_names):
            new_val = row[i]
            old_val = existing[i]
            if str(new_val) != str(old_val):
                # Log the change
                cursor.execute("""
                INSERT INTO change_logs (sr_no, field, old_value, new_value, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                """, (sr_no, col, str(old_val), str(new_val), datetime.now()))

                # Update main table
                cursor.execute(f"UPDATE tblfort500 SET {col} = %s WHERE sr_no = %s", (new_val, sr_no))

db.commit()
cursor.close()
db.close()
print("Scraping + change detection complete")
