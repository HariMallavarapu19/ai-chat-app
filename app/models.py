from sqlmodel import SQLModel,Field
from datetime import datetime,timezone


class User(SQLModel,table=True):
    id:int | None=Field(default=None,primary_key=True)
    username:str=Field(unique=True)
    email:str=Field(unique=True)
    hashed_password:str

class Chat(SQLModel,table=True):
    id:int | None=Field(default=None,primary_key=True)
    user_id:int=Field(foreign_key="user.id")
    title:str
    created_at:datetime=Field(
        default_factory=lambda: datetime.now(timezone.utc))

class Message(SQLModel,table=True):
    id:int | None=Field(default=None,primary_key=True)
    chat_id:int=Field(foreign_key="chat.id")
    role:str
    content:str
    created_at:datetime=Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
