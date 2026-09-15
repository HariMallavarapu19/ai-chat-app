from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Session,select
from app.database import create_db_and_tables,engine
from app.auth import hash_password
from app.models import User
from app.schemas import UserCreate





@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables()
    yield

app=FastAPI(lifespan=lifespan)

@app.get('/')
def home():
    return {"message":"Ai chat app is running"}

@app.post("/register")
def register(user:UserCreate):
    hashed_password=hash_password(user.password)

    new_user=User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    with Session(engine) as session:
        existing_user=session.exec(
            select(User).where(
                (User.username==user.username)|(User.email==user.email)
            )
        ).first()

        if existing_user:
            raise HTTPException(status_code=400,detail="already registerd")
        session.add(new_user)
        session.commit()
        session.refresh(new_user)

    return {
        "message":"User created Successfully",
        "username":new_user.username,
        "email":new_user.email
    }



