from final import scrape_data   # your scraper function
from api import start_dashboard # your Dash app function
from apscheduler.schedulers.blocking import BlockingScheduler

def run_scraper():
    scrape_data()

scheduler = BlockingScheduler()
scheduler.add_job(run_scraper, 'interval', days=1)  # run daily

if __name__ == "__main__":
    run_scraper()        # run once immediately
    start_dashboard()    # launch dashboard
    scheduler.start()    # start scheduler for repeated runs
