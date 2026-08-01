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


def _is_macos_metadata(name: str) -> bool:
    """Return whether a ZIP member is Finder metadata rather than user content."""
    path = pathlib.PurePosixPath(name)
    return "__MACOSX" in path.parts or path.name in {".DS_Store"} or path.name.startswith("._")


def _safe_member_parts(name: str) -> tuple[str, ...]:
    path = pathlib.PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError(f"unsafe archive path: {name}")
    if not path.parts or path.name in ("", "."):
        raise ValueError(f"unsafe archive path: {name}")
    return path.parts


def safe_extract_zip(
    source: io.BytesIO | pathlib.Path | str,
    destination: pathlib.Path,
    *,
    max_files: int = 1000,
    max_uncompressed_bytes: int = 2 * 1024 * 1024 * 1024,
    allow_single_root_directory: bool = False,
) -> list[pathlib.Path]:
    """Extract regular ZIP files within bounded limits.

    By default files must be at the ZIP root. Dashboard uploads may opt into a
    single enclosing directory, which is a common result of creating a ZIP in
    Finder or Explorer.
    """

    destination.mkdir(parents=True, exist_ok=True)
    paths: list[pathlib.Path] = []
    total = 0
    with zipfile.ZipFile(source) as archive:
        members = [
            member
            for member in archive.infolist()
            if not member.is_dir() and not _is_macos_metadata(member.filename)
        ]
        if len(members) > max_files:
            raise ValueError("archive contains too many files")
        member_parts = [_safe_member_parts(member.filename) for member in members]
        root_directory: str | None = None
        if allow_single_root_directory and member_parts and all(
            len(parts) == 2 for parts in member_parts
        ):
            candidate = member_parts[0][0]
            if all(parts[0] == candidate for parts in member_parts):
                root_directory = candidate
        for member in members:
            parts = _safe_member_parts(member.filename)
            if root_directory:
                name = parts[1]
            else:
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
