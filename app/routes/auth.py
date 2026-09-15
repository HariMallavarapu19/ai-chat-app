from fastapi import FastAPI,HTTPException,APIRouter
from sqlmodel import SQLModel,Session,select

from app.database import engine
from app.auth import hash_password
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
        emami=user.email,
        hashed_password=hash_password
    )

    with Session as session:
        existing_user=session.exec(
            select(User).where(User.username==user.username|User.email==user.email)
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