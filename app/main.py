from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from app.database import create_db_and_tables,engine
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db_and_tables()
    yield

app=FastAPI(title="AI Chat API",
    description=(
        "Backend API for an AI chat application "
        "with JWT authentication, persistent chat history, "
        "and Gemini integration."
    ),
    version="1.0.0",
    lifespan=lifespan)
app.include_router(auth_router)
app.include_router(chat_router)

@app.get('/')
def home():
    return {"message":"Ai chat app is running"}





