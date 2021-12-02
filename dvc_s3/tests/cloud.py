import locale
import os
import uuid

from dvc.testing.cloud import Cloud
from dvc.testing.path_info import CloudURLInfo
from funcy import cached_property

TEST_AWS_REPO_BUCKET = os.environ.get("DVC_TEST_AWS_REPO_BUCKET", "dvc-temp")
TEST_AWS_ENDPOINT_URL = "http://127.0.0.1:{port}/"


class S3(Cloud, CloudURLInfo):

    TEST_AWS_ENDPOINT_URL = None

    @property
    def config(self):
        return {"url": self.url, "endpointurl": self.TEST_AWS_ENDPOINT_URL}

    @staticmethod
    def _get_storagepath():
        return (
            TEST_AWS_REPO_BUCKET
            + "/"
            + "dvc_test_caches"
            + "/"
            + str(uuid.uuid4())
        )

    @staticmethod
    def get_url():
        return "s3://" + S3._get_storagepath()

    @cached_property
    def _s3(self):
        import boto3

        return boto3.client("s3", endpoint_url=self.config["endpointurl"])

    def is_file(self):
        from botocore.exceptions import ClientError

        if self.path.endswith("/"):
            return False

        try:
            self._s3.head_object(Bucket=self.bucket, Key=self.path)
        except ClientError as exc:
            if exc.response["Error"]["Code"] != "404":
                raise
            return False

        return True

    def is_dir(self):
        path = (self / "").path
        resp = self._s3.list_objects(Bucket=self.bucket, Prefix=path)
        return bool(resp.get("Contents"))

    def exists(self):
        return self.is_file() or self.is_dir()

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        assert mode == 0o777
        assert parents

    def write_bytes(self, contents):
        self._s3.put_object(Bucket=self.bucket, Key=self.path, Body=contents)

    def read_bytes(self):
        data = self._s3.get_object(Bucket=self.bucket, Key=self.path)
        return data["Body"].read()

    def read_text(self, encoding=None, errors=None):
        if not encoding:
            encoding = locale.getpreferredencoding(False)
        assert errors is None
        return self.read_bytes().decode(encoding)

    @property
    def fs_path(self):
        return self.bucket + "/" + self.path.lstrip("/")
