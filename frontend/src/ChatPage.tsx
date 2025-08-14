// frontend/src/ChatPage.jsx
import React, { useState, useEffect } from "react";

export default function ChatPage() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [botReady, setBotReady] = useState(false);

  useEffect(() => {
    let timer;

    const checkBot = async () => {
      try {
        const res = await fetch("/api/health");
        const data = await res.json();
        setBotReady(Boolean(data.server));
      } catch (error) {
        console.error("Error checking bot health:", error);
        setBotReady(false);
      }
    };

    checkBot(); // check ngay khi load
    timer = setInterval(checkBot, 5000); // poll mỗi 5s

    return () => clearInterval(timer);
  }, []);

  const handleSend = async () => {
    if (!question.trim()) return;
    if (!botReady) {
      setAnswer("⚠️ Bot chưa sẵn sàng, thử lại sau.");
      return;
    }

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
    setQuestion("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-slate-900 flex flex-col items-center justify-center p-6 space-y-6">
      <div className="flex flex-col items-center space-y-4">
        <img src="/images/thinkrobot.jpeg" alt="Chatbot Robot" className="w-60 h-60" />
        <h1 className="text-white text-4xl font-bold drop-shadow">Namlee Chatbot</h1>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md space-y-4">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Hãy hỏi bất cứ điều gì..."
          className="w-full p-3 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-indigo-400"
        />

        <button onClick={handleSend} className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition">
          Gửi
        </button>

        <div className="bg-gray-100 p-4 rounded min-h-[100px]">
          <p className="text-sm font-semibold text-gray-500 mb-1">Phản hồi từ chatbot:</p>
          <p>{answer}</p>
        </div>
      </div>
    </div>
  );
}
