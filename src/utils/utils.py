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
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
        logging.info(f"Created bucket {bucket_name}")
    else:
        logging.info(f"Bucket {bucket_name} already exists, start uploading data ...")