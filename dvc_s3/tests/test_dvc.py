import pytest
from dvc.testing.api_tests import (  # noqa, pylint: disable=unused-import
    TestAPI,
)
from dvc.testing.remote_tests import (  # noqa, pylint: disable=unused-import
    TestRemote,
)
from dvc.testing.workspace_tests import TestAdd as _TestAdd
from dvc.testing.workspace_tests import TestImport as _TestImport
from dvc.testing.workspace_tests import TestLsUrl as _TestLsUrl


@pytest.fixture
def cloud(make_cloud):
    yield make_cloud(typ="s3")


@pytest.fixture
def remote(make_remote):
    yield make_remote(name="upstream", typ="s3")


@pytest.fixture
def workspace(make_workspace):
    yield make_workspace(name="workspace", typ="s3")


class TestImport(_TestImport):
    @pytest.fixture
    def stage_md5(self):
        return "2aa17f8daa26996b3f7a4cf8888ac9ac"

    @pytest.fixture
    def is_object_storage(self):
        return True

    @pytest.fixture
    def dir_md5(self):
        return "ec602a6ba97b2dd07bd6d2cd89674a60.dir"


class TestAdd(_TestAdd):
    @pytest.fixture
    def hash_name(self):
        return "etag"

    @pytest.fixture
    def hash_value(self):
        return "8c7dd922ad47494fc02c388e12c00eac"

    @pytest.fixture
    def dir_hash_value(self):
        return "ec602a6ba97b2dd07bd6d2cd89674a60.dir"


class TestLsUrl(_TestLsUrl):
    pass
