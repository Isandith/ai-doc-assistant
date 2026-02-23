from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from sqlmodel import text
import json

from app.core.auth import create_firebase_user, get_firebase_user, verify_firebase_token
from app.core.database import engine
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    display_name: str = ""


class UserResponse(BaseModel):
    uid: str
    email: str
    display_name: str
    email_verified: bool


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister):
    """
    Register a new Firebase user.
    Returns user info and tells client to authenticate with Firebase SDK.
    """
    # Create Firebase user
    firebase_user = create_firebase_user(
        email=user_data.email,
        password=user_data.password,
        display_name=user_data.display_name
    )
    
    if not firebase_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered or invalid"
        )
    
    # Also create a record in your PostgreSQL database
    with engine.connect() as conn:
        try:
            insert_query = text("""
                INSERT INTO app_records (
                    id, record_type, owner_uid, meta
                ) VALUES (
                    :id, 'user', :owner_uid, :meta
                )
                ON CONFLICT (id) DO UPDATE SET meta = :meta
                RETURNING id
            """)
            
            conn.execute(
                insert_query,
                {
                    "id": firebase_user["uid"],
                    "owner_uid": firebase_user["uid"],
                    "meta": json.dumps({
                        "email": firebase_user["email"],
                        "display_name": firebase_user["display_name"],
                        "firebase_uid": firebase_user["uid"]
                    })
                }
            )
            conn.commit()
        except Exception as e:
            print(f"Database insert error: {e}")
            # User was created in Firebase, so don't fail the request
    
    return {
        "message": "User registered successfully. Use Firebase SDK to authenticate.",
        "user": firebase_user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current logged-in user information.
    Requires valid Firebase ID token.
    """
    user = get_firebase_user(current_user["uid"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "uid": user["uid"],
        "email": user["email"],
        "display_name": user["display_name"] or "",
        "email_verified": user["email_verified"]
    }


@router.post("/verify-token")
def verify_token(token: str):
    """
    Verify a Firebase ID token.
    Returns decoded token data if valid.
    """
    user_data = verify_firebase_token(token)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "valid": True,
        "user": user_data
    }

