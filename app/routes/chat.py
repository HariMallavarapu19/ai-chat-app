from fastapi import APIRouter, Depends,HTTPException
from sqlmodel import Session,select
from app.services.gemini import ask_gemini_with_history
from app.auth import get_current_user
from app.database import get_session
from app.models import Chat, User, Message
from app.schemas import (MessageCreate,
MessageResponse,CreateMessageResponse,ChatResponse,MessageResponseSimple)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post("/",
    response_model=ChatResponse,
    summary="Create a new chat",
    description="Create a new chat for the currently authenticated user."
)
def create_chat(
    title: str,
    current_user: User = Depends(get_current_user),
    session:Session=Depends(get_session)):
    new_chat = Chat(
        user_id=current_user.id,
        title=title
    )


    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)

    return {
        "id": new_chat.id,
        "title": new_chat.title,
        "user_id": new_chat.user_id,
        "created_at": new_chat.created_at
    }

@router.get('/',
    response_model=list[ChatResponse],
    summary="Get user's chats",
    description="Return all chats belonging to the currently authenticated user."
)
def get_chats(current_user:User=Depends(get_current_user),
              session:Session=Depends(get_session)):

    chats=session.exec(
        select(Chat).where(Chat.user_id==current_user.id)
    ).all()

    return chats

@router.get('/{chat_id}',
    response_model=ChatResponse,
    summary="Get a chat",
    description="Return a specific chat belonging to the currently authenticated user."
)
def get_chat(chat_id:int,
             current_user:User=Depends(get_current_user),
             session:Session=Depends(get_session)
             ):
    

    chat=session.exec(
        select(Chat).where((Chat.id==chat_id) & (Chat.user_id==current_user.id))
    ).first()

    if chat is None:
        raise HTTPException(status_code=404,detail='chat not found')
    
    return chat

@router.delete('/{chat_id}',
    response_model=MessageResponseSimple,
    summary="Delete a chat",
    description="Delete a chat and all messages belonging to it."
)
def delete_chat(chat_id:int,
                current_user:User=Depends(get_current_user),
                session:Session=Depends(get_session)):
    
    chat=session.exec(
        select(Chat).where((Chat.id==chat_id)&(Chat.user_id==current_user.id))
    ).first()

    if chat is None:
        raise HTTPException(status_code=404,detail="chat not found")

    messages = session.exec(
        select(Message).where(
            Message.chat_id == chat_id
        )
    ).all()

    for message in messages:
        session.delete(message)

    session.delete(chat)
    session.commit()

    return {
        "message":"chat deleted successfully"
    }

@router.post('/{chat_id}/messages',
    response_model=CreateMessageResponse,
    summary="Send a message",
    description="Save a user message and generate an AI response using Gemini."
)
def create_message(chat_id:int,
                   message:MessageCreate,
                   current_user:User=Depends(get_current_user),
                   session:Session=Depends(get_session)):

    chat=session.exec(
        select(Chat).where(
            (Chat.id==chat_id)&(
            Chat.user_id==current_user.id)
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
        ).order_by(Message.created_at.desc())
        .limit(20)
    ).all()

    messages.reverse()

        
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

@router.get("/{chat_id}/messages",
    response_model=list[MessageResponse],
    summary="Get chat messages",
    description="Return the messages belonging to a specific chat."
)
def get_messages(chat_id:int,
                 current_user:User=Depends(get_current_user),
                 session:Session=Depends(get_session)):

    
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

@router.delete("/{chat_id}/messages/{message_id}",
    response_model=MessageResponseSimple,
    summary="Delete a message",
    description="Delete a specific message from a chat."
)
def delete_message(
    chat_id: int,
    message_id: int,
    current_user: User = Depends(get_current_user),
    session:Session=Depends(get_session)
):
    
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







