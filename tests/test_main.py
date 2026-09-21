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
    



