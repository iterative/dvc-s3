import os
import threading
from collections import defaultdict

from dvc_objects.fs.base import ObjectFileSystem
from dvc_objects.fs.errors import ConfigError
from funcy import cached_property, wrap_prop

_AWS_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".aws", "config")


# https://github.com/aws/aws-cli/blob/5aa599949f60b6af554fd5714d7161aa272716f7/awscli/customizations/s3/utils.py
MULTIPLIERS = {
    "kb": 1024,
    "mb": 1024**2,
    "gb": 1024**3,
    "tb": 1024**4,
    "kib": 1024,
    "mib": 1024**2,
    "gib": 1024**3,
    "tib": 1024**4,
}


def human_readable_to_bytes(value: str) -> int:
    value = value.lower()
    suffix = ""
    if value.endswith(tuple(MULTIPLIERS.keys())):
        size = 2
        size += value[-2] == "i"  # KiB, MiB etc
        value, suffix = value[:-size], value[-size:]

    multiplier = MULTIPLIERS.get(suffix, 1)
    return int(value) * multiplier


# pylint:disable=abstract-method
class S3FileSystem(ObjectFileSystem):
    protocol = "s3"
    REQUIRES = {"s3fs": "s3fs", "boto3": "boto3"}
    PARAM_CHECKSUM = "etag"

    _GRANTS = {
        "grant_full_control": "GrantFullControl",
        "grant_read": "GrantRead",
        "grant_read_acp": "GrantReadACP",
        "grant_write_acp": "GrantWriteACP",
    }

    _TRANSFER_CONFIG_ALIASES = {
        "max_queue_size": "max_io_queue",
        "max_concurrent_requests": "max_concurrency",
        "multipart_threshold": "multipart_threshold",
        "multipart_chunksize": "multipart_chunksize",
    }

    def _split_s3_config(self, s3_config):
        """Splits the general s3 config into 2 different config
        objects, one for transfer.TransferConfig and other is the
        general session config"""

        from boto3.s3.transfer import TransferConfig

        config, transfer_config = {}, {}
        for key, value in s3_config.items():
            if key in self._TRANSFER_CONFIG_ALIASES:
                if key in {"multipart_chunksize", "multipart_threshold"}:
                    # cast human readable sizes (like 24MiB) to integers
                    value = human_readable_to_bytes(value)
                else:
                    value = int(value)
                transfer_config[self._TRANSFER_CONFIG_ALIASES[key]] = value
            else:
                config[key] = value

        # pylint: disable=attribute-defined-outside-init
        self._transfer_config = TransferConfig(**transfer_config)
        return config

    def _load_aws_config_file(self, profile):
        from botocore.configloader import load_config

        # pylint: disable=attribute-defined-outside-init
        self._transfer_config = None
        config_path = os.environ.get("AWS_CONFIG_FILE", _AWS_CONFIG_PATH)
        if not os.path.exists(config_path):
            return {}

        config = load_config(config_path)
        profile_config = config["profiles"].get(profile or "default")
        if not profile_config:
            return {}

        s3_config = profile_config.get("s3", {})
        return self._split_s3_config(s3_config)

    def _prepare_credentials(self, **config):
        import base64

        from flatten_dict import flatten, unflatten
        from s3fs.utils import SSEParams

        login_info = defaultdict(dict)

        # credentials
        login_info["key"] = config.get("access_key_id")
        login_info["secret"] = config.get("secret_access_key")
        login_info["token"] = config.get("session_token")

        # session configuration
        login_info["profile"] = config.get("profile")
        login_info["use_ssl"] = config.get("use_ssl", True)

        # extra client configuration
        client = login_info["client_kwargs"]
        client["region_name"] = config.get("region")
        client["endpoint_url"] = config.get("endpointurl")
        client["verify"] = config.get("ssl_verify")

        # timeout configuration
        config_kwargs = login_info["config_kwargs"]
        config_kwargs["read_timeout"] = config.get("read_timeout")
        config_kwargs["connect_timeout"] = config.get("connect_timeout")

        # encryptions
        additional = login_info["s3_additional_kwargs"]
        sse_customer_key = None
        if config.get("sse_customer_key"):
            if config.get("sse_kms_key_id"):
                raise ConfigError(
                    "`sse_kms_key_id` and `sse_customer_key` AWS S3 config "
                    "options are mutually exclusive"
                )
            sse_customer_key = base64.b64decode(config.get("sse_customer_key"))
        sse_customer_algorithm = config.get("sse_customer_algorithm")
        if not sse_customer_algorithm and sse_customer_key:
            sse_customer_algorithm = "AES256"
        sse_params = SSEParams(
            server_side_encryption=config.get("sse"),
            sse_customer_algorithm=sse_customer_algorithm,
            sse_customer_key=sse_customer_key,
            sse_kms_key_id=config.get("sse_kms_key_id"),
        )
        additional.update(sse_params.to_kwargs())
        additional["ACL"] = config.get("acl")
        for grant_option, grant_key in self._GRANTS.items():
            if config.get(grant_option):
                if additional["ACL"]:
                    raise ConfigError(
                        "`acl` and `grant_*` AWS S3 config options "
                        "are mutually exclusive"
                    )
                additional[grant_key] = config[grant_option]

        # config kwargs
        session_config = login_info["config_kwargs"]
        session_config["s3"] = self._load_aws_config_file(
            login_info["profile"]
        )

        shared_creds = config.get("credentialpath")
        if shared_creds:
            os.environ.setdefault("AWS_SHARED_CREDENTIALS_FILE", shared_creds)

        if (
            client["region_name"] is None
            and session_config["s3"].get("region_name") is None
            and os.getenv("AWS_REGION") is None
        ):
            # Enable bucket region caching
            login_info["cache_regions"] = config.get("cache_regions", True)

        config_path = config.get("configpath")
        if config_path:
            os.environ.setdefault("AWS_CONFIG_FILE", config_path)

        d = flatten(login_info, reducer="dot")
        return unflatten(
            {key: value for key, value in d.items() if value is not None},
            splitter="dot",
        )

    @wrap_prop(threading.Lock())
    @cached_property
    def fs(self):
        from s3fs import S3FileSystem as _S3FileSystem

        return _S3FileSystem(**self.fs_args)

    @classmethod
    def _strip_protocol(cls, path: str) -> str:
        from fsspec.utils import infer_storage_options

        return infer_storage_options(path)["path"]

    def unstrip_protocol(self, path):
        return "s3://" + path.lstrip("/")
