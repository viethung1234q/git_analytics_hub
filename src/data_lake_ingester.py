import os
import io
import requests
import configparser
import logging
import boto3
from datetime import datetime
from src.utils.utils import build_config, create_bucket
from src.utils.progress import Progress

class DataLakeIngester():
    def __init__(self, dataset_base_path):
        """
        :param dataset_base_path: prefix to use for this dataset
        """
        self.dataset_base_path = dataset_base_path
        self.config = self._load_config()


    def ingest_hourly(self, process_date: datetime, verbal=False):
        """
        Ingest data hourly from GHArchive and upload to minio
        """

        # The format of the Hourly json dump files is YYYY-MM-DD-H.json.gz
        # with Hour part without leading zero when single digit (i.e. non-padded)
        date_hour = datetime.strftime(process_date, "%Y-%m-%d-%-H")
        gh_filename = f"{date_hour}.json.gz"
        gh_url = f"http://data.gharchive.org/{gh_filename}"

        bucket_name = self.config.get('datalake', 'bronze_bucket')
        obj_name = self._create_sink_path(process_date, gh_filename, self.dataset_base_path)

        data = self._collect_data(gh_url)
        # data = self._collect_data("https://docs.python.org/3/library/io.html#binary-i-o")
        self._upload_to_minio(bucket_name, obj_name, data, verbal)


    def _upload_to_minio(self, bucket_name, obj_name, data, length=-1, verbal=False):
        # Create an Minio client using the loaded credentials.
        client = boto3.client('s3',**self._get_minio_credentials())

        # Create the bucket if it doesn't exist.
        create_bucket(client, bucket_name)

        try:
            client.upload_fileobj(data, bucket_name, obj_name, Callback=self._s3_progress_callback)
            logging.info(f"Successfully uploaded {obj_name} to {bucket_name}")
        except boto3.exceptions.S3UploadFailedError as e:
            logging.error(f"Failed to upload {obj_name} to {bucket_name}: {e}")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred uploading to S3: {e}")
            raise


    def _get_minio_credentials(self):
        credentials = build_config(
            aws_access_key_id=self.config.get('minio', 'access_key'),
            aws_secret_access_key=self.config.get('minio', 'secret_key'),
            endpoint_url=self.config.get('minio', 'endpoint'),
            conditional_items=[
                (self.config.get('minio', 'region'), "region_name", self.config.get('minio', 'region'))
            ]
        )

        return credentials


    def _collect_data(self, url):
        logging.info(f"Downloading from: {url}")

        response = requests.get(url)
        if response.status_code == 200:
            return io.BytesIO(response.content)
        else:
            logging.error(f"Something bad happened...")
            response.raise_for_status()  # raise HTTPError for non-200 status codes


    def _create_sink_path(self, process_date, filename, base_path):
        date_partition = datetime.strftime(process_date, "%Y-%m-%d")
        hour_partition = datetime.strftime(process_date, "%H")
        minio_path = f"{base_path}/{date_partition}/{hour_partition}/{filename}"

        return minio_path 


    def _load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.ini")
        config.read(config_path)

        return config


    def _s3_progress_callback(self, bytes_transferred):
        """
        Callback function to print progress of S3 upload.
        """
        logging.info(f"Transferred: {bytes_transferred} bytes to S3 bucket")
