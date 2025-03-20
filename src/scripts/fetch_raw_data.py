import sys
import os
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path: ~/git_analytics_hub/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.datalake_ingester import DataLakeIngester

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s:%(filename)s:%(lineno)d] - %(message)s')

def main():
    try:
        logging.info(f"{sys.argv}")

        ingester = DataLakeIngester("gharchive/events")
        now = datetime.now() # 2024-11-27 15:03:47.349568
        process_date = now.replace(minute=0, second=0, microsecond=0) - timedelta(days=1)

        # Start ingest data
        ingester.ingest_hourly(process_date)

        logging.info(f"Successfully ingested data for {process_date}")
    except Exception as e:
        logging.error(f"Got error while ingest data to bronze bucket: {e}")
    
    print(f"{process_date}")

if __name__ == "__main__":
    main()