"use client";

import { useState } from "react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    const response = await fetch("http://localhost:8080/api/login", {
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
    <div className="min-h-screen flex flex-col items-center justify-center px-4">
      <h1 className="text-2xl font-bold mb-4">🔐 Đăng nhập</h1>
      <div className="max-w-sm w-full border rounded p-4 shadow bg-white space-y-4">
        <input
          type="text"
          value={username}
          placeholder="Tên đăng nhập"
          onChange={(e) => setUsername(e.target.value)}
          className="w-full border rounded px-3 py-2"
        />
        <input
          type="password"
          value={password}
          placeholder="Mật khẩu"
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border rounded px-3 py-2"
        />
        <button
          onClick={handleLogin}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full"
        >
          Đăng nhập
        </button>
      </div>
    </div>
  );
}
