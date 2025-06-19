from fastapi import APIRouter, Request, HTTPException, Depends,status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import SignupRequest, VerifyOtpRequest,RefreshTokenRequest,ResetVerifyRequest,ResetPasswordRequest
from app.utils.security import hash_password,create_access_token, create_refresh_token,verify_password,decode_token
from app.utils.email import send_verification_email
from app.db.session import db
from datetime import datetime, timedelta
import random
from bson import ObjectId
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import JWTError

security = HTTPBearer()  # login endpoint issues tokens

router = APIRouter()

@router.post("/signup")
async def signup(data: SignupRequest, request: Request):
    if data.password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    existing_user = await db.db["users"].find_one({"email": data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    ip_address = request.client.host
    hashed_pwd = hash_password(data.password)

    user = {
        "name": data.username,
        "email": data.email,
        "password": hashed_pwd,
        "verified": False,
        "ip_address": ip_address,
        "is_admin": data.is_admin
    }
    
    user_res = await db.db["users"].insert_one(user)
    otp = str(random.randint(1000, 9999))

    otp_data = {
        "user_id": user_res.inserted_id,
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    
    if await db.db["otps"].find_one({"user_id": user_res.inserted_id}):
        await db.db["otps"].delete_one({"user_id": user_res.inserted_id})
    await db.db["otps"].insert_one(otp_data)
    send_verification_email(data.email, otp)

    return {
        "message": "Signup successful. OTP sent to email.",
        "user_id": str(user_res.inserted_id),
        "otp": otp
    }

@router.post("/verify")                                                                       #Can apply rate limiting in future
async def verify(data: VerifyOtpRequest):
    user_id = ObjectId(data.user_id)
    otp_data = await db.db["otps"].find_one({"user_id": user_id, "otp": data.otp})

    if not otp_data:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if otp_data["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    await db.db["users"].update_one({"_id": user_id}, {"$set": {"verified": True}})
    await db.db["otps"].delete_many({"user_id": user_id})

    return {"message": "Email verified successfully.", "user_id": str(user_id)}


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.db["users"].find_one({"email": form_data.username})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user["verified"]:
        raise HTTPException(status_code=403, detail="Email not verified")

    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user["_id"])})
    refresh_token = create_refresh_token({"sub": str(user["_id"])})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

#     Content-Type: application/x-www-form-urlencoded

# username=example@email.com
# password=yourpassword



@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    user = await db.db["users"].find_one({"_id": ObjectId(user_id)})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create a new access token
    new_access_token = create_access_token({"sub": str(user["_id"])})

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.post("/reset/request")
async def request_reset(current_user: dict = Depends(get_current_user)):
    user = await db.db["users"].find_one({"_id": ObjectId(current_user["user_id"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(1000, 9999))
    otp_data = {
        "user_id": user["_id"],
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    if await db.db["otps"].find_one({"user_id": user["_id"]}):
        await db.db["otps"].delete_one({"user_id": user["_id"]})
    await db.db["otps"].insert_one(otp_data)
    send_verification_email(user["email"], otp)

    return {
        "message": "OTP sent to email",
        "user_id": str(user["_id"]),
        "otp": otp
    }


@router.post("/reset/verify")
async def verify_reset(request: ResetVerifyRequest,current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["user_id"])
    otp_data = await db.db["otps"].find_one({"user_id": user_id})

    if not otp_data:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if request.otp != otp_data["otp"]:
        raise HTTPException(status_code=400, detail="Wrong OTP")

    if otp_data["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    await db.db["otps"].delete_many({"user_id": user_id})

    return {
        "message": "OTP verified",
        "user_id": str(user_id)
    }


@router.post("/reset")
async def reset_password(request: ResetPasswordRequest,current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["user_id"])
    user = await db.db["users"].find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = hash_password(user["password"])
    await db.db["users"].update_one({"_id": user_id}, {"$set": {"password": hashed_password}})

    return {
        "message": "Password reset successful"
    }


@router.post("/forgot")
async def forgot_password(request: ResetVerifyRequest):
    user_id = ObjectId(request.user_id)
    user = await db.db["users"].find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(1000, 9999))
    otp_data = {
        "user_id": user_id,
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }
    if await db.db["otps"].find_one({"user_id": user_id}):
        await db.db["otps"].delete_one({"user_id": user_id})
    await db.db["otps"].insert_one(otp_data)
    send_verification_email(user["email"], otp)

    return {
        "message": "OTP sent to email",
        "user_id": str(user_id),
        "otp": otp
    }

@router.post("/forgot/verify")
async def verify_forgot(request: ResetVerifyRequest):
    user_id = ObjectId(request.user_id)
    otp_data = await db.db["otps"].find_one({"user_id": user_id})

    if not otp_data:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if request.otp != otp_data["otp"]:
        raise HTTPException(status_code=400, detail="Wrong OTP")

    if otp_data["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    await db.db["otps"].delete_many({"user_id": user_id})

    return {
        "message": "OTP verified",
        "user_id": str(user_id)
    }

@router.post("/forgot/reset")
async def reset_forgot(request: ResetPasswordRequest):
    user_id = ObjectId(request.user_id)
    user = await db.db["users"].find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = hash_password(user["password"])
    await db.db["users"].update_one({"_id": user_id}, {"$set": {"password": hashed_password}})

    return {
        "message": "Password reset successful"
    }
