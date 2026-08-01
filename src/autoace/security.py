"""Safe archive extraction and temporary workspace helpers."""

from __future__ import annotations

import io
import pathlib
import stat
import zipfile


def _safe_root_name(name: str) -> str:
    path = pathlib.PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe archive path: {name}")
    if len(path.parts) != 1 or path.name in ("", "."):
        raise ValueError(f"archive files must be at root: {name}")
    if path.name != name or "\\" in name:
        raise ValueError(f"unsafe archive path: {name}")
    return path.name


def safe_extract_zip(
    source: io.BytesIO | pathlib.Path | str,
    destination: pathlib.Path,
    *,
    max_files: int = 1000,
    max_uncompressed_bytes: int = 2 * 1024 * 1024 * 1024,
) -> list[pathlib.Path]:
    """Extract only regular root-level files within bounded limits."""

    destination.mkdir(parents=True, exist_ok=True)
    paths: list[pathlib.Path] = []
    total = 0
    with zipfile.ZipFile(source) as archive:
        members = [member for member in archive.infolist() if not member.is_dir()]
        if len(members) > max_files:
            raise ValueError("archive contains too many files")
        for member in members:
            name = _safe_root_name(member.filename)
            mode = (member.external_attr >> 16) & 0o777777
            if stat.S_ISLNK(mode):
                raise ValueError(f"unsafe symlink archive entry: {name}")
            total += member.file_size
            if total > max_uncompressed_bytes:
                raise ValueError("archive exceeds uncompressed size limit")
            target = destination / name
            if target.exists():
                raise ValueError(f"duplicate archive filename: {name}")
            with archive.open(member, "r") as input_handle, target.open("xb") as output:
                while chunk := input_handle.read(1024 * 1024):
                    output.write(chunk)
            paths.append(target)
    return paths
