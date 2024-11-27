import os
from google.oauth2 import service_account
from google.cloud import storage
import logging
import datetime


CRED_PATH = os.path.abspath(os.environ.get(
                    "CRED_PATH", "./credentials/cred.json"))

def generate_download_signed_url_v4(bucket_name, blob_name, minutes=15, thread_url=None, thread_key=None):
    """Generates a signed URL for downloading a blob.

    Note that this method requires a service account key file. You can not use
    this if you are using Application Default Credentials from Google Compute
    Engine or from the Google Cloud SDK.
    """
    try:
        if bucket_name is None :
            bucket_name = "erp_clients_indexed_documents_prod"

        credentials = service_account.Credentials.from_service_account_file(
            CRED_PATH
        )
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        url = blob.generate_signed_url(
            # This URL is valid for 15 minutes
            expiration=datetime.timedelta(minutes=minutes),
            # Allow GET requests using this URL.
            method="GET",
        )

    except Exception as e:
        logging.error(
            f"Fail to fetch signed url for {blob_name} in bucket {bucket} : {str(e)}, return 'error'")
        url = 'error'

    if thread_url is not None:
        thread_url[thread_key] = url

    return url