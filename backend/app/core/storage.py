import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

ALLOWED_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def upload_dir() -> Path:
    directory = settings.UPLOAD_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def save_image(file: UploadFile) -> str:
    if file.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format gambar tidak didukung (jpg/png/webp).",
        )

    content = file.file.read(settings.MAX_UPLOAD_SIZE + 1)
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran gambar maksimal 2 MB.",
        )
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File kosong.",
        )

    extension = ALLOWED_EXTENSIONS.get(file.content_type or "", ".bin")
    filename = f"{uuid.uuid4().hex}{extension}"
    (upload_dir() / filename).write_bytes(content)
    return f"/uploads/{filename}"


def delete_image(url: str | None) -> None:
    if not url or not url.startswith("/uploads/"):
        return
    filename = url.rsplit("/", 1)[-1]
    file_path = upload_dir() / filename
    if file_path.exists():
        file_path.unlink()