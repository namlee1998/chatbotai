"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Trash2, Loader2 } from "lucide-react"

export default function ChatPage() {
  const [question, setQuestion] = useState("")
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([])
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const token = localStorage.getItem("token")
    if (!token) return

    const ws = new WebSocket(`ws://localhost:8080/ws?token=${token}`)

    ws.onopen = () => console.log("✅ Connected")
    ws.onmessage = (event) => {
      setMessages((prev) => [...prev, { role: "bot", text: event.data }])
      setLoading(false)
    }
    ws.onclose = () => console.log("❌ Disconnected")
    setSocket(ws)

    return () => ws.close()
  }, [])

  const sendMessage = () => {
    if (socket && question.trim()) {
      socket.send(question)
      setMessages((prev) => [...prev, { role: "user", text: question }])
      setQuestion("")
      setLoading(true)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = () => {
    setMessages([])
  }

  return (
    <div className="flex justify-center items-center min-h-screen bg-background px-4">
      <div className="w-full max-w-2xl">
        <Card>
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold">🤖 Chatbot</CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="flex justify-end">
              <Button variant="ghost" size="sm" onClick={clearChat} title="Clear chat">
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>

            <ScrollArea className="h-[300px] pr-4">
              {messages.map((msg, index) => (
                <div key={index} className="text-sm mb-2">
                  <span className="font-semibold">
                    {msg.role === "user" ? "🧠 You: " : "🤖 Bot: "}
                  </span>
                  <span>{msg.text}</span>
                </div>
              ))}
              {loading && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Đang trả lời...
                </div>
              )}
              <div ref={messagesEndRef} />
            </ScrollArea>

            <div className="flex gap-2">
              <Textarea
                className="flex-1 resize-none"
                rows={2}
                placeholder="Nhập câu hỏi..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <Button onClick={sendMessage} disabled={!question.trim()}>
                Gửi
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
