from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.auth import verify_firebase_token
from app.core.config import DEBUG_MODE

security = HTTPBearer(auto_error=False)  # Don't require token, we'll handle in function

print(f"[Dependencies] DEBUG_MODE: {DEBUG_MODE}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to extract and validate Firebase ID token.
    Returns the decoded Firebase token containing user info (uid, email, etc.)
    
    In DEBUG_MODE, skips authentication entirely.
    """
    # Development mode - skip all authentication
    if DEBUG_MODE:
        return {
            "uid": "debug-user-123",
            "email": "debug@example.com"
        }  # Mock user for testing
    
    # Production mode - verify Firebase token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    user_data = verify_firebase_token(token)
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data
