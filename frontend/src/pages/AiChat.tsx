import React, { useState, useEffect, useRef } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  Send,
  Sparkles,
  Bot,
  User,
  Copy,
  Check,
  Sliders,
  Cpu,
  Database,
  Loader2,
} from "lucide-react";
import { api } from "../api/client";

interface ChatSession {
  id: string;
  title: string;
  system_prompt: string;
  created_at: string;
  updated_at: string;
}

interface ChatMessage {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  tokens_used?: number;
  created_at: string;
}

export default function AiChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showPromptSettings, setShowPromptSettings] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      loadSessionDetails(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  // Scroll to bottom when messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  async function loadSessions() {
    setLoadingSessions(true);
    try {
      const data = await api.get("/api/v1/chat/sessions");
      setSessions(data || []);
      if (data && data.length > 0 && !activeSessionId) {
        setActiveSessionId(data[0].id);
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    } finally {
      setLoadingSessions(false);
    }
  }

  async function loadSessionDetails(id: string) {
    try {
      const res = await api.get(`/api/v1/chat/sessions/${id}`);
      setMessages(res.messages || []);
      setSystemPrompt(res.session?.system_prompt || "");
    } catch (err) {
      console.error("Failed to load session details:", err);
    }
  }

  async function handleCreateSession() {
    try {
      const newSession = await api.post("/api/v1/chat/sessions", {
        title: "New Conversation",
        system_prompt: systemPrompt || undefined,
      });
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  }

  async function handleDeleteSession(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await api.del(`/api/v1/chat/sessions/${id}`);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        const remaining = sessions.filter((s) => s.id !== id);
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  }

  async function handleSendMessage(contentToSend?: string) {
    const text = contentToSend || inputPrompt;
    if (!text.trim() || isSending) return;

    let targetSessionId = activeSessionId;
    if (!targetSessionId) {
      // Auto-create a session if none is selected
      try {
        const newSession = await api.post("/api/v1/chat/sessions", {
          title: text.slice(0, 30) + (text.length > 30 ? "..." : ""),
          system_prompt: systemPrompt || undefined,
        });
        setSessions((prev) => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        targetSessionId = newSession.id;
      } catch (err) {
        console.error("Failed to create session for message:", err);
        return;
      }
    }

    const currentSessionId = targetSessionId;
    if (!currentSessionId) return;

    const optimisticUserMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      session_id: currentSessionId,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, optimisticUserMsg]);
    setInputPrompt("");
    setIsSending(true);

    try {
      const res = await api.post(
        `/api/v1/chat/sessions/${targetSessionId}/messages`,
        { content: text }
      );

      setMessages((prev) => [
        ...prev.filter((m) => m.id !== optimisticUserMsg.id),
        res.user_message,
        res.assistant_message,
      ]);

      // Update session title in sidebar if it was updated
      loadSessions();
    } catch (err) {
      console.error("Failed to send message:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: "err-" + Date.now(),
          session_id: currentSessionId,
          role: "assistant",
          content: "⚠️ Failed to receive response from Azure OpenAI. Please check your network and API key configuration.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  function copyToClipboard(text: string, id: string) {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  const starterPrompts = [
    "Explain how Cloudflare Workers and D1 work together",
    "Write a Python FastAPI service connecting to Azure OpenAI",
    "What are the benefits of Serverless SQL over traditional PostgreSQL?",
    "Give me 5 architectural tips for low-latency AI agents",
  ];

  return (
    <div className="flex h-[calc(100vh-85px)] bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* ── Left Sidebar (Conversations) ─────────────────────────────────── */}
      <div className="w-72 bg-gray-50 border-r border-gray-200 flex flex-col justify-between">
        <div className="p-4 flex flex-col flex-1 overflow-hidden">
          <button
            onClick={handleCreateSession}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg shadow-sm transition-all mb-4 text-sm"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </button>

          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-1">
            History (D1 SQL)
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {loadingSessions ? (
              <div className="flex items-center justify-center p-6 text-gray-400 text-xs">
                <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading chats...
              </div>
            ) : sessions.length === 0 ? (
              <div className="p-4 text-center text-xs text-gray-400">
                No chat history yet. Start a new conversation!
              </div>
            ) : (
              sessions.map((s) => (
                <div
                  key={s.id}
                  onClick={() => setActiveSessionId(s.id)}
                  className={`group flex items-center justify-between p-2.5 rounded-lg cursor-pointer text-sm transition-colors ${
                    activeSessionId === s.id
                      ? "bg-blue-50 text-blue-900 font-medium"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className="w-4 h-4 shrink-0 text-gray-400 group-hover:text-blue-500" />
                    <span className="truncate">{s.title || "Untitled Chat"}</span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(s.id, e)}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 transition-opacity p-1"
                    title="Delete session"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Cloudflare & Azure Architecture Badge */}
        <div className="p-3 bg-gray-100 border-t border-gray-200 text-xs text-gray-600 space-y-1.5">
          <div className="flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-blue-600" />
            <span className="font-semibold text-gray-800">Model:</span>
            <span>Azure gpt-4.1-mini</span>
          </div>
          <div className="flex items-center gap-2">
            <Database className="w-3.5 h-3.5 text-amber-600" />
            <span className="font-semibold text-gray-800">Storage:</span>
            <span>Cloudflare D1 SQL</span>
          </div>
        </div>
      </div>

      {/* ── Main Chat Area ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col justify-between bg-white overflow-hidden">
        {/* Chat Header */}
        <div className="px-6 py-3 border-b border-gray-100 flex items-center justify-between bg-white z-10">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-gray-900">
                {sessions.find((s) => s.id === activeSessionId)?.title || "AI Agent Workspace"}
              </h2>
              <p className="text-xs text-gray-500">
                Cloudflare Workers • FastAPI • Azure OpenAI
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowPromptSettings(!showPromptSettings)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              showPromptSettings
                ? "bg-blue-50 border-blue-200 text-blue-700"
                : "bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            System Persona
          </button>
        </div>

        {/* System Prompt Customizer Collapsible */}
        {showPromptSettings && (
          <div className="bg-slate-50 border-b border-slate-200 p-4 transition-all">
            <label className="block text-xs font-semibold text-gray-700 mb-1">
              Custom System Instructions (Saved in D1)
            </label>
            <input
              type="text"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="e.g. You are a senior software architect specializing in Cloudflare & AI..."
              className="w-full text-xs p-2.5 bg-white border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        )}

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-12">
              <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-sm border border-blue-100">
                <Sparkles className="w-7 h-7" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Cloudflare Agent Workspace
              </h3>
              <p className="text-sm text-gray-500 mb-6">
                Powered by Azure OpenAI <strong>gpt-4.1-mini</strong> with full conversation persistence in <strong>Cloudflare D1 Serverless SQL</strong>.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full text-left">
                {starterPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSendMessage(prompt)}
                    className="p-3 bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-200 rounded-xl text-xs text-gray-700 transition-all text-left"
                  >
                    "{prompt}"
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3.5 ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {m.role === "assistant" && (
                  <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0 mt-0.5 shadow-xs">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`group relative max-w-2xl rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-blue-600 text-white rounded-br-xs"
                      : "bg-gray-100 text-gray-900 rounded-bl-xs"
                  }`}
                >
                  <div className="whitespace-pre-wrap">{m.content}</div>

                  <div
                    className={`flex items-center gap-2 mt-2 pt-1 border-t text-[10px] ${
                      m.role === "user"
                        ? "border-blue-500/50 text-blue-200"
                        : "border-gray-200 text-gray-400"
                    }`}
                  >
                    <span>{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    {m.tokens_used ? <span>• {m.tokens_used} tokens</span> : null}

                    <button
                      onClick={() => copyToClipboard(m.content, m.id)}
                      className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity hover:text-gray-700"
                      title="Copy text"
                    >
                      {copiedId === m.id ? (
                        <Check className="w-3 h-3 text-green-500" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                    </button>
                  </div>
                </div>

                {m.role === "user" && (
                  <div className="w-7 h-7 rounded-full bg-gray-800 flex items-center justify-center text-white shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))
          )}

          {/* Loading Indicator */}
          {isSending && (
            <div className="flex gap-3.5 justify-start">
              <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-gray-100 rounded-2xl px-4 py-3 text-sm text-gray-500 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span>Generating response with gpt-4.1-mini...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-gray-100 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-end gap-2 bg-gray-50 border border-gray-200 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 rounded-xl p-2 transition-all"
          >
            <textarea
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask anything or request code (Press Enter to send, Shift+Enter for new line)..."
              rows={2}
              className="flex-1 bg-transparent text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none px-2 py-1"
            />
            <button
              type="submit"
              disabled={!inputPrompt.trim() || isSending}
              className={`p-2.5 rounded-lg text-white transition-all ${
                inputPrompt.trim() && !isSending
                  ? "bg-blue-600 hover:bg-blue-700 shadow-sm"
                  : "bg-gray-300 cursor-not-allowed"
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="flex justify-between items-center px-2 pt-2 text-[11px] text-gray-400">
            <span>Connected to Cloudflare D1 Serverless SQL</span>
            <span>Azure OpenAI Service</span>
          </div>
        </div>
      </div>
    </div>
  );
}
