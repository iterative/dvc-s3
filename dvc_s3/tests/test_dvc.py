import pytest

from dvc.testing.api_tests import (  # noqa: F401
    TestAPI,
)
from dvc.testing.remote_tests import (  # noqa: F401
    TestRemote,
    TestRemoteVersionAware,
)
from dvc.testing.workspace_tests import TestGetUrl as _TestGetUrl
from dvc.testing.workspace_tests import TestImport as _TestImport
from dvc.testing.workspace_tests import (  # noqa: F401
    TestImportURLVersionAware,
)
from dvc.testing.workspace_tests import TestLsUrl as _TestLsUrl
from dvc.testing.workspace_tests import TestToRemote as _TestToRemote


class TestImport(_TestImport):
    @pytest.fixture
    def stage_md5(self):
        return "ffe462bbb08432b7a1c3985fcf82ad3a"

    @pytest.fixture
    def is_object_storage(self):
        return True

    @pytest.fixture
    def dir_md5(self):
        return "ec602a6ba97b2dd07bd6d2cd89674a60.dir"


class TestLsUrl(_TestLsUrl):
    pass


class TestGetUrl(_TestGetUrl):
    pass


class TestToRemote(_TestToRemote):
    pass
