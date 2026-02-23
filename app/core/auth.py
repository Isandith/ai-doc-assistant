import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional
from app.core.config import FIREBASE_CREDENTIALS_PATH, FIREBASE_PROJECT_ID, DEBUG_MODE

# Initialize Firebase Admin SDK (skip in DEBUG_MODE)
if not DEBUG_MODE:
    try:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'projectId': FIREBASE_PROJECT_ID
        })
    except Exception as e:
        print(f"Warning: Firebase initialization failed. Ensure FIREBASE_CREDENTIALS_PATH is set correctly. Error: {e}")
else:
    print("DEBUG_MODE enabled - Firebase initialization skipped")


def verify_firebase_token(token: str) -> Optional[dict]:
    """
    Verify Firebase ID token and return decoded token
    
    Returns:
        dict with uid and email, or None if invalid
    """
    if DEBUG_MODE:
        # In debug mode, skip verification
        return None
    
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "email_verified": decoded_token.get("email_verified"),
            "name": decoded_token.get("name")
        }
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def create_firebase_user(email: str, password: str, display_name: str = "") -> Optional[dict]:
    """
    Create a new Firebase user
    
    Returns:
        dict with uid and email, or None if creation failed
    """
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name
        }
    except auth.EmailAlreadyExistsError:
        return None  # User exists
    except Exception as e:
        print(f"User creation failed: {e}")
        return None


def get_firebase_user(uid: str) -> Optional[dict]:
    """Get Firebase user by UID"""
    try:
        user = auth.get_user(uid)
        return {
            "uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "email_verified": user.email_verified
        }
    except Exception as e:
        print(f"Get user failed: {e}")
        return None

