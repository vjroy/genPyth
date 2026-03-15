"""Local filesystem storage for image storer."""

import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

# Default base dir: ~/.image-storer (or IMAGE_STORER_DIR env)
SNAPSHOTS_DIR_NAME = "snapshots"

EXT_BY_MIME = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}


def get_storage_root() -> Path:
    root = os.environ.get("IMAGE_STORER_DIR")
    if root:
        return Path(root).expanduser().resolve()
    return Path.home() / ".image-storer"


def get_snapshots_dir() -> Path:
    d = get_storage_root() / SNAPSHOTS_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_images() -> list[dict]:
    """Return list of stored images: [{ "id", "filename", "added_at" }, ...]."""
    snap = get_snapshots_dir()
    out = []
    for f in sorted(snap.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            out.append({
                "id": f.name,
                "filename": f.name,
                "added_at": int(f.stat().st_mtime),
            })
    return out


def add_image(stream: BinaryIO, content_type: str | None = None, filename: str | None = None) -> str:
    """Save image from stream; return stored filename (id)."""
    snap = get_snapshots_dir()
    ext = "png"
    if content_type and content_type.lower() in EXT_BY_MIME:
        ext = EXT_BY_MIME[content_type.lower()]
    elif filename:
        suf = Path(filename).suffix.lower().lstrip(".")
        if suf in ("png", "jpg", "jpeg", "gif", "webp"):
            ext = suf
    name = f"{uuid.uuid4().hex}.{ext}"
    path = snap / name
    with open(path, "wb") as f:
        shutil.copyfileobj(stream, f)
    return name


def add_image_from_bytes(data: bytes, content_type: str = "image/png") -> str:
    """Save image from bytes (e.g. base64 decoded); return stored filename."""
    ext = EXT_BY_MIME.get(content_type.lower(), "png")
    name = f"{uuid.uuid4().hex}.{ext}"
    path = get_snapshots_dir() / name
    path.write_bytes(data)
    return name


def remove_image(image_id: str) -> bool:
    """Delete one image by id (filename). Returns True if removed."""
    snap = get_snapshots_dir()
    path = snap / image_id
    if not path.is_file():
        return False
    path.unlink()
    return True


def clear_all() -> int:
    """Delete all stored images. Returns count removed."""
    snap = get_snapshots_dir()
    n = 0
    for f in snap.iterdir():
        if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            f.unlink()
            n += 1
    return n


def get_image_path(image_id: str) -> Path | None:
    """Return Path to image file if it exists."""
    snap = get_snapshots_dir()
    path = (snap / image_id).resolve()
    if not path.is_file() or SNAPSHOTS_DIR_NAME not in path.parts:
        return None
    return path
