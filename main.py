import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://fortune.com/ranking/fortune500/")

WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@data-cy='search-action']"))
).click()

WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//table/tbody/tr"))
)

rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

data = []
for row in rows:
    try:
        row_data = [
            int(row.find_element(By.XPATH, './td[1]').text),
            row.find_element(By.XPATH, './td[2]').text,
            row.find_element(By.XPATH, './td[3]').text,
            row.find_element(By.XPATH, './td[4]').text,
            row.find_element(By.XPATH, './td[5]').text,
            row.find_element(By.XPATH, './td[6]').text,
            row.find_element(By.XPATH, './td[7]').text,
            row.find_element(By.XPATH, './td[8]').text,
            row.find_element(By.XPATH, './td[9]').text,
            row.find_element(By.XPATH, './td[10]').text,
            row.find_element(By.XPATH, './td[11]').text
        ]
        data.append(row_data)
    except Exception as e:
        print("Skipping row due to error:", e)


db = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="mits123456",
    database="fort500"
)
cursor = db.cursor()
#1 create db
cursor.execute("CREATE DATABASE IF NOT EXISTS FORT500" )
cursor.execute("SHOW DATABASES")


#2 create table
create_table = """
CREATE TABLE IF NOT EXISTS tblfort500 (
    sr_no INT,
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
"""
cursor.execute(create_table)
db.commit()

#3 insert in table
insert_query = """
INSERT INTO tblfort500 (
    sr_no, name, revenue, rev_per, profit, prof_per, asset, 
    market_value, rank_change_1000, employees, rank_change_500
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor.executemany(insert_query, data)
db.commit()

print("Values inserted into MySQL database.")

driver.quit()
cursor.close()
db.close()