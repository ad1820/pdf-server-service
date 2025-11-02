from fastapi import Request, HTTPException
from utils.firebase_auth_utils import auth as admin_auth
from datetime import datetime, timezone

async def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        token = auth_header.split(" ")[1]
        decoded_token = admin_auth.verify_id_token(token, check_revoked=True)

        exp_time = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
        if exp_time < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Token expired")

        return decoded_token

    except admin_auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail="Token has been revoked. Please log in again.")
    except admin_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Token expired. Please log in again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
