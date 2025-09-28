📊 Fortune-500 Dashboard

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)
![Dash](https://img.shields.io/badge/Dashboard-Plotly%20Dash-purple)
![Selenium](https://img.shields.io/badge/Scraper-Selenium-brightgreen)


🔎 Overview

The Fortune-500 Dashboard is a complete pipeline that:

Scrapes the latest Fortune 500 company data

Stores it in a MySQL database

Visualizes insights in an interactive dashboard built with Dash

It’s designed for automation, analysis, and visualization of company trends like revenue, ranking, and industries.

🚀 Key Features

✅ Automated scraping of company details (name, revenue, rank, industry, etc.)
✅ Structured storage in MySQL database
✅ Scheduler to run scraping jobs periodically
✅ Interactive dashboard with graphs, charts & filters
✅ Export data to CSV / Excel
✅ Secure setup with .env for credentials
✅ Built-in logging & alerts for scraper runs

📂 Project Structure
### Project Structure
 
│── style.css # CSS and frontend assets (if any)
│
│── api.py # API or scraping logic
│── csvfileconversion.py # CSV/Excel conversion utilities
│── final.py # Main processing script
│── log changes.py # Logs / changes tracking
│── logging system.py # Logging utilities
│── main.py # Main program
│── normalization.py # Data normalization utilities
│── run.py # Entry point (scheduler + scraper)
│── .env.example # Example environment variables
│── requirements.txt # Python dependencies


🛠️ Tech Stack

Python 3.10+

Selenium → Web scraping

MySQL → Database storage

Dash / Plotly → Interactive dashboard

APScheduler → Task scheduling

pandas → Data manipulation

⚡ Setup
1️⃣ Clone the repository
git clone https://github.com/MitaliSwamy/Fortune-500-Dashboard.git
cd Fortune-500-Dashboard

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Configure .env

Create a .env file in the project root with your database and email credentials (see .env.example).

4️⃣ Run the project
python run.py

📝 Notes

Ensure your MySQL server is running and accessible.

Adjust scraping intervals in run.py as needed.

Email alerts will be sent on scraper failure (configured in .env).
