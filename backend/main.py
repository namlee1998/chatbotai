import os
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from backend.chatbot import Chatbot
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

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

# Serve frontend static files under /static
app.mount("/static", StaticFiles(directory="backend/static", html=True), name="static")

# Serve index.html at root
@app.get("/")
def serve_index():
    return FileResponse("backend/static/index.html")

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

# === Health check ===
@app.get("/health")
def health_check():
    return {"status": "ok", "server": bot is not None}

# === API chat ===
@app.post("/api/chat")
async def chat_endpoint(payload: ChatRequest):
    question = payload.question
    if not bot:
        return {"reply": "❌ Bot chưa được khởi tạo"}
    answer = bot.retrieve_top_answer(question) or "I don't know"
    bot.save_chat_history(question, answer)
    return {"reply": answer}

# === WebSocket chat ===
@app.websocket("/ws")
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
                answer = bot.retrieve_top_answer(data)
                answer = answer if answer else "I don't know"
                await websocket.send_text(answer)
                bot.save_chat_history(data, answer)

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error("❌ WebSocket error: %s", str(e))
        await websocket.close()
