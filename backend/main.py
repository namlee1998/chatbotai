import os
import json
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import JWTError, jwt
from dotenv import load_dotenv
from chatbot import Chatbot
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import uvicorn
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles
# === Logging setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load env ===
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
MONGO_URI = os.getenv("MONGO_URI")
CHROMA_PATH = os.getenv("CHROMA_PATH")
PDF_PATH = os.getenv("PDF_PATH")

# === FastAPI app ===
app = FastAPI()

app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cra-frontend-622933104662.asia-southeast1.run.app", "http://localhost:3000"],
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

# Auth setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    question: str

# === Global bot ===
bot = None

# === Custom Exception Handler for CORS ===
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "https://cra-frontend-622933104662.asia-southeast1.run.app",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# === OPTIONS Handler for Preflight ===
@app.options("/api/login")
async def options_login():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "https://cra-frontend-622933104662.asia-southeast1.run.app",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true"
        }
    )

# === Startup: initialize bot ===
@app.on_event("startup")
async def startup_event():
    global bot
    try:
        logger.info("🔧 Initializing Chatbot at startup...")
        bot = Chatbot(mongo_uri=MONGO_URI, chroma_path=CHROMA_PATH, db_name="chatbot_db")
        logger.info("✅ Chatbot initialized at startup")

        pdf_path = os.getenv("PDF_PATH")
        if not os.path.exists(PDF_PATH):
            logger.warning(f"❌ PDF file not found at: {PDF_PATH}")
            return

        qa_pairs = bot.load_and_prepare_documents([PDF_PATH])
        if qa_pairs:
            bot.create_vector_store()
            logger.info(f"✅ Vector DB created at startup with {len(qa_pairs)} QA pairs")
        else:
            logger.warning("⚠️ No QA pairs extracted from PDF")

    except Exception as e:
        logger.error("❌ Error initializing chatbot or vector store: %s", str(e))
        bot = None

    logger.info("🚀 Startup event completed")

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
    logger.info("Login request: username=%s, password=%s", form_data.username, form_data.password)
    user = fake_users_db.get(form_data.username)
    if not user or user["password"] != form_data.password:
        logger.warning("❌ Invalid login attempt for username: %s", form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    logger.info("✅ Login success for user: %s", user["username"])
    return {"access_token": access_token, "token_type": "bearer"}

# === API chat ===
@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest, token: str = Depends(oauth2_scheme)):
    username = verify_token(token)
    question = payload.question

    if not bot:
        return {"reply": "❌ Bot chưa được khởi tạo"}
    answer = bot.retrieve_top_answer(question) or "I don't know"
    bot.save_chat_history(question, answer)
    return {"reply": answer}

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
