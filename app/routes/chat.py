from fastapi import APIRouter, Depends,HTTPException
from sqlmodel import Session,select
from app.services.gemini import ask_gemini_with_history,ask_gemini
from app.auth import get_current_user
from app.database import engine
from app.models import Chat, User, Message
from app.schemas import MessageCreate


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
def get_chat(chat_id:int,current_user:User=Depends(get_current_user)):
    with Session(engine) as session:
        chat=session.exec(
            select(Chat).where((Chat.id==chat_id) & (Chat.user_id==current_user.id))
        ).first()

        if chat is None:
            raise HTTPException(status_code=404,detail='chat not found')
    return chat

@router.delete('/{chat_id}')
def delete_chat(chat_id:int,current_user:User=Depends(get_current_user)):
    with Session(engine) as session:
        chat=session.exec(
            select(Chat).where((Chat.id==chat_id)&(Chat.user_id==current_user.id))
        ).first()

        if chat is None:
            raise HTTPException(status_code=404,detail="chat not found")

        session.delete(chat)
        session.commit()

    return {
        "message":"chat deleted successfully"
    }

@router.post('/{chat_id}/messages')
def create_message(chat_id:int,
                   message:MessageCreate,
                   current_user:User=Depends(get_current_user)):
    with Session(engine) as  session:
        chat=session.exec(
            select(Chat).where(
                (Chat.id==chat_id)&(Chat.user_id==current_user.id)
            )
        ).first()

        if chat is None:
            raise HTTPException(status_code=404,detail='chat not found')

        new_message=Message(
            chat_id=chat.id,
            role="user",
            content=message.content
        )

        session.add(new_message)
        session.commit()
        session.refresh(new_message)
    
        messages=session.exec(
            select(Message).where(
                Message.chat_id==chat_id
            ).order_by(Message.created_at)
        ).all()
        try:
            ai_response=ask_gemini_with_history(messages)
        except RuntimeError as e:
            raise HTTPException(status_code=503,detail=str(e))
       
        # ai_response=ask_gemini(message.content)

        ai_message=Message(
            chat_id=chat.id,
            role="model",
            content=ai_response
        )

        session.add(ai_message)
        session.commit()
        session.refresh(ai_message)

        result= {
            "user_message": {
                "id": new_message.id,
                "chat_id": new_message.chat_id,
                "role": new_message.role,
                "content": new_message.content,
                "created_at": new_message.created_at
            },
            "ai_message": {
                "id": ai_message.id,
                "chat_id": ai_message.chat_id,
                "role": ai_message.role,
                "content": ai_message.content,
                "created_at": ai_message.created_at
            }
        }
        return result

@router.get("/{chat_id}/messages")
def get_messages(chat_id:int,
                 current_user:User=Depends(get_current_user)):

    with Session(engine) as session:
        chat=session.exec(
           select(Chat).where( 
               (Chat.id==chat_id)&(Chat.user_id==current_user.id)
           )
        ).first()

        if chat is None:
            raise HTTPException(
                status_code=404,detail="chat not found"
            )

        messages=session.exec(
            select(Message).where(
                Message.chat_id==chat_id
            )
        ).all()

    return messages

@router.delete("/{chat_id}/messages/{message_id}")
def delete_message(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user)
):
    with Session(engine) as session:
        chat = session.exec(
            select(Chat).where(
                (Chat.id == chat_id) &
                (Chat.user_id == current_user.id)
            )
        ).first()

        if chat is None:
            raise HTTPException(
                status_code=404,
                detail="Chat not found"
            )

        message = session.exec(
            select(Message).where(
                (Message.id == message_id) &
                (Message.chat_id == chat_id)
            )
        ).first()

        if message is None:
            raise HTTPException(
                status_code=404,
                detail="Message not found"
            )

        session.delete(message)
        session.commit()

    return {
        "message": "Message deleted successfully"
    }





