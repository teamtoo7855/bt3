from __future__ import annotations

from firebase import db


def get_profile_doc_ref(uid: str):
    """Get the Firestore document reference for a user's profile."""
    return db.collection("profile").document(uid)


def get_profile_data(uid: str):
    """Fetch a user's profile from Firestore, returning an empty dict if missing."""
    doc = get_profile_doc_ref(uid).get()
    return doc.to_dict() if doc.exists else {}


def set_profile(uid: str, profile_data: dict[str, str], *, merge: bool):
    """Persist profile data to Firestore."""
    get_profile_doc_ref(uid).set(profile_data, merge=merge)
