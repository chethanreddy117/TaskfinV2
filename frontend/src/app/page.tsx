"use client";

import { useState } from "react";
import axios from "axios";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState<string | null>(null);

  const BACKEND_URL = "http://localhost:8000";

  // ---------------- Health Check ----------------
  const isBackendHealthy = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      return res.ok;
    } catch {
      return false;
    }
  };

  // ---------------- Submit ----------------
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      // ✅ Health check FIRST
      const healthy = await isBackendHealthy();
      if (!healthy) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Backend is unavailable. Please try again later.",
          },
        ]);
        return;
      }

      // 🔐 Login once
      let authToken = token;
      if (!authToken) {
        const loginRes = await axios.post(`${BACKEND_URL}/login`, {
          username: "chethan",
          password: "1234",
        });

        authToken = loginRes.data.access_token;
        setToken(authToken);
      }

      // 💬 Chat
      const chatRes = await axios.post(
        `${BACKEND_URL}/agent/chat`,
        { message: userMessage.content },
        {
          headers: {
            Authorization: `Bearer ${authToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: chatRes.data.response },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error communicating with backend. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // ---------------- UI ----------------
  return (
    <main className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl h-[80vh] bg-white rounded-xl shadow-lg flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-blue-600 text-white">
          <h1 className="text-xl font-semibold">TaskFin</h1>
          <p className="text-xs opacity-90">
            Agent-Based Bill Payment Assistant
          </p>
        </div>

        {/* System Hint */}
        <div className="text-xs text-gray-500 text-center py-2 border-b bg-gray-50">
          Secure session • Mock financial data
        </div>

        {/* Messages */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-gray-50">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[75%] px-4 py-3 rounded-xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-white text-gray-900 border rounded-bl-none"
                }`}
              >
                <span className="whitespace-pre-line">
                  {msg.content}
                </span>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border px-4 py-3 rounded-xl text-sm animate-pulse">
                Processing request…
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <form
          onSubmit={handleSubmit}
          className="p-4 border-t bg-white flex gap-3"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your bills or payments…"
            className="flex-1 px-4 py-3 bg-black text-white placeholder-gray-400 border border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </form>
      </div>
    </main>
  );
}
