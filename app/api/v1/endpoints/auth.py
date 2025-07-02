from fastapi import APIRouter, Request, HTTPException, Depends,status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import SignupRequest, VerifyOtpRequest,RefreshTokenRequest,ResetVerifyRequest,ResetPasswordRequest,ResendOtpRequest
from app.core.security import hash_password,create_access_token, create_refresh_token,verify_password,decode_token
from app.utils.emails import send_verification_email
from app.database.connection import get_mongo_db
from datetime import datetime, timedelta
import random
from bson import ObjectId
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from jose import JWTError
from fastapi.responses import Response
from app.database.models import OTPModel, UserModel, UsageMetrics
from app.core.plans import get_initial_usage_metrics
security = HTTPBearer()  # login endpoint issues tokens

router = APIRouter()

@router.post("/signup", status_code=201)
async def signup(data: SignupRequest, request: Request, db = Depends(get_mongo_db)):
    # Check if user already exists
    existing_user = await db["users"].find_one({"email": data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    try:
        # Create new user
        ip_address = request.client.host
        hashed_pwd = hash_password(data.password)
        usage_metrics = UsageMetrics(**get_initial_usage_metrics("basic"))
        
        
        user = UserModel(
            name=data.username,
            email=data.email,
            password=hashed_pwd,
            verified=False,
            ip_address=ip_address,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            plan_type="basic",
            usage_metrics=usage_metrics,   
        )
        
        # Save user to database
        user_result = await db["users"].insert_one(user.dict())
        user_id = user_result.inserted_id
        
        # Generate and save OTP
        otp = str(random.randint(1000, 9999))
        otp_data = OTPModel(
            user_id=str(user_id),
            otp=otp,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        
        # Remove any existing OTP for this user
        await db["otps"].delete_many({"user_id": str(user_id)})
        await db["otps"].insert_one(otp_data.dict())
        
        # Send verification email
        send_verification_email(data.email, otp)
        
        return {
            "message": "Registration successful. Please check your email for verification code.",
            "user_id": str(user_id)
        }
        
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration. Please try again."
        )

@router.post("/verify")                                                                       #Can apply rate limiting in future
async def verify(data: VerifyOtpRequest,db = Depends(get_mongo_db)):
    user_id = data.user_id
    otp_data = await db["otps"].find_one({"user_id": user_id, "otp": data.otp})

    if not otp_data:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if otp_data["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    await db["users"].update_one({"_id": ObjectId(user_id)}, {"$set": {"verified": True}})
    await db["otps"].delete_many({"user_id": user_id})

    return {"message": "Email verified successfully.", "user_id": str(user_id)}


@router.post("/resend-otp")
async def resend_otp(data: ResendOtpRequest,db = Depends(get_mongo_db)):
    user_id = data.user_id
    otp_data = await db["otps"].find_one({"user_id": user_id})

    if not otp_data:
        raise HTTPException(status_code=400, detail="No OTP found. Please register first.")

    # Generate new OTP
    otp = str(random.randint(1000, 9999))
    otp_data = {
        "user_id": user_id,
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=10)
    }

    # Remove any existing OTP for this user
    await db["otps"].delete_many({"user_id": user_id})
    await db["otps"].insert_one(otp_data)

    # Send verification email
    send_verification_email(data.email, otp)

    return {
        "message": "OTP sent to email",
        "user_id": str(user_id)
    }


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(),db = Depends(get_mongo_db)):
    user = await db["users"].find_one({"email": form_data.username})
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    if not user["verified"]:
        raise HTTPException(status_code=403, detail="Email not verified")

    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(user["_id"])})
    refresh_token = create_refresh_token({"sub": str(user["_id"])})
    response = Response(status_code=200)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=1800, # 30 minutes
    )

    return {
        "refresh_token": refresh_token,
    }

# @router.post("/refresh")
# async def refresh_token(data: RefreshTokenRequest):
#     payload = decode_token(data.refresh_token)
#     if not payload or payload.get("type") != "refresh":
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

#     user_id = payload.get("sub")
#     user = await db.db["users"].find_one({"_id": ObjectId(user_id)})

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     # Create a new access token
#     new_access_token = create_access_token({"sub": str(user["_id"])})

#     return {
#         "access_token": new_access_token,
#         "token_type": "bearer"
#     }



@router.post("/forgot")
async def forgot_password(request: ResetVerifyRequest,db = Depends(get_mongo_db)):
    email=request.email
    user = await db["users"].find_one({"email": email})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = str(random.randint(1000, 9999))
    otp_data = OTPModel(
        user_id=str(user["_id"]),
        otp=otp,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    if await db["otps"].find_one({"user_id": str(user["_id"])}):
        await db["otps"].delete_one({"user_id": str(user["_id"])})  
    await db["otps"].insert_one(otp_data.dict())
    send_verification_email(user["email"], otp)

    return {
        "message": "OTP sent to email",
        "user_id": str(user["_id"]),
        "otp": otp
    }


@router.post("/forgot/reset-password")
async def reset_forgot(request: ResetPasswordRequest,db = Depends(get_mongo_db)):
    user_id = ObjectId(request.user_id)
    user = await db["users"].find_one({"_id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    hashed_password = hash_password(request.new_password)
    await db["users"].update_one({"_id": user_id}, {"$set": {"password": hashed_password}})
    await db["users"].update_one({"_id": user_id}, {"$set": {"password": hashed_password, "updated_at": datetime.utcnow()}})
    
    return {
        "message": "Password reset successful"
    }
