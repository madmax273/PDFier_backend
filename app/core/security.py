from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)



def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except ExpiredSignatureError:
        # Token is expired
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        # Token is invalid
        raise HTTPException(status_code=401, detail="Invalid token")

def decode_refresh_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except ExpiredSignatureError:
        # Token is expired
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except JWTError:
        # Token is invalid
        raise HTTPException(status_code=401, detail="Invalid refresh token")

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "type": "access"  # 👈 Important for later decoding
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({
        "exp": expire,
        "type": "refresh"  # 👈 Used to distinguish token type
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


