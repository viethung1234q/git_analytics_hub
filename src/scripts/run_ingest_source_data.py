import sys
import os
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path: ~/git_analytics_hub/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.data_lake_ingester import DataLakeIngester

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s:%(filename)s] - %(message)s')

def main():
    try:
        ingester = DataLakeIngester("gharchive/events")
        now = datetime.utcnow() # 2024-11-27 15:03:47.349568
        # 1 hour before to ensure data availability at source
        process_date = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)  # 2024-11-27 14:00:00

        # Start ingest data
        ingester.ingest_hourly(process_date)

        logging.info(f"Successfully ingested data for {process_date}")
    except Exception as e:
        logging.error(f"Got error while ingest data to bronze bucket: {e}")

if __name__ == "__main__":
    main()