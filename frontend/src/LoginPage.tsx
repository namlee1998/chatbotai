import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    const response = await fetch("https://chatbot-622933104662.asia-southeast1.run.app/api/login", {
      method: "POST",
	  mode: "cors",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ username, password }),
    });

    if (!response.ok) {
      alert("❌ Đăng nhập thất bại");
      return;
    }

    const data = await response.json();
    localStorage.setItem("access_token", data.access_token);
    navigate("/chat");
  };

  return (
    <div className="min-h-screen bg-purple-100 flex flex-col items-center justify-center">
      {/* Phần hình robot và tiêu đề */}
      <div className="flex flex-col items-center mb-6">
        <img
          src="/images/airobot.jpeg" // 👉 Thay bằng link ảnh minh họa thực tế
          alt="AI Robot"
          className="w-28 h-28 mb-3"
        />
        <h1 className="text-red-500 text-4xl font-bold drop-shadow">AI CHATBOT</h1>
      </div>

      {/* Form đăng nhập */}
      <div className="bg-white p-6 rounded shadow-md w-80 space-y-4">
        <label className="text-sm text-gray-700 font-medium">
          Please insert your username here:
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
        />

        <label className="text-sm text-gray-700 font-medium">
          Please insert your password here:
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-400"
        />

        <button
          onClick={handleLogin}
          className="w-full bg-red-500 text-white py-2 rounded hover:bg-red-600 transition"
        >
          LOGIN
        </button>
      </div>
    </div>
  );
}
