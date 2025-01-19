import duckdb
import configparser
from datetime import datetime
import logging
import os
from datetime import datetime

class DataLakeTransformer:
    """
    A class for transforming and moving data from bronze bucket to silver bucket.
    """
    def __init__(self, dataset_base_path):
        self.config = self.load_config()
        self.dataset_base_path = dataset_base_path
        self.con = self.set_duckdb_connection()
        self.set_duckdb_s3_credentials()
        logging.info("DuckDB connection initiated")

    def set_duckdb_connection(self):
        conn = duckdb.connect()
        con.install_extension("httpfs")
        con.load_extension("httpfs")
        
        return conn

    def set_duckdb_s3_credentials(self):
        self.con.execute(f"SET s3_access_key_id='{self.config.get('minio', 'access_key')}'")
        self.con.execute(f"SET s3_secret_access_key='{self.config.get('minio', 'secret_key')}'")
        self.con.execute(f"SET s3_endpoint='{self.config.get('minio', 'endpoint')}'")
        self.con.execute(f"SET s3_region='{self.config.get('minio', 'region')}'")
        self.con.execute(f"SET s3_url_style='{self.config.get('minio', 'url_style')}'")
        self.con.execute(f"SET s3_use_ssl='{self.config.get('minio', 'use_ssl')}'")

    def load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
        config.read(config_path)

        return config

    def serialise_raw_data(self):
        pass
