# backend/main.py
import os
import json
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from backend.chatbot import Chatbot

# === Logging setup ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Load env ===
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
CHROMA_PATH = os.getenv("CHROMA_PATH", "/app/data")  # default an toàn
# Nếu PDF_PATH không set từ env, mặc định dùng file đã COPY trong image
PDF_PATH = os.getenv("PDF_PATH", "/app/trainchatbot.pdf"))

# === FastAPI app ===
app = FastAPI()

class ChatRequest(BaseModel):
    question: str

# === Global bot ===
bot = None

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
            return  # giữ nguyên logic: bot vẫn tồn tại, chỉ không build vector

        qa_pairs = bot.load_and_prepare_documents([PDF_PATH])
        if qa_pairs:
            bot.create_vector_store()
            logger.info(f"✅ Vector DB created at startup with {len(qa_pairs)} QA pairs")
        else:
            logger.warning("⚠️ No QA pairs extracted from PDF")

    except Exception as e:
        # Log full stack trace để dễ debug
        logger.exception("❌ Error initializing chatbot or vector store")
        bot = None

    logger.info("🚀 Startup event completed")

# === API chat ===
@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    question = payload.question
    if not bot:
        return {"reply": "❌ Bot chưa được khởi tạo"}
    answer = bot.retrieve_top_answer(question) or "I don't know"
    bot.save_chat_history(question, answer)
    return {"reply": answer}

# === Health check ===
@app.get("/api/health")
def health_check():
    # giữ nguyên cấu trúc trả về cũ để frontend không phải đổi nhiều
    return {"status": "ok", "server": bot is not None}

# === WebSocket chat ===
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("🔌 WebSocket connected")

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
                answer = bot.retrieve_top_answer(data) or "I don't know"
                await websocket.send_text(answer)
                bot.save_chat_history(data, answer)

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception:
        logger.exception("❌ WebSocket error")
        await websocket.close()

# === Serve frontend static files (React build) ===
app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
