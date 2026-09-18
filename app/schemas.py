from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username:str
    email:str
    password:str

class MessageCreate(BaseModel):
    content:str

class MessageResponse(BaseModel):
    id:int
    chat_id:int
    role:str
    content:str
    created_at:datetime

class CreateMessageResponse(BaseModel):
    user_message:MessageResponse
    ai_message:MessageResponse


class UserResponse(BaseModel):
    id:int
    username:str
    email:str

class ChatResponse(BaseModel):
    id:int
    user_id:int
    title:str
    created_at:datetime

class MessageResponseSimple(BaseModel):
    message:str







