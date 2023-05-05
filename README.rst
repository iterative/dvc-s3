dvc-s3
======

s3 plugin for dvc

Tests
-----

By default tests will be run against moto (via pytest-servers).
To run against real S3, set ``DVC_TEST_AWS_REPO_BUCKET`` with an AWS bucket name.
