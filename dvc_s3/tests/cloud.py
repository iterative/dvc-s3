import locale
import os
import uuid

from dvc.testing.cloud import Cloud
from dvc.testing.path_info import CloudURLInfo
from funcy import cached_property


class S3(Cloud, CloudURLInfo):
    @property
    def config(self):
        return {"url": self.url}

    @staticmethod
    def _get_storagepath():
        bucket = os.environ.get("DVC_TEST_AWS_REPO_BUCKET")
        assert bucket
        return bucket + "/" + "dvc_test_caches" + "/" + str(uuid.uuid4())

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


class FakeS3(S3):
    """Fake S3 client that is supposed to be using a mock server's endpoint"""

    def __init__(self, *args, endpoint_url: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.endpoint_url = endpoint_url

    def __truediv__(self, key):
        ret = super().__truediv__(key)
        ret.endpoint_url = self.endpoint_url
        return ret

    @property
    def config(self):
        return {"url": self.url, "endpointurl": self.endpoint_url}

    def get_url(self):  # pylint: disable=arguments-differ
        return str(self)
