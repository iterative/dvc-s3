import os

import pytest

from .cloud import S3, FakeS3


@pytest.fixture
# pylint: disable-next=redefined-outer-name,unused-argument
def make_s3(request):
    def _make_s3():
        if os.environ.get("DVC_TEST_AWS_REPO_BUCKET"):
            return S3(S3.get_url())
        tmp_s3_path = request.getfixturevalue("tmp_s3_path")
        s3_server = request.getfixturevalue("s3_server")
        return FakeS3(str(tmp_s3_path).rstrip("/"), config=s3_server)

    return _make_s3


@pytest.fixture
# pylint: disable-next=redefined-outer-name,unused-argument
def make_s3_version_aware(versioning, tmp_s3_path, s3_server):
    def _make_s3():
        return FakeS3(str(tmp_s3_path).rstrip("/"), config=s3_server)

    return _make_s3


@pytest.fixture
def s3(make_s3):  # pylint: disable=redefined-outer-name
    return make_s3()


@pytest.fixture
def cloud(make_cloud):
    return make_cloud(typ="s3")


@pytest.fixture
def remote(make_remote):
    return make_remote(name="upstream", typ="s3")


@pytest.fixture
def remote_version_aware(make_remote_version_aware):
    return make_remote_version_aware(name="upstream", typ="s3")


@pytest.fixture
def remote_worktree(make_remote_worktree):
    return make_remote_worktree(name="upstream", typ="s3")


@pytest.fixture
def workspace(make_workspace):
    return make_workspace(name="workspace", typ="s3")
