// src/components/LoginForm.tsx
"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

export default function LoginForm() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const router = useRouter()

  const handleLogin = async () => {
    try {
      const res = await fetch("http://localhost:8080/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }).toString()
      })

      if (!res.ok) throw new Error("Login failed")
      const data = await res.json()
      localStorage.setItem("token", data.access_token)
      router.push("/chat")
    } catch (err) {
      setError("Sai tài khoản hoặc mật khẩu")
    }
  }

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
