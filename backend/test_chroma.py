from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
import os

print("➡ Khởi tạo documents và embeddings...")

documents = [Document(page_content="What is AI?"), Document(page_content="What is LangChain?")]
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

persist_path = r"D:\Project\fullstack_chatbot\chatbot\backend\data_test"

if os.path.exists(persist_path):
    import shutil
    shutil.rmtree(persist_path)

print("➡ Gọi Chroma.from_documents...")
db = Chroma.from_documents(documents, embedding=embedding, persist_directory=persist_path)

print("➡ Ghi vector xuống ổ đĩa...")
db.persist()

print("✅ Test Chroma thành công!")
