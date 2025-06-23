from pydantic import BaseModel, EmailStr

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
   
class ResetVerifyRequest(BaseModel):
    otp: str

class ResendOtpRequest(BaseModel):
    user_id: str

class ResetPasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_new_password: str

class VerifyOtpRequest(BaseModel):
    user_id: str
    otp: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str