from fastapi import APIRouter, Depends, HTTPException
from middleware.verification_middleware import verify_token
from database.db import users_collection

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me")
async def get_user_info(user=Depends(verify_token)):
    user_data = users_collection.find_one({"uid": user["uid"]}, {"_id": 0})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found in DB")
    return {"firebase": user, "mongo": user_data}
