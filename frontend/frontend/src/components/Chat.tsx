'use client';
import { useState, useRef, useEffect } from 'react';

const Chat = () => {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    socket.current = new WebSocket("ws://localhost:8080/ws");

    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages((prev) => [...prev, { role: "bot", content: data.message }]);
    };

    return () => socket.current?.close();
  }, []);

  return (
    <div>
      {messages.map((msg, idx) => (
        <p key={idx}><strong>{msg.role}:</strong> {msg.content}</p>
      ))}
    </div>
  );
};

export default Chat;
