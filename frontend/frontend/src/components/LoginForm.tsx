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
    <div className="w-full max-w-md p-6 bg-white dark:bg-gray-900 rounded-xl shadow">
      <h2 className="text-2xl font-semibold text-center mb-4">Đăng nhập</h2>
      <Input className="mb-3" placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
      <Input className="mb-3" placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      {error && <p className="text-sm text-red-500 mb-2">{error}</p>}
      <Button className="w-full" onClick={handleLogin}>Đăng nhập</Button>
    </div>
  )
}