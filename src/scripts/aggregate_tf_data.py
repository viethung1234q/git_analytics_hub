#!/usr/bin/env python3
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
        ymd = sys.argv[1]
        hms = sys.argv[2]
        process_date = datetime.strptime(f"{ymd} {hms}", "%Y-%m-%d %H:%M:%S")
        logging.info(f"Process date: {process_date}")

        # Start aggregate data
        transformer = DataLakeTransformer('gharchive/events')
        transformer.aggregate_silver_data(process_date)
        
        logging.info(f"{process_date}: Successfully aggregated to gold bucket")
    except Exception as e:
        logging.error(f"Got error while aggregate data to gold bucket: {e}")


if __name__ == "__main__":
    main()
