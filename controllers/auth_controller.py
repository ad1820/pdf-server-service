from fastapi import APIRouter, HTTPException, Depends
from utils.firebase_auth_utils import pb_auth, auth as admin_auth
from database.db import users_collection
from middleware.verification_middleware import verify_token
from models.schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup")
async def signup(user: UserCreate):
    try:
        user_data = pb_auth.create_user_with_email_and_password(user.email, user.password)
        firebase_uid = user_data["localId"]

        users_collection.insert_one({
            "uid": firebase_uid,
            "email": user.email,
            "auth_provider": "email_password",
            "active_chat": False,
            "cloudinary_pdf_link": None,
            "conversations": [],
        })

        return {"message": "User created successfully", "uid": firebase_uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(user: UserCreate):
    try:
        login = pb_auth.sign_in_with_email_and_password(user.email, user.password)
        token = login["idToken"]

        decoded = admin_auth.verify_id_token(token)
        uid = decoded["uid"]
        existing = users_collection.find_one({"uid": uid})
        if not existing:
            users_collection.insert_one({
                "uid": uid,
                "email": user.email,
                "auth_provider": "email_password",
                "active_chat": False,
                "cloudinary_pdf_link": None,
                "conversations": [],
            })

        return {"message": "Login successful", "token": token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {str(e)}")


@router.post("/logout")
async def logout(user=Depends(verify_token)):
    try:
        admin_auth.revoke_refresh_tokens(user["uid"])
        return {"message": f"User {user['email']} logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
