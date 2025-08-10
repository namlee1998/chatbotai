import React, { useState } from "react";

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const handleSend = async () => {
    if (!question.trim()) return;

    const token = localStorage.getItem("access_token");

    try {
      const response = await fetch("https://backend-service-622933104662.asia-southeast1.run.app/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ question }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnswer(data.reply);
      } else {
        setAnswer("❌ Lỗi xử lý yêu cầu.");
      }
    } catch (error) {
      setAnswer("❌ Không thể kết nối tới chatbot.");
      console.error("Chat error:", error);
    }

    setQuestion(""); // reset input
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-slate-900 flex flex-col items-center justify-center p-6 space-y-6">
      {/* Hình ảnh robot + tiêu đề */}
      <div className="flex flex-col items-center space-y-4">
        <img
          src="/images/thinkrobot.JPEG" // 👉 Thay bằng link thật của ảnh robot
          alt="Chatbot Robot"
          className="w-32 h-32"
        />
        <h1 className="text-white text-4xl font-bold drop-shadow">Namlee Chatbot</h1>
      </div>

      {/* Form chat */}
      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md space-y-4">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Hãy hỏi bất cứ điều gì..."
          className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />

        <button
          onClick={handleSend}
          className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition"
        >
          Gửi
        </button>

        <div className="bg-gray-100 p-4 rounded min-h-[100px]">
          <p className="text-sm font-semibold text-gray-500 mb-1">
            Phản hồi từ chatbot:
          </p>
          <p>{answer}</p>
        </div>
      </div>
    </div>
  );
}
