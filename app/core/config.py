from pydantic_settings import BaseSettings  
from typing import List, Optional
import os
from urllib.parse import quote_plus

class Settings(BaseSettings):
    PROJECT_NAME: str = "PDFier API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # MongoDB settings 
    MONGO_USER: str
    MONGO_PASS: str
    MONGO_CLUSTER: str
    DB_NAME: str
   

    @property
    def MONGO_URI(self):
        user = quote_plus(self.MONGO_USER)
        passwd = quote_plus(self.MONGO_PASS)
        return f"mongodb+srv://{user}:{passwd}@{self.MONGO_CLUSTER}/{self.DB_NAME}?retryWrites=true&w=majority"


    # JWT settings
    # SECRET_KEY: str  
    # ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int 
    REFRESH_TOKEN_EXPIRE_DAYS: int 
    # JWT_REFRESH_SECRET_KEY: str
    
    # CORS settings
    # BACKEND_CORS_ORIGINS: List[str] = []

    # Email settings
    EMAIL_USER: str
    EMAIL_PASS: str

    

    class Config:
        env_file = ".env"

settings = Settings()
