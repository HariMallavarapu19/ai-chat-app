import pytest
import uuid

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session
from app.database import Message


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)


def override_get_session():
    with Session(test_engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session

SQLModel.metadata.create_all(test_engine)

client = TestClient(app)

@pytest.fixture
def auth_headers():

    unique_id=uuid.uuid4().hex
    username=f"fixtureuser_{unique_id}"
    email=f"{unique_id}@example.com"
    
    client.post(
        "/auth/register",
        json={
            "username":'username',
            'email':"email",
            'password':'password123'
        }
    )

    login_response=client.post(
        '/auth/login',
        data={
            'username':'username',
            'password':'password123'
        }
    )
    token=login_response.json()['access_token']

    return {
        "Authorization":f"Bearer {token}"
    }

@pytest.fixture
def mock_gemini(monkeypatch):
    def fake_gemini(messages):

        return "This is a fake Ai response"

    monkeypatch.setattr(
        "app.routes.chat.ask_gemini_with_history",fake_gemini
    )

def test_home():
    response=client.get("/")

    assert response.status_code==200
    assert response.json()=={
        "message":"Ai chat app is running"
    }

def test_register():
    response=client.post(
        "/auth/register",
        json={"username":"testuser",
              "email":"test@example.com",
              "password":'passwowrd123'}
    )

    assert response.status_code==200

    data=response.json()

    assert data['username']=='testuser'
    assert data['email']=='test@example.com'


def test_login():
    register_response=client.post(
        "/auth/register",
        json={
            "username":"loginuser",
            "email":'login@example.com',
            "password":"password123"
        }
    )

    assert register_response.status_code==200

    response=client.post(
        "/auth/login",
        data={
            "username":"loginuser",
            "password":"password123"
        }
    )

    assert response.status_code==200

    data=response.json()
    assert "access_token" in data
    assert data['token_type']=="bearer"


def test_login_wrong_password():
    register_response = client.post(
        "/auth/register",
        json={
            "username": "wrongpassuser",
            "email": "wrongpass@example.com",
            "password": "password123"
        }
    )

    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        data={
            "username": "wrongpassuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "incorrect username or password"


def test_get_me():
    register_response=client.post(
        "/auth/register",
        json={
            "username":'meuser',
            'email':"me@example.com",
            'password':"password123"
        }
    )

    assert register_response.status_code==200

    login_response=client.post(
        "/auth/login",
        data={
           "username":"meuser",
           "password":"password123"
        }
    )

    assert login_response.status_code==200

    token=login_response.json()['access_token']


    response=client.get(
        "/auth/me",
        headers={
            "Authorization":f"Bearer {token}"
        }
    )

    assert response.status_code==200

    data=response.json()

    assert data["username"]=="meuser"
    assert data['email']=="me@example.com"


def test_getme_without_token():
    response=client.get("/auth/me")

    assert response.status_code==401


def test_create_chat(auth_headers):
    response=client.post(
        '/chat/',
        params={
            "title":"My first test chat"
        },
        headers=auth_headers
    )

    assert response.status_code==200

    data=response.json()

    assert data['title']=="My first test chat"
    assert data['user_id'] is not None
    assert data['id'] is not None


def test_get_chats(auth_headers):
    create_response=client.post(
        '/chat',
        params={
            'title':'Chat One',
        },
        headers=auth_headers
    )

    assert create_response.status_code==200

    response=client.get(
        '/chat/',
        headers=auth_headers
    )

    assert response.status_code==200

    data=response.json()

    assert len(data)>=1

    titles=[chat['title'] for chat in data]

    assert "Chat One" in titles


def test_get_chat(auth_headers):
    create_response=client.post(
        '/chat/',
        params={
            'title':"specific chat"
        },
        headers=auth_headers
    )

    assert create_response.status_code==200
    chat_id=create_response.json()['id']
    response=client.get(
        f"chat/{chat_id}",
        headers=auth_headers
    )

    assert response.status_code==200

    data=response.json()

    assert data['id']==chat_id
    assert data['title']=="specific chat"


def test_delete_chat(auth_headers):
    create_response = client.post(
        "/chat/",
        params={
            "title": "Chat To Delete"
        },
        headers=auth_headers
    )

    assert create_response.status_code == 200

    chat_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/chat/{chat_id}",
        headers=auth_headers
    )

    assert delete_response.status_code == 200

    data = delete_response.json()

    assert data["message"] == "chat deleted successfully"


def test_get_messages(auth_headers):
    create_response=client.post(
        '/chat/',
        params={
            "title":'message test chat'
        },
        headers=auth_headers
    )

    assert create_response.status_code==200

    chat_id=create_response.json()['id']

    response=client.get(
        f"/chat/{chat_id}/messages",
        headers=auth_headers
    )

    assert response.status_code==200

    data=response.json()
    assert isinstance(data,list)
    assert len(data)==0

def test_create_message(auth_headers,mock_gemini):
    

    create_response=client.post(
        '/chat/',
        params={
            'title':'gemini test chat'
        },
        headers=auth_headers
    )

    assert create_response.status_code==200

    chat_id=create_response.json()['id']

    response=client.post(
        f'/chat/{chat_id}/messages',
        json={
            'content':'hello'
        },
        headers=auth_headers
    )

    assert response.status_code==200
    data=response.json()

    assert "user_message" in data
    assert 'ai_message' in data

    assert data['user_message']['content']=='hello'
    assert data['user_message']['role']=='user'

    assert data['ai_message']['role']=='model'
    assert data['ai_message']['content']=='This is a fake Ai response'


def test_get_messages_after_create(auth_headers,mock_gemini):

   
    create_response=client.post(
        "/chat/",
        params={
            "title":"History Test Chat"
        },
        headers=auth_headers
    )

    assert create_response.status_code==200
    chat_id=create_response.json()['id']
    message_response=client.post(
        f'/chat/{chat_id}/messages',
        json={
            'content':'hello history'
        },
        headers=auth_headers
    )

    assert message_response.status_code==200

    response=client.get(
        f"/chat/{chat_id}/messages",
        headers=auth_headers
    )

    assert response.status_code==200
    data=response.json()
    assert len(data)==2

    assert data[0]['role']=='user'
    assert data[0]['content']=='hello history'

    assert data[1]['role']=='model'
    assert data[1]['content']=='This is a fake Ai response'

def test_delete_message(auth_headers,mock_gemini):
    
    create_response=client.post(
        '/chat',
        params={
            'title':'delete message chat'
        },
        headers=auth_headers
    )

    assert create_response.status_code==200

    chat_id=create_response.json()['id']

    message_response=client.post(
        f'/chat/{chat_id}/messages',
        json={
            'content':'message to delete'
        },
        headers=auth_headers
    )

    assert message_response.status_code==200

    message_id=message_response.json()['user_message']['id']

    delete_response=client.delete(
        f'/chat/{chat_id}/messages/{message_id}',
        headers=auth_headers
    )

    assert delete_response.status_code==200
    data=delete_response.json()

    assert data['message']=="Message deleted successfully"


def test_user_cannot_access_other_users_chat():
    user_a={
        "username":'user_a',
        'email':'user_a@example.com',
        'password':'password123'
    }

    user_b = {
        "username": "user_b",
        "email": "user_b@example.com",
        "password": "password123"
    }

    register_a=client.post(
        '/auth/register',
        json=user_a
    )

    assert register_a.status_code==200

    login_a = client.post(
        "/auth/login",
        data={
            "username": user_a["username"],
            "password": user_a["password"]
        }
    )

    assert login_a.status_code == 200

    token_a = login_a.json()["access_token"]

    headers_a = {
        "Authorization": f"Bearer {token_a}"
    }

    create_chat = client.post(
        "/chat/",
        params={
            "title": "User A Private Chat"
        },
        headers=headers_a
    )

    assert create_chat.status_code == 200

    chat_id = create_chat.json()["id"]

    register_b = client.post(
        "/auth/register",
        json=user_b
    )

    assert register_b.status_code == 200

    login_b = client.post(
        "/auth/login",
        data={
            "username": user_b["username"],
            "password": user_b["password"]
        }
    )

    assert login_b.status_code == 200

    token_b = login_b.json()["access_token"]

    headers_b = {
        "Authorization": f"Bearer {token_b}"
    }

    response = client.get(
        f"/chat/{chat_id}",
        headers=headers_b
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat not found"


def test_user_cannot_access_other_users_messages(mock_gemini):
    user_a = {
        "username": "message_user_a",
        "email": "message_user_a@example.com",
        "password": "password123"
    }

    user_b = {
        "username": "message_user_b",
        "email": "message_user_b@example.com",
        "password": "password123"
    }

    # Register User A
    register_a = client.post(
        "/auth/register",
        json=user_a
    )

    assert register_a.status_code == 200

    # Login User A
    login_a = client.post(
        "/auth/login",
        data={
            "username": user_a["username"],
            "password": user_a["password"]
        }
    )

    assert login_a.status_code == 200

    token_a = login_a.json()["access_token"]

    headers_a = {
        "Authorization": f"Bearer {token_a}"
    }

    # User A creates a chat
    create_chat = client.post(
        "/chat/",
        params={
            "title": "User A Message Chat"
        },
        headers=headers_a
    )

    assert create_chat.status_code == 200

    chat_id = create_chat.json()["id"]

    # User A creates a message
    message_response = client.post(
        f"/chat/{chat_id}/messages",
        json={
            "content": "Private message"
        },
        headers=headers_a
    )

    assert message_response.status_code == 200

    # Register User B
    register_b = client.post(
        "/auth/register",
        json=user_b
    )

    assert register_b.status_code == 200

    # Login User B
    login_b = client.post(
        "/auth/login",
        data={
            "username": user_b["username"],
            "password": user_b["password"]
        }
    )

    assert login_b.status_code == 200

    token_b = login_b.json()["access_token"]

    headers_b = {
        "Authorization": f"Bearer {token_b}"
    }

    # User B tries to access User A's messages
    response = client.get(
        f"/chat/{chat_id}/messages",
        headers=headers_b
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat not found"


def test_user_cannot_delete_other_users_chat():
    user_a = {
        "username": "delete_user_a",
        "email": "delete_user_a@example.com",
        "password": "password123"
    }

    user_b = {
        "username": "delete_user_b",
        "email": "delete_user_b@example.com",
        "password": "password123"
    }

    # Register User A
    register_a = client.post(
        "/auth/register",
        json=user_a
    )

    assert register_a.status_code == 200

    # Login User A
    login_a = client.post(
        "/auth/login",
        data={
            "username": user_a["username"],
            "password": user_a["password"]
        }
    )

    assert login_a.status_code == 200

    token_a = login_a.json()["access_token"]

    headers_a = {
        "Authorization": f"Bearer {token_a}"
    }

    # User A creates a chat
    create_chat = client.post(
        "/chat/",
        params={
            "title": "Private Chat"
        },
        headers=headers_a
    )

    assert create_chat.status_code == 200

    chat_id = create_chat.json()["id"]

    # Register User B
    register_b = client.post(
        "/auth/register",
        json=user_b
    )

    assert register_b.status_code == 200

    # Login User B
    login_b = client.post(
        "/auth/login",
        data={
            "username": user_b["username"],
            "password": user_b["password"]
        }
    )

    assert login_b.status_code == 200

    token_b = login_b.json()["access_token"]

    headers_b = {
        "Authorization": f"Bearer {token_b}"
    }

    # User B tries to delete User A's chat
    response = client.delete(
        f"/chat/{chat_id}",
        headers=headers_b
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat not found"

def test_get_nonexistent_chat(auth_headers):
    response = client.get(
        "/chat/999999",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "chat not found"


def test_duplicate_registration():
    user = {
        "username": "duplicate_user",
        "email": "duplicate@example.com",
        "password": "password123"
    }

    first_response = client.post(
        "/auth/register",
        json=user
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/auth/register",
        json=user
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "already registerd"

def test_invalid_token():
    headers = {
        "Authorization": "Bearer this-is-not-a-valid-jwt"
    }

    response = client.get(
        "/auth/me",
        headers=headers
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "could not validate credentials"

def test_delete_nonexistent_message(auth_headers):
    create_response = client.post(
        "/chat/",
        params={
            "title": "Nonexistent Message Test"
        },
        headers=auth_headers
    )

    assert create_response.status_code == 200

    chat_id = create_response.json()["id"]

    response = client.delete(
        f"/chat/{chat_id}/messages/999999",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"

def test_gemini_failure(mock_gemini, auth_headers, monkeypatch):
    def fake_gemini_failure(messages):
        raise RuntimeError("Gemini service is temporarily unavailable")

    monkeypatch.setattr(
        "app.routes.chat.ask_gemini_with_history",
        fake_gemini_failure
    )

    create_response = client.post(
        "/chat/",
        params={"title": "Gemini Failure Test"},
        headers=auth_headers
    )

    assert create_response.status_code == 200

    chat_id = create_response.json()["id"]

    response = client.post(
        f"/chat/{chat_id}/messages",
        json={"content": "Hello"},
        headers=auth_headers
    )

    assert response.status_code == 503

def test_gemini_failure_keeps_user_message(auth_headers, monkeypatch):
    def fake_gemini_failure(messages):
        raise RuntimeError("Gemini service is temporarily unavailable")

    monkeypatch.setattr(
        "app.routes.chat.ask_gemini_with_history",
        fake_gemini_failure
    )

    # Create chat
    create_response = client.post(
        "/chat/",
        params={"title": "Gemini Failure Persistence Test"},
        headers=auth_headers
    )

    assert create_response.status_code == 200

    chat_id = create_response.json()["id"]

    # Try to send a message
    response = client.post(
        f"/chat/{chat_id}/messages",
        json={"content": "This should be saved"},
        headers=auth_headers
    )

    # Gemini failed
    assert response.status_code == 503

    # Check messages stored in database through the API
    messages_response = client.get(
        f"/chat/{chat_id}/messages",
        headers=auth_headers
    )

    assert messages_response.status_code == 200

    messages = messages_response.json()

    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "This should be saved"

def test_delete_chat_removes_messages(auth_headers, mock_gemini):
    create_response = client.post(
        "/chat/",
        params={"title": "Cascade Delete Test"},
        headers=auth_headers
    )

    assert create_response.status_code == 200

    chat_id = create_response.json()["id"]

    message_response = client.post(
        f"/chat/{chat_id}/messages",
        json={"content": "Message before deleting chat"},
        headers=auth_headers
    )

    assert message_response.status_code == 200

    delete_response = client.delete(
        f"/chat/{chat_id}",
        headers=auth_headers
    )

    assert delete_response.status_code == 200

    messages_response = client.get(
        f"/chat/{chat_id}/messages",
        headers=auth_headers
    )

    assert messages_response.status_code == 404

def test_delete_chat_removes_messages_from_database(
    auth_headers,
    mock_gemini
):
    # Create a chat
    create_response = client.post(
        "/chat/",
        params={"title": "Database Cascade Test"},
        headers=auth_headers
    )

    assert create_response.status_code == 200

    chat_id = create_response.json()["id"]

    # Create a message
    message_response = client.post(
        f"/chat/{chat_id}/messages",
        json={"content": "Message to check"},
        headers=auth_headers
    )

    assert message_response.status_code == 200

    message_id = message_response.json()["user_message"]["id"]

    # Delete the chat
    delete_response = client.delete(
        f"/chat/{chat_id}",
        headers=auth_headers
    )

    assert delete_response.status_code == 200

    # Inspect the database directly
    with Session(test_engine) as session:
        message = session.get(Message, message_id)

        assert message is None

