import boto3
from config import settings

class S3Client:
    def __init__(self):
        if not all([
            settings.S3_ENDPOINT,
            settings.S3_BUCKET,
            settings.S3_ACCESS_KEY,
            settings.S3_SECRET_KEY
        ]):
            self.enabled = False
            return

        self.enabled = True
        self.bucket = settings.S3_BUCKET
        self.prefix = settings.S3_PREFIX

        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
        )

    def upload(self, local_path: str, key: str):
        if not self.enabled:
            return
        self.client.upload_file(
            local_path,
            self.bucket,
            f"{self.prefix}/{key}"
        )
