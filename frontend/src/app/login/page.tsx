"use client";

import { useState } from "react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    const response = await fetch("https://chatbotai-1-r5ha.onrender.com/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username,
        password,
      }),
    });

    if (!response.ok) {
      alert("❌ Đăng nhập thất bại");
      return;
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    window.location.href = "/chat";
  };

  return (
    <div className="min-h-screen bg-purple-100 flex flex-col items-center justify-center">
      <h1 className="text-red-500 text-4xl font-bold drop-shadow mb-8">AI CHATBOT</h1>
      <div className="bg-white p-6 rounded shadow-md w-80 space-y-4">
        <input
          type="text"
          placeholder="Username"
          className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
        <input
          type="password"
          placeholder="Password"
          className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
        <button className="w-full bg-red-500 text-white py-2 rounded hover:bg-red-600 transition">
          LOGIN
        </button>
      </div>
    </div>
  );
}
