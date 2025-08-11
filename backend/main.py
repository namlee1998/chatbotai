import os
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from backend.chatbot import Chatbot
import uvicorn
from fastapi.responses import JSONResponse
from fastapi import Request
from fastapi.staticfiles import StaticFiles

# === Logging setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load env ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
CHROMA_PATH = os.getenv("CHROMA_PATH")
PDF_PATH = os.getenv("PDF_PATH")

# === FastAPI app ===
app = FastAPI()

# Serve frontend static files
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://cra-frontend-622933104662.asia-southeast1.run.app",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
@app.options("/api/chat")
async def options_chat():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
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

# === API chat (no auth) ===
@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    question = payload.question
    if not bot:
        return {"reply": "❌ Bot chưa được khởi tạo"}
    answer = bot.retrieve_top_answer(question) or "I don't know"
    bot.save_chat_history(question, answer)
    return {"reply": answer}

# === WebSocket chat (no auth) ===
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("🔌 WebSocket connected (no auth)")

    try:
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
