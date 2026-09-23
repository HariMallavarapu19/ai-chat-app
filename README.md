# AI Chat API

A backend API for an AI chat application built with FastAPI, SQLModel, JWT authentication, and Google Gemini.

## Features

- User registration
- User login with JWT authentication
- Protected API endpoints
- User-specific chat ownership
- Create, read, and delete chats
- Send messages to Gemini
- Persistent chat history
- Conversation context using recent messages
- Error handling for Gemini failures
- Input validation
- Database uniqueness for username and email
- API documentation with Swagger
- Automated tests
- Docker support

## Tech Stack

- Python
- FastAPI
- SQLModel
- SQLite
- JWT
- pwdlib + Argon2
- Google Gemini API
- Pytest
- Docker

## Project Structure

```text
chat_app/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── routes/
│   │   ├── auth.py
│   │   └── chat.py
│   └── services/
│       └── gemini.py
│
├── tests/
│   └── test_main.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md


## Environment Variables

Create a .env file in the project root:

SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key

Do not commit .env to Git.

## Run Locally
1. Create and activate the virtual environment

Windows PowerShell:

python -m venv ve
.\ve\Scripts\Activate.ps1
2. Install dependencies
pip install -r requirements.txt
3. Start the API
uvicorn app.main:app --reload

The API will be available at:

http://localhost:8000

Swagger documentation:

http://localhost:8000/docs

## Run Tests

Run the test suite with:

pytest -q

The project currently contains 25 tests covering authentication, authorization, chat operations, message operations, Gemini error handling, and other important API behavior.

## Run with Docker

Make sure Docker Desktop is running.

Build the Docker image
docker build -t ai-chat-app .
Run the container
docker run --name ai-chat-container -p 8000:8000 --env-file .env ai-chat-app

The API will then be available at:

http://localhost:8000

Swagger:

http://localhost:8000/docs
## Stop the container

Press:

Ctrl + C

or, if the container is running in the background:

docker stop ai-chat-container
## API Overview
## Authentication
POST /auth/register
POST /auth/login
GET  /auth/me
## Chats
POST   /chat/
GET    /chat/
GET    /chat/{chat_id}
DELETE /chat/{chat_id}
## Messages
POST   /chat/{chat_id}/messages
GET    /chat/{chat_id}/messages
DELETE /chat/{chat_id}/messages/{message_id}

## Authentication

Protected endpoints require a JWT access token.

Send the token using:

Authorization: Bearer <access_token>

Swagger can be used to test the protected endpoints after logging in.

## Architecture

The application follows a simple layered structure:

Client
  ↓
FastAPI Routes
  ↓
Authentication / Authorization
  ↓
SQLModel / SQLite
  ↓
Gemini Service
  ↓
AI Response

Chat messages are stored in the database, allowing recent conversation history to be sent to Gemini when generating a response.

## Docker Architecture
Dockerfile
    ↓
Docker Image
    ↓
Docker Container
    ↓
Uvicorn
    ↓
FastAPI

The local Python virtual environment (ve) is separate from the Docker environment.
