from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from app.database import create_db_and_tables,engine
from app.routes.auth import router as auth_router

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables()
    yield

app=FastAPI(lifespan=lifespan)
app.include_router(auth_router)

@app.get('/')
def home():
    return {"message":"Ai chat app is running"}





