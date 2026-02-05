import time
import schedule
import logging
import sys
from .cron_update import run_update

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('update.log')
    ]
)

def job():
    logging.info("Starting scheduled update job...")
    try:
        run_update()
        logging.info("Scheduled update job completed.")
    except Exception as e:
        logging.error(f"Job failed: {e}")

def main():
    # Run once on startup to ensure we have data even if machine shuts down soon
    logging.info("Scheduler started. Running initial update...")
    job()
    
    # Schedule the job every 60 minutes
    # This ensures we capture the latest state throughout the day.
    # Since save_daily_snapshot assumes one entry per day (UPSERT), 
    # it will just update today's record with the latest value.
    schedule.every(60).minutes.do(job)
    
    logging.info("Scheduler configured: Running every 60 minutes.")
    
    # Also print next run for verification
    logging.info(f"Next run: {schedule.next_run()}")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    # We need to install 'schedule' lib if not present, but better to add to requirements.txt
    # For now assuming user will rebuild image with updated requirements or we add it to requirements.txt
    main()
