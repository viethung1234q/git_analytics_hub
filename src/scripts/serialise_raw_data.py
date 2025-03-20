import sys
import os
import logging
from datetime import datetime, timedelta

# Add the parent directory to the Python path: ~/git_analytics_hub/
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from src.datalake_transformer import DataLakeTransformer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s:%(filename)s:%(lineno)d] - %(message)s')

def main():
    try:
        transformer = DataLakeTransformer("gharchive/events")
        now = datetime.now()  # 2024-11-27 15:03:47.349568
        process_date = now.replace(minute=0, second=0, microsecond=0) - timedelta(days=1)
        logging.info(f"process_date: {process_date}")

        # Start transform data
        transformer.serialise_raw_data(process_date)

        logging.info(f"Successfully serialised raw data for {process_date}")
    except Exception as e:
        logging.error(f"Got error while serialise data to silver bucket: {e}")

if __name__ == "__main__":
    main()
