import pytest

from .cloud import S3, FakeS3


@pytest.fixture
# pylint: disable-next=redefined-outer-name,unused-argument
def make_s3(tmp_s3_path, s3_server, request):
    def _make_s3():
        return FakeS3(str(tmp_s3_path).rstrip("/"), endpoint_url=s3_server)

    return _make_s3


@pytest.fixture
# pylint: disable-next=redefined-outer-name,unused-argument
def make_s3_version_aware(versioning, tmp_s3_path, s3_server):
    def _make_s3():
        return FakeS3(str(tmp_s3_path).rstrip("/"), endpoint_url=s3_server)

    return _make_s3


@pytest.fixture
def s3(make_s3):  # pylint: disable=redefined-outer-name
    yield make_s3()


@pytest.fixture
def real_s3():
    yield S3(S3.get_url())
