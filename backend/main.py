import os
import json
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from dotenv import load_dotenv
from chatbot import Chatbot
import uvicorn
# === Logging setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load env ===
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
MONGO_URI = os.getenv("MONGO_URI")
CHROMA_PATH = os.getenv("CHROMA_PATH", "D:\\Project\\fullstack_chatbot\\chatbot\\backend\\data")

# === FastAPI app ===
app = FastAPI()
bot = None  # global bot

logger.info("✅ Starting backend server setup...")

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Dummy User ===
fake_users_db = {
    "admin": {
        "username": "admin",
        "password": "Namltmta1998"
    }
}

# === Models ===
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

# === Startup: initialize bot ===
@app.on_event("startup")
async def startup_event():
    logger.info("🔧 Startup event running — chatbot init tạm thời bị vô hiệu hóa")


@app.get("/")
def root():
    return {"message": "Server is alive"}

# === Health check ===
@app.get("/health")
def health_check():
    return {"status": "ok", "server": bot is not None}

# === Auth ===
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = fake_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        logger.warning("❌ Invalid login attempt")
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    logger.info("✅ Login success for user: %s", user["username"])
    return {"access_token": access_token, "token_type": "bearer"}

# === WebSocket chat ===
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        username = verify_token(token)
        await websocket.accept()
        logger.info("🔌 WebSocket connected for: %s", username)

        while True:
            data = await websocket.receive_text()
            logger.info("🧠 Received question: %s", data)

            if not bot:
                await websocket.send_text("❌ Bot not initialized.")
                continue

            previous_answer = bot.check_previous_answer(data)
            if previous_answer:
                await websocket.send_text(json.dumps({"message": previous_answer}))
            else:
                answer = bot.retrieve_top_answer(data)
                answer = answer if answer else "I don't know"
                await websocket.send_text(answer)
                bot.save_chat_history(data, answer)

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error("❌ WebSocket error: %s", str(e))
        await websocket.close()


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, workers=4)
