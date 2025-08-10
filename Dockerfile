# Stage 1: Build React frontend
FROM node:18 AS frontend-builder
WORKDIR /app/frontend

# Cài đặt dependencies và build
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Build FastAPI backend
FROM python:3.11-slim AS backend

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV CHROMA_PATH=/app/data
ENV PORT=8080

# Cài đặt hệ thống cần thiết
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt pip và spaCy
RUN pip install --upgrade pip && \
    pip install spacy && \
    python -m spacy download en_core_web_sm

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn backend
COPY backend/ ./backend

# Copy file PDF cần thiết
COPY trainchatbot.pdf ./trainchatbot.pdf

# Copy frontend đã build vào thư mục static của backend
COPY --from=frontend-builder /app/frontend/build ./backend/static

# Tạo thư mục dữ liệu
RUN mkdir -p /app/data

# Mở cổng 8080 cho Cloud Run
EXPOSE 8080

# Chạy ứng dụng FastAPI bằng uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]

