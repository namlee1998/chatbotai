"use client";

import { useEffect, useRef, useState } from "react";

type Message = { role: "user" | "bot"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      alert("Bạn chưa đăng nhập!");
      window.location.href = "/login";
      return;
    }

    socket.current = new WebSocket(`ws://localhost:8080/ws?token=${token}`);

    socket.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [...prev, { role: "bot", content: data.message }]);
      } catch {
        setMessages((prev) => [...prev, { role: "bot", content: event.data }]);
      }
    };

    return () => socket.current?.close();
  }, []);

  const sendMessage = () => {
    if (!input.trim()) return;
    socket.current?.send(input);
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setInput("");
  };

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <h1 className="text-2xl font-bold">Chatbot</h1>
      <div className="h-96 overflow-y-auto bg-gray-100 p-4 rounded space-y-2">
        {messages.map((msg, i) => (
          <div key={i} className={`max-w-sm px-3 py-2 rounded ${msg.role === "user" ? "bg-blue-200 ml-auto" : "bg-gray-300 mr-auto"}`}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 border px-3 py-2 rounded"
          placeholder="Nhập câu hỏi..."
        />
        <button onClick={sendMessage} className="bg-blue-600 text-white px-4 py-2 rounded">
          Gửi
        </button>
      </div>
    </div>
  );
}
