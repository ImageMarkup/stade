from botocore.config import Config
from storages.backends.s3boto3 import S3Boto3Storage


class TimeoutS3Boto3Storage(S3Boto3Storage):
    """Override boto3 default timeout values."""

    config = Config(connect_timeout=3, read_timeout=10, retries={'max_attempts': 5})
