from pwdlib import PasswordHash
import os
import jwt
from dotenv import load_dotenv
from datetime import datetime,timedelta,timezone


load_dotenv()
SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM='HS256'
ACCESS_TOKEN_EXPIRE_MINUTES=30

password_hash=PasswordHash.recommended()

def hash_password(password:str) -> str:
    return password_hash.hash(password)

def verify_password(password:str,hashed_password:str) ->bool:
    return password_hash.verify(password,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta | None=None) -> str:
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=15)

    to_encode.update({"exp":expire})

    return jwt.encode(
        to_encode,SECRET_KEY,algorithm=ALGORITHM
    )