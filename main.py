from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from passlib.context import CryptContext
from pydantic import BaseModel
import jwt
import time
import httpx
import pymssql
import urllib

server = 'cst8912-chatbot.database.windows.net'
database = 'user'
username = 'gundami'
password = 'Cyy@@52363465'
encoded_password = urllib.parse.quote_plus(password)

# Database configuration
DATABASE_URL = f"mssql+pymssql://{username}:{encoded_password}@{server}/{database}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Password encryption configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User")
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    sender = Column(String(50))
    content = Column(Text)
    timestamp = Column(Integer)
    chat = relationship("Chat", back_populates="messages")

Base.metadata.create_all(bind=engine)

# Application instance
app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates configuration
templates = Jinja2Templates(directory="templates")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = time.time() + expires_delta * 60
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: SessionLocal = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Routes

# Render homepage
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Registration route
class RegisterData(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(data: RegisterData, db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = get_password_hash(data.password)
    new_user = User(username=data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "Registration successful"}

# Login route
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: SessionLocal = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# Get chat list
@app.get("/chats")
def get_chats(current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    chats = db.query(Chat).filter(Chat.user_id == current_user.id).all()
    return chats

# Create new chat
@app.post("/chats")
def create_chat(current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    new_chat = Chat(user_id=current_user.id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

# Get messages
@app.get("/chats/{chat_id}/messages")
def get_messages(chat_id: int, current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages

# Send message
class MessageData(BaseModel):
    content: str

@app.post("/chats/{chat_id}/messages")
def send_message(chat_id: int, data: MessageData, current_user: User = Depends(get_current_user), db: SessionLocal = Depends(get_db)):
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    # Save user message
    user_message = Message(chat_id=chat_id, sender="user", content=data.content, timestamp=int(time.time()))
    db.add(user_message)
    db.commit()
    # Get AI response
    ai_reply = get_ai_response(data.content)
    ai_message = Message(chat_id=chat_id, sender="ai", content=ai_reply, timestamp=int(time.time()))
    db.add(ai_message)
    db.commit()
    return {"reply": ai_reply}

def get_ai_response(user_input):
    # Implement your AI response logic here
    endpoint = "https://chen1-m4nno74e-eastus2.cognitiveservices.azure.com/"
    api_key = "t8TTJ2BGhk96Gt3Dnd9qwnaXK7Fd8NxZFu5vLS1wH1NgC79x3DFDJQQJ99ALACHYHv6XJ3w3AAAAACOGLILN"
    deployment_name = "gpt-4o-mini"
    api_version = "2024-08-01-preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    data = {
        "messages": [{"role": "user", "content": user_input}]
    }
    response = httpx.post(
        f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}",
        headers=headers,
        json=data
    )
    result = response.json()
    return result['choices'][0]['message']['content']

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)