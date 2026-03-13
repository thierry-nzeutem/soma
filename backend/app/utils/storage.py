"""
Utilitaire de stockage fichiers — SOMA LOT 2.

Gère le stockage local des photos de repas.
Abstraction prévue pour migration vers stockage objet (S3, GCS) en LOT 5+.
"""
import uuid
import os
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


# Types MIME acceptés pour les photos
_ALLOWED_MIMES = {
    mime.strip()
    for mime in settings.ALLOWED_PHOTO_MIME_TYPES.split(",")
    if mime.strip()
}

# Extensions autorisées par MIME
_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
}


def _get_storage_root() -> Path:
    """Retourne le répertoire racine du stockage (crée si absent)."""
    root = Path(settings.STORAGE_PATH).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def validate_photo_file(file: UploadFile) -> None:
    """
    Valide le type MIME et la taille d'un fichier photo.
    Lève HTTPException 422 si invalide.
    """
    # Validation MIME
    content_type = file.content_type or ""
    if content_type not in _ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Type de fichier non supporté : '{content_type}'. "
                f"Types acceptés : {', '.join(sorted(_ALLOWED_MIMES))}"
            ),
        )


async def save_photo(
    file: UploadFile,
    user_id: uuid.UUID,
    subdir: str = "nutrition",
) -> dict:
    """
    Sauvegarde un fichier photo uploadé.

    Retourne un dict avec :
    - path       : chemin relatif depuis STORAGE_PATH (à stocker en DB)
    - abs_path   : chemin absolu sur le disque
    - size_bytes : taille du fichier
    - mime_type  : MIME type du fichier
    """
    validate_photo_file(file)

    content_type = file.content_type or "image/jpeg"
    ext = _MIME_TO_EXT.get(content_type, ".jpg")
    filename = f"{uuid.uuid4()}{ext}"

    # Chemin : {STORAGE_PATH}/{subdir}/{user_id}/{filename}
    dest_dir = _get_storage_root() / subdir / str(user_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    # Vérification taille pendant l'écriture (streaming)
    max_bytes = settings.MAX_FOOD_PHOTO_SIZE_MB * 1024 * 1024
    written = 0

    with dest_path.open("wb") as out_file:
        while True:
            chunk = await file.read(1024 * 64)  # 64KB chunks
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes:
                # Nettoyer le fichier partiel
                dest_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Fichier trop volumineux. "
                        f"Maximum : {settings.MAX_FOOD_PHOTO_SIZE_MB}Mo."
                    ),
                )
            out_file.write(chunk)

    # Chemin relatif depuis STORAGE_PATH
    rel_path = str(Path(subdir) / str(user_id) / filename)

    return {
        "path": rel_path,
        "abs_path": str(dest_path),
        "size_bytes": written,
        "mime_type": content_type,
    }


def delete_photo(relative_path: str) -> None:
    """Supprime un fichier photo du stockage local (best-effort, ne lève pas d'erreur)."""
    root = _get_storage_root()
    full_path = root / relative_path
    try:
        full_path.unlink(missing_ok=True)
    except Exception:
        pass  # Toujours silencieux : le fichier peut déjà avoir été supprimé


def get_photo_abs_path(relative_path: str) -> Optional[Path]:
    """Retourne le chemin absolu d'une photo, ou None si elle n'existe pas."""
    root = _get_storage_root()
    full_path = root / relative_path
    return full_path if full_path.exists() else None
