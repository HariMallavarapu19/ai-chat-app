from pwdlib import PasswordHash
from fastapi import Depends,HTTPException,status
from fastapi.security import OAuth2PasswordBearer
import os
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv
from datetime import datetime,timedelta,timezone
from sqlmodel import Session,select
from app.database import engine
from app.models import User


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

oauth2_schema=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_id(token:str=Depends(oauth2_schema)) -> int:
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate credentails",
        headers={"WWW-Authenticate":"Bearer"}
    )

    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        user_id=payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return int(user_id)

    except (InvalidTokenError,ValueError):
        raise credentials_exception


def get_current_user(
        user_id:int=Depends(get_current_user_id)):

    with Session(engine) as session:
        user=session.exec(
            select(User).where(User.id==user_id)
        ).first()

        if  user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate":"Bearer"}
            )
    return user