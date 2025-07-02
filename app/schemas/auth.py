from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
   
class ResetVerifyRequest(BaseModel):
    email: EmailStr

class ResendOtpRequest(BaseModel):
    user_id: str
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    user_id: str
    new_password: str
    

class VerifyOtpRequest(BaseModel):
    user_id: str
    otp: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

   