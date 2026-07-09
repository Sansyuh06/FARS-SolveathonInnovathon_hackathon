"""Shared Firebase initialization for legacy FARS scripts."""
from __future__ import annotations


from pathlib import Path

FARS_DIR = Path(__file__).resolve().parent
KEY_FILE = FARS_DIR / "ServiceAccountKey.json"
DATABASE_URL = "https://fars-81b18-default-rtdb.firebaseio.com/"
STORAGE_BUCKET = "fars-81b18.appspot.com"

_app = None


def get_credentials_path() -> Path:
    """Return path to service account JSON (handles Windows case differences)."""
    if KEY_FILE.exists():
        return KEY_FILE
    alt = FARS_DIR / "serviceAccountKey.json"
    if alt.exists():
        return alt
    raise FileNotFoundError(
        f"Firebase key not found. Expected {KEY_FILE} in the FARS folder."
    )


def init_firebase(storage: bool = False):
    """Initialize Firebase once; returns (db, storage_bucket_or_none)."""
    global _app
    import firebase_admin
    from firebase_admin import credentials, db, storage

    if _app is None:
        cred_path = str(get_credentials_path())
        opts = {"databaseURL": DATABASE_URL}
        if storage:
            opts["storageBucket"] = STORAGE_BUCKET
        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred, opts)

    bucket = storage.bucket() if storage else None
    return db, bucket
