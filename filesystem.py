from pathlib import Path
from typing import Annotated

from pydantic import Field


def stat_file(
        path: Annotated[str, Field(description="Path to the file to stat.")]
):
    path = Path(path)
    if not path.exists():
        return {
            "error": "File does not exist"
        }

    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "mode": stat.st_mode,
        "uid": stat.st_uid,
        "gid": stat.st_gid,
    }


def send_request():
    return "filesystem", {"path": ".gitignore"}
