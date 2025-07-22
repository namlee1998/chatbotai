

import os
import shutil
from datetime import datetime

from pymongo import MongoClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
import os
import time
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from fastapi import FastAPI

app = FastAPI()

# Load .env file (default is .env, or you can specify)
load_dotenv(".env")  # hoặc ".env" nếu bạn để cùng thư mục

# Truy cập biến môi trường
mongo_uri = os.getenv("MONGO_URI")
chroma_path = os.getenv("CHROMA_PATH", r"D:\Project\fullstack_chatbot\chatbot\backend\data")
model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")



# ============================================
# 🧠 Chatbot Class
# ============================================

class Chatbot:
    def __init__(self, mongo_uri,chroma_path, db_name="chatbot_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.history_collection = self.db["chat_history"]
        self.feedback_collection = self.db["feedback"]

        self.chroma_path = chroma_path
        try:
            if os.path.exists(self.chroma_path):
                shutil.rmtree(self.chroma_path)
        except Exception as e:
            print(f"❌ Không thể xoá thư mục vectorstore: {str(e)}")

        os.makedirs(self.chroma_path, exist_ok=True)

        self.embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vectordb = None
        self.qa_pairs = []

    # ============================================
    # 📄 Document Handling
    # ============================================

    def load_and_prepare_documents(self, file_paths):
        docs = []
        for path in file_paths:
            if path.lower().endswith(".pdf"):
                loader = PyPDFLoader(path)
                docs.extend(loader.load())

        qa_pairs = []
        for doc in docs:
            lines = doc.page_content.strip().split('\n')
            question = None
            answer = None
            for line in lines:
                line = line.strip()
                if line.lower().startswith("q:"):
                    question = line[2:].strip()
                elif line.lower().startswith("a:") and question:
                    answer = line[2:].strip()
                    qa_pairs.append((question, answer))
                    question = None
                    answer = None

        self.qa_pairs = qa_pairs
        return qa_pairs



    def create_vector_store(self):
        try:
            print("📦 Đang tạo Vector Store bằng FAISS...")

            questions = [Document(page_content=qa[0]) for qa in self.qa_pairs]

            vectordb = FAISS.from_documents(
                documents=questions,
                embedding=self.embedding
            )

            # Lưu lại nếu muốn (không bắt buộc)
            vectordb.save_local(self.chroma_path)

            self.vectordb = vectordb
            print(f"✅ Vector DB (FAISS) created với {len(questions)} câu hỏi.")
        except Exception as e:
            print(f"❌ Lỗi khi tạo Vector Store: {str(e)}")



    # ============================================
    # 🔎 Retrieval
    # ============================================

    def retrieve_top_answer(self, question):
        if not self.vectordb:
            print("❌ vectordb chưa được khởi tạo")
            return "I don't know"
        results = self.vectordb.similarity_search(question, k=1)
        if not results:
            return None

        matched_question = results[0].page_content.strip().lower()

        for q, a in self.qa_pairs:
            if q.strip().lower() == matched_question:
                return a.strip()
        return None

    def retrieve_top3_answers(self, question):
        results = self.vectordb.similarity_search(question, k=3)
        suggestions = []
        for res in results:
            matched_question = res.page_content.strip().lower()
            for q, a in self.qa_pairs:
                if q.strip().lower() == matched_question:
                    suggestions.append(a)
        return suggestions

    # ============================================
    # 📑 MongoDB Logging
    # ============================================

    def check_previous_answer(self, question):
        result = self.history_collection.find_one({"question": question.strip().lower()})
        if result:
            return result["response"]
        return None

    def save_chat_history(self, question, answer):
        self.history_collection.update_one(
            {"question": question.strip().lower()},
            {"$set": {
                "response": answer.strip(),
                "timestamp": datetime.utcnow()
            }},
            upsert=True  # cập nhật nếu có, thêm mới nếu chưa có
        )


    def save_feedback(self, question, model_answer, feedback, corrected=None):
        self.feedback_collection.insert_one({
            "question": question.strip().lower(),
            "model_answer": model_answer,
            "user_feedback": feedback,
            "user_suggested_answer": corrected,
            "timestamp": datetime.utcnow()
        })

    # ============================================
    # 📝 Feedback Handling
    # ============================================

    def handle_feedback(self, question, answer):
        feedback = input("👍👎 Is the answer good? (y/n): ").lower()

        if feedback == "n":
            suggestions = self.retrieve_top3_answers(question)

            if suggestions:
                print("\n💡 Suggested better answers:")
                for idx, s in enumerate(suggestions):
                    print(f"{idx+1}. {s}")

                try:
                    choice = int(input("Select (1-3) or 0 to skip: "))
                except:
                    choice = 0

                if 1 <= choice <= len(suggestions):
                    better = suggestions[choice - 1]
                    self.save_feedback(question, answer, "bad", better)
                    self.save_chat_history(question, better)
                    print("✅ Feedback saved with selected suggestion.")
                else:
                    print("ℹ️ Feedback skipped.")
            else:
                print("⚠️ No suggestions found.")
                self.save_feedback(question, answer, "bad", None)

        else:
            self.save_feedback(question, answer, "good")
            print("✅ Feedback saved as good.")


# ============================================
# 🚀 MAIN CHAT LOOP
# ============================================

if __name__ == "__main__":
    start_time = time.time()

    print("🔧 Đang khởi tạo Chatbot...")
    bot = Chatbot(mongo_uri=mongo_uri,chroma_path=chroma_path)
    print(f"✅ Chatbot initialized in {time.time() - start_time:.2f}s")
    
    print("📄 Đang load và tách tài liệu PDF...")
    qa_pairs= bot.load_and_prepare_documents(["D:/Project/fullstack_chatbot/backend/trainchatbot.pdf"])
    print(f"✅ Tải {len(qa_pairs)} cặp hỏi đáp thành công")
    
    try:
        print("📦 Đang tạo Vector Store (có thể mất vài phút)...")
        start_time = time.time()
        bot.create_vector_store()
        print(f"✅ Vector Store created in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"❌ Lỗi khi tạo Vector Store: {str(e)}")

    
    
    print("\n🤖 Chatbot ready. Type 'exit' to quit.\n")

    while True:
        q = input("🧠 You: ").strip()

        if q.lower() in ["exit", "quit"]:
            print("👋 Bye!")
            break

        # Check history in MongoDB
        previous_answer = bot.check_previous_answer(q)

        if previous_answer:
            print(f"\n🤖 Answer (from memory): {previous_answer}")
        else:
            # Retrieve from vector DB
            answer = bot.retrieve_top_answer(q)

            if answer:
                print(f"\n🤖 Answer: {answer}")
                bot.save_chat_history(q, answer)
            else:
                print("\n🤖 Answer: I don't know")
                bot.save_chat_history(q, "I don't know")

            # Feedback
            bot.handle_feedback(q, answer if answer else "I don't know")