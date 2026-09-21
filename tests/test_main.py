import pytest
import uuid

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_session


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