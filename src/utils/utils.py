import logging

def build_config(conditional_items=None, **base_items):
    """
    Constructs a configuration dictionary with base key-value pairs and optional conditional items.

    :param conditional_items:
        [Optional] A list of (condition, key, value) tuples:
        - condition (bool): Determines if the key-value pair is added.
        - key (str): The key to add if the condition is True.
        - value: The value associated with the key.

    :param base_items: 
        Key-value pairs to include in the dictionary by default.

    :return: dict
        The resulting configuration dictionary with all base and conditional items.
    """
    # Initialize dictionary with base items
    config = base_items.copy()

    # Add conditional items if applicable
    if conditional_items:
        for condition, key, value in conditional_items:
            if condition:
                config[key] = value

    return config


def create_bucket(client, bucket_name):
    """
    Create bucket if it not exist

    :param client: 
        Minio client


    :param bucket_name: 
        Name of bucket to check and create if not exist
    """
    try:
        # List all existing buckets
        existing_buckets = client.list_buckets()
        bucket_names = [bucket['Name'] for bucket in existing_buckets['Buckets']]

        # Check if the bucket exists
        if bucket_name in bucket_names:
            logging.info(f"Bucket '{bucket_name}' already exists! Start uploading data...")
        else:
            client.create_bucket(Bucket=bucket_name)
            logging.info(f"Bucket '{bucket_name}' created successfully.")

    except Exception as e:
        logging.error(f"Error: {e}")
