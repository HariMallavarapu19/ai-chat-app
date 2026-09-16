from fastapi import APIRouter, Depends,HTTPException
from sqlmodel import Session,select

from app.auth import get_current_user
from app.database import engine
from app.models import Chat, User


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/")
def create_chat(
    title: str,
    current_user: User = Depends(get_current_user)
):
    new_chat = Chat(
        user_id=current_user.id,
        title=title
    )

    with Session(engine) as session:
        session.add(new_chat)
        session.commit()
        session.refresh(new_chat)

    return {
        "id": new_chat.id,
        "title": new_chat.title,
        "user_id": new_chat.user_id
    }

@router.get('/')
def get_chats(current_user:User=Depends(get_current_user)):
    with Session(engine) as session:
        chats=session.exec(
            select(Chat).where(Chat.user_id==current_user.id)
        ).all()

    return chats

@router.get('/{chat_id}')
def get_chat(chat_id:int,current_user=Depends(get_current_user)):
    with Session(engine) as session:
        chat=session.exec(
            select(Chat).where((Chat.id==chat_id) & (Chat.user_id==current_user.id))
        ).first()

        if chat is None:
            raise HTTPException(status_code=404,detail='chat not found')
    return chat

             