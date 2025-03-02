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
            partitions_path = self.create_partition_path(process_date, has_hourly_partition=True)
            source_path = f"s3://{source_bucket}/{self.dataset_base_path}/{partitions_path}/*"

            # Register and clean raw GHArchive data
            raw_table = self.create_raw_table(source_path)
            clean_table = self.create_clean_table(raw_table.alias)

            # Define sink bucket and path
            sink_bucket = self.config.get("datalake", "silver_bucket")
            sink_path = self.create_sink_path(
                "clean", sink_bucket, self.dataset_base_path, process_date, has_hourly_partition=True
            )

            # Serialize and export cleaned data
            logging.info(f"DuckDB - serialize and export cleaned data to {sink_path}")
            clean_table.write_parquet(sink_path)
        except Exception as e:
            logging.error(f"Error in serialise_raw_data: {str(e)}")
            raise


    def create_partition_path(self, process_date, has_hourly_partition=False):
        """
        Generate the partition path based on the process date
        """
        if has_hourly_partition:
            partition_path = process_date.strftime("%Y-%m-%d/%H")
        else:
            partition_path = process_date.strftime("%Y-%m-%d")
        return partition_path


    def generate_export_filename(self, data_type, process_date, has_hourly_partition=False, file_extension='parquet'):
        """
        Generate a filename for the exported data file
        """
        if has_hourly_partition:
            timestamp = process_date.strftime("%Y%m%d_%H")
        else:
            timestamp = process_date.strftime("%Y%m%d")
        return f"{data_type}_{timestamp}.{file_extension}"


    def create_raw_table(self, source_path, raw_table_name="raw_gharchive"):
        """
        Create an in-memory table from raw GHArchive source data
        """
        logging.info(f"DuckDB - creating table {raw_table_name} from: {source_path}")

        query = f'''
            CREATE OR REPLACE TABLE {raw_table_name} AS 
            FROM read_json_auto('{source_path}', ignore_errors=true)
        '''
        self.con.execute(f"{query}")
        return self.con.table(f"{raw_table_name}")


    def create_clean_table(self, raw_table, clean_table_name="clean_gharchive"):
        """
        Perform some data cleaning on the raw GHArchive data:
        - Only selected attributed we are interest in
        """
        logging.info(f"DuckDB - creating {clean_table_name}")

        query = f'''
        CREATE OR REPLACE TABLE {clean_table_name} AS 
        FROM (
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
            FROM '{raw_table}'
        )
        '''
        self.con.execute(f"{query}")
        return self.con.table(f"{clean_table_name}")


    def create_sink_path(self, data_type, sink_bucket, sink_base_path, process_date, has_hourly_partition=False):
        """
        Create the full S3 path for the sink file.
        """
        partitions_path = self.create_partition_path(process_date, has_hourly_partition)
        sink_filename = self.generate_export_filename(data_type, process_date, has_hourly_partition)
        return f"s3://{sink_bucket}/{sink_base_path}/{partitions_path}/{sink_filename}"


    def aggregate_silver_data(self, process_date):
        """
        Aggregate raw data and export to parquet format.
        """
        try:
            
            source_bucket = self.config.get('datalake', 'silver_bucket')
            partitions_path = self.create_partition_path(process_date, has_hourly_partition=False)
            source_path = f"s3://{source_bucket}/{self.dataset_base_path}/{partitions_path}/*/*.parquet"

            logging.info(f"DuckDB - aggregate silver data in {source_path}")
            agg_table = self.create_aggregated_table(source_path)

            sink_bucket = self.config.get('datalake', 'gold_bucket')
            sink_path = self.create_sink_path(
                'agg', sink_bucket, self.dataset_base_path, process_date
            )

            logging.info(f"DuckDB - export aggregated data to {sink_path}")
            agg_table.write_parquet(sink_path)
        except Exception as e:
            logging.error(f"Error in aggregate_silver_data: {str(e)}")
            raise


    def create_aggregated_table(self, source_path, agg_table_name="agg_gharchive"):
        """
        Aggregate the raw GHArchive data.
        """
        logging.info(f"DuckDB - creating {agg_table_name}")

        query = f'''
        CREATE OR REPLACE TABLE {agg_table_name} AS 
        FROM (
            SELECT 
                event_type,
                repo_id,
                repo_name,
                repo_url,
                DATE_TRUNC('day',CAST(event_date AS TIMESTAMP)) AS event_date,
                count(*) AS event_count
            FROM '{source_path}'
            GROUP BY ALL
        )
        '''
        self.con.execute(f"{query}")
        return self.con.table(f"{agg_table_name}")


    def __del__(self):
        """
        Close DuckDB connection when the object is destroyed
        """
        if hasattr(self, 'con'):
            self.con.close()