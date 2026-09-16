from fastapi import FastAPI,HTTPException,APIRouter,Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel,Session,select
from datetime import timedelta
from app.database import engine
from app.auth import (
    hash_password,verify_password,
    create_access_token,get_current_user)
from app.models import User
from app.schemas import UserCreate


router=APIRouter(
    prefix='/auth',
    tags=['autentication']
)

@router.post("/register")
def register(user:UserCreate):
    hashed_password=hash_password(user.password)

    new_user=User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    with Session(engine) as session:
        existing_user=session.exec(
            select(User).where((User.username==user.username)|(User.email==user.email))
        ).first()

        if existing_user:
            raise HTTPException(status_code=400,detail="already registerd")

        session.add(new_user)
        session.commit()
        session.refresh(new_user)

    return {
        "message": "User created Successfully",
        "username": new_user.username,
        "email": new_user.email
    }


@router.post('/login')
def login(form_data:OAuth2PasswordRequestForm=Depends()):
    with Session(engine) as session:
        user=session.exec(
            select(User).where(User.username==form_data.username)
        ).first()

        if not user:
            raise HTTPException(status_code=401,detail="incorrect username or password")

        if not verify_password(
            form_data.password,user.hashed_password
        ):
            raise HTTPException(status_code=401,detail='incorrect username or password')

        access_token=create_access_token(
            data={"sub":str(user.id)},
            expires_delta=timedelta(minutes=30)
        )

    return {
        "access_token":access_token,
        "token_type":"bearer"
    }

@router.get("/me")
def get_me(current_user:User=Depends(get_current_user)):
    return {
        "id":current_user.id,
        "username":current_user.username,
        "email":current_user.email
    }