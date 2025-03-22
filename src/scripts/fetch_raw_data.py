import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the Python path: ~/git_analytics_hub/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.datalake_ingester import DataLakeIngester

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s:%(filename)s:%(lineno)d] - %(message)s')

def main():
    try:
        ymd = sys.argv[1]
        hms = sys.argv[2]
        process_date = datetime.strptime(f"{ymd} {hms}", "%Y-%m-%d %H:%M:%S")
        logging.info(f"Process date: {process_date}")

        # Start ingest data
        ingester = DataLakeIngester("gharchive/events")
        ingester.ingest_hourly(process_date)

        logging.info(f"{process_date}: Successfully ingested data to bronze bucket")
    except Exception as e:
        logging.error(f"Got error while ingest data to bronze bucket: {e}")

if __name__ == "__main__":
    main()