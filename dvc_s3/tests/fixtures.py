import os

import pytest

from .cloud import S3, TEST_AWS_ENDPOINT_URL, TEST_AWS_REPO_BUCKET


@pytest.fixture
def s3_fake_creds_file(monkeypatch):
    # https://github.com/spulec/moto#other-caveats
    import pathlib

    aws_dir = pathlib.Path("~").expanduser() / ".aws"
    aws_dir.mkdir(exist_ok=True)

    aws_creds = aws_dir / "credentials"
    initially_exists = aws_creds.exists()

    if not initially_exists:
        aws_creds.touch()

    try:
        with monkeypatch.context() as m:
            m.setenv("AWS_ACCESS_KEY_ID", "testing")
            m.setenv("AWS_SECRET_ACCESS_KEY", "testing")
            m.setenv("AWS_SECURITY_TOKEN", "testing")
            m.setenv("AWS_SESSION_TOKEN", "testing")
            yield
    finally:
        if aws_creds.exists() and not initially_exists:
            aws_creds.unlink()


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(os.path.dirname(__file__), "docker-compose.yml")


@pytest.fixture(scope="session")
def s3_server(docker_compose, docker_services):
    import requests

    port = docker_services.port_for("motoserver", 5000)
    endpoint_url = TEST_AWS_ENDPOINT_URL.format(port=port)

    def _check():
        try:
            r = requests.get(endpoint_url)
            return r.ok
        except requests.RequestException:
            return False

    docker_services.wait_until_responsive(
        timeout=60.0, pause=0.1, check=_check
    )
    S3.TEST_AWS_ENDPOINT_URL = endpoint_url
    return endpoint_url


@pytest.fixture
def make_s3(s3_server, s3_fake_creds_file):
    def _make_s3():
        s3dir = S3(S3.get_url())
        s3dir._s3.create_bucket(  # pylint: disable=protected-access
            Bucket=TEST_AWS_REPO_BUCKET
        )
        return s3dir

    return _make_s3


@pytest.fixture
def s3(make_s3):
    return make_s3()


@pytest.fixture
def real_s3():
    yield S3(S3.get_url())
