import boto3
import botocore.session
import datetime
import time
from CTFd.utils import get_app_config
from CTFd.utils.uploads.uploaders import S3Uploader
from botocore.client import BaseClient
from botocore.config import Config
from botocore.handlers import validate_bucket_name
from flask import redirect
from freezegun import freeze_time
from urllib.parse import urlparse


class BWSS3Uploader(S3Uploader):
    def __init__(self):
        super().__init__()
        self.bucket = get_app_config("BWS_S3_BUCKET")
        self.project = get_app_config("BWS_PROJECT")

    def _get_s3_connection(self):
        core_session = botocore.session.Session()
        core_session.unregister("before-parameter-build.s3", validate_bucket_name)

        session = boto3.Session(
            aws_access_key_id=get_app_config("BWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_app_config("BWS_SECRET_ACCESS_KEY"),
            botocore_session=core_session
        )
        return session.client(
            "s3",
            region_name=get_app_config("BWS_S3_REGION"),
            endpoint_url=get_app_config("BWS_S3_ENDPOINT_URL"),
            config=Config(parameter_validation=False)
        )

    def download(self, filename):
        # S3 URLs by default are valid for one hour.
        # We round the timestamp down to the previous hour and generate the link at that time
        current_timestamp = int(time.time())
        truncated_timestamp = current_timestamp - (current_timestamp % 3600)
        if self.s3_prefix:
            filename = self.s3_prefix + filename
        key = filename
        filename = filename.split("/").pop()

        if filename.endswith(".mp4"):
            disposition = "inline"
        else:
            disposition = "attachment; filename={}".format(filename)

        with freeze_time(datetime.datetime.utcfromtimestamp(truncated_timestamp)):
            url = self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": "{}:{}".format(self.project, self.bucket),
                    "Key": key,
                    "ResponseContentDisposition": disposition,
                    "ResponseCacheControl": "max-age=3600",
                },
                ExpiresIn=3600,
            )

        custom_domain = get_app_config("AWS_S3_CUSTOM_DOMAIN")
        if custom_domain:
            url = urlparse(url)._replace(netloc=custom_domain).geturl()

        return redirect(url)
