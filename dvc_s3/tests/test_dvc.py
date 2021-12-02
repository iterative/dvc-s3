import pytest
from dvc.testing.test_api import TestAPI  # noqa, pylint: disable=unused-import
from dvc.testing.test_remote import (  # noqa, pylint: disable=unused-import
    TestRemote,
)
from dvc.testing.test_workspace import (  # noqa, pylint: disable=unused-import
    TestAdd,
    TestImport,
)


@pytest.fixture
def remote(make_remote):
    yield make_remote(name="upstream", typ="s3")


@pytest.fixture
def workspace(make_workspace):
    yield make_workspace(name="workspace", typ="s3")


@pytest.fixture
def stage_md5():
    return "2aa17f8daa26996b3f7a4cf8888ac9ac"


@pytest.fixture
def is_object_storage():
    return True


@pytest.fixture
def dir_md5():
    return "ec602a6ba97b2dd07bd6d2cd89674a60.dir"


@pytest.fixture
def hash_name():
    return "etag"


@pytest.fixture
def hash_value():
    return "8c7dd922ad47494fc02c388e12c00eac"


@pytest.fixture
def dir_hash_value(dir_md5):
    return dir_md5
