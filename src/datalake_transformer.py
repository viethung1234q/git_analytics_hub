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
        self.dataset_base_path = dataset_base_path
        self.config = self._load_config()
        self.con = self._set_duckdb_connection()
        self._set_duckdb_s3_credentials()
        logging.info("DuckDB connection initiated!")


    def _set_duckdb_connection(self):
        """
        Create connect to DuckDB and load the necessary extensions
        """
        conn = duckdb.connect()
        conn.install_extension("httpfs")
        conn.load_extension("httpfs")
        return conn


    def _set_duckdb_s3_credentials(self):
        self.con.execute(f"SET s3_access_key_id='{self.config.get('minio', 'access_key')}'")
        self.con.execute(f"SET s3_secret_access_key='{self.config.get('minio', 'secret_key')}'")
        self.con.execute(f"SET s3_endpoint='{self.config.get('minio', 'endpoint')}'")
        self.con.execute(f"SET s3_region='{self.config.get('minio', 'region')}'")
        self.con.execute(f"SET s3_url_style='{self.config.get('minio', 'url_style')}'")
        self.con.execute(f"SET s3_use_ssl='{self.config.get('minio', 'use_ssl')}'")


    def _load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
        config.read(config_path)
        return config


    def serialise_raw_data(self, process_date):
        """
        Serialize and clean raw data, then export to parquet format for the next stage.
        """
        try:
            # Retrieve source bucket and path
            source_bucket = self.config.get("datalake", "bronze_bucket")
            source_path = self._raw_hourly_file_path(
                source_bucket, self.dataset_base_path, process_date
            )

            # Register and clean raw GHArchive data
            gharchive_raw_result = self.register_raw_gharchive(source_path)
            gharchive_clean_result = self.clean_raw_gharchive(gharchive_raw_result.alias)

            # Define sink bucket and path
            sink_bucket = self.config.get("datalake", "silver_bucket")
            sink_path = self.create_sink_path(
                "clean", sink_bucket, self.dataset_base_path, process_date, True
            )

            # Serialize and export cleaned data
            logging.info(f"DuckDB - serialize and export cleaned data to {sink_path}")
            gharchive_clean_result.write_parquet(sink_path)
        except Exception as e:
            logging.error(f"Error in serialise_raw_data: {str(e)}")
            raise


    def _raw_hourly_file_path(self, source_bucket, source_base_path, process_date):
        """
        Generate the S3 path for hourly silver exported files
        """
        partitions_path = self._partition_path(process_date, True)
        s3_key = f"s3://{source_bucket}/{source_base_path}/{partitions_path}/*"
        return s3_key


    def _partition_path(self,process_date, has_hourly_partition=False):
        """
        Generate the partition path based on the process date
        """
        if has_hourly_partition:
            partition_path = process_date.strftime("%Y-%m-%d/%H")
        else:
            partition_path = process_date.strftime("%Y-%m-%d")
        return partition_path


    def _generate_export_filename(self, data_type, process_date, has_hourly_partition=False, file_extension='parquet'):
        """
        Generate a filename for the exported data file
        """
        if has_hourly_partition:
            timestamp = process_date.strftime("%Y%m%d_%H")
        else:
            timestamp = process_date.strftime("%Y%m%d")
        return f"{data_type}_{timestamp}.{file_extension}"


    def register_raw_gharchive(self, source_path):
        """
        Create an in-memory table from raw GHArchive source data
        """
        logging.info(f"DuckDB - collect source data files: {source_path}")
        self.con.execute(f"CREATE OR REPLACE TABLE gharchive_raw \
                        AS FROM read_json_auto('{source_path}', ignore_errors=true)")
        return self.con.table("gharchive_raw")


    def clean_raw_gharchive(self, raw_dataset):
        """
        Clean the raw GHArchive data and only selected attributed we are interest in.
        """
        query = f'''
        SELECT 
            id AS "event_id",
            actor.id AS "user_id",
            actor.login AS "user_name",
            actor.display_login AS "user_display_name",
            type AS "event_type",
            repo.id AS "repo_id",
            repo.name AS "repo_name",
            repo.url AS "repo_url",
            created_at AS "event_date"
        FROM '{raw_dataset}'
        '''
        logging.info("DuckDB - clean data")
        self.con.execute(f"CREATE OR REPLACE TABLE gharchive_clean AS FROM ({query})")
        return self.con.table("gharchive_clean")


    def create_sink_path(self, data_type, sink_bucket, sink_base_path, process_date, has_hourly_partition=False):
        """
        Create the full S3 path for the sink file.
        """
        partitions_path = self._partition_path(process_date, has_hourly_partition)
        sink_filename = self._generate_export_filename(data_type, process_date, has_hourly_partition)
        return f"s3://{sink_bucket}/{sink_base_path}/{partitions_path}/{sink_filename}"


    def __del__(self):
        """
        Close DuckDB connection when the object is destroyed
        """
        if hasattr(self, 'con'):
            self.con.close()