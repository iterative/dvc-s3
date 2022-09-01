from typing import Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from dvc_objects.fs.base import AnyFSPath
from dvc_objects.fs.path import Path
from funcy import first


class S3Path(Path):
    VERSION_ID_KEY = "versionId"

    def split_version(self, path: AnyFSPath) -> Tuple[str, Optional[str]]:
        parts = list(urlsplit(path))
        query = parse_qs(parts[3])
        if self.VERSION_ID_KEY in query:
            version_id = first(query[self.VERSION_ID_KEY])
            del query[self.VERSION_ID_KEY]
            parts[3] = urlencode(query)
        else:
            version_id = None
        return urlunsplit(parts), version_id

    def join_version(self, path: AnyFSPath, version_id: Optional[str]) -> str:
        parts = list(urlsplit(path))
        query = parse_qs(parts[3])
        if self.VERSION_ID_KEY in query:
            raise ValueError("path already includes a version query")
        parts[3] = f"versionid={version_id}" if version_id else ""
        return urlunsplit(parts)

    def version_path(self, path: AnyFSPath, version_id: Optional[str]) -> str:
        path, _ = self.split_version(path)
        return self.join_version(path, version_id)

    def coalesce_version(
        self, path: AnyFSPath, version_id: Optional[str]
    ) -> Tuple[AnyFSPath, Optional[str]]:
        path, path_version_id = self.split_version(path)
        versions = {ver for ver in (version_id, path_version_id) if ver}
        if len(versions) > 1:
            raise ValueError("Path version mismatch: '{path}', '{version_id}'")
        return path, (versions.pop() if versions else None)
