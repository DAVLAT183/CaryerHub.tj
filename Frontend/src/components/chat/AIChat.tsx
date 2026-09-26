'use client';

import { useState, useEffect, useRef } from 'react';
import { Send, User, Sparkles, Loader2, MessageSquare } from 'lucide-react';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import { showToast, getErrorMessage } from '@/lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  created_at?: string;
}

interface ChatSession {
  id: number;
  title: string;
  messages: Message[];
  last_message: Message | null;
  created_at: string;
}

export default function AIChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const res = await api.get('/chat/sessions/');
      const data = res.data;
      setSessions(data.results || data);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadSession = async (sessionId: number) => {
    try {
      const res = await api.get(`/chat/${sessionId}/messages/`);
      setActiveSession(res.data);
      setMessages(res.data.messages || []);
      setSidebarOpen(false);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const startNewSession = () => {
    setActiveSession(null);
    setMessages([]);
    setInput('');
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    try {
      const payload: { message: string; session_id?: number } = { message: text };
      if (activeSession) {
        payload.session_id = activeSession.id;
      }

      const res = await api.post('/chat/send/', payload);
      const data = res.data;

      const assistantMsg: Message = { role: 'assistant', content: data.assistant_message.content };
      setMessages((prev) => [...prev, assistantMsg]);

      if (!activeSession) {
        setActiveSession({
          id: data.session_id,
          title: data.session_title,
          messages: [userMsg, assistantMsg],
          last_message: assistantMsg,
          created_at: new Date().toISOString(),
        });
        loadSessions();
      }
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-full relative">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[400] lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:relative inset-y-0 left-0 z-[401] w-72 border-r border-[var(--color-border-default)] bg-[var(--color-bg-secondary)] flex flex-col transform transition-transform duration-200 ease-in-out
        lg:translate-x-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-4 border-b border-[var(--color-border-default)]">
          <Button onClick={startNewSession} className="w-full" size="sm">
            <Sparkles size={14} className="mr-1.5" />
            Новый чат
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center text-[var(--color-text-muted)] text-sm">
              Загрузка...
            </div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-[var(--color-text-muted)] text-xs">
              Нет чатов
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => loadSession(session.id)}
                className={`w-full text-left px-4 py-3 border-b border-[var(--color-border-default)] transition-colors ${
                  activeSession?.id === session.id
                    ? 'bg-[var(--color-surface-hover)]'
                    : 'hover:bg-[var(--color-surface-hover)]'
                }`}
              >
                <div className="flex items-center gap-2">
                  <MessageSquare size={14} className="text-[var(--color-accent-primary)] flex-shrink-0" />
                  <span className="text-sm text-[var(--color-text-primary)] truncate">
                    {session.title}
                  </span>
                </div>
                {session.last_message && (
                  <p className="text-xs text-[var(--color-text-muted)] mt-1 ml-6 truncate">
                    {session.last_message.content}
                  </p>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-3 sm:p-4 border-b border-[var(--color-border-default)] bg-[var(--color-bg-secondary)]">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-[var(--color-surface-hover)] transition-colors flex-shrink-0"
            >
              <MessageSquare size={18} className="text-[var(--color-text-muted)]" />
            </button>
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-accent-primary flex items-center justify-center flex-shrink-0">
              <img src="/robot-avatar.svg" alt="AI" className="w-5 h-5 sm:w-6 sm:h-6" />
            </div>
            <div className="min-w-0">
              <h3 className="font-heading font-semibold text-sm">AI Карьерный консультант</h3>
              <p className="text-xs text-[var(--color-text-muted)] hidden sm:block">Поможет составить резюме и найти работу</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[var(--color-accent-primary)]/10 flex items-center justify-center mb-3 sm:mb-4">
                <img src="/robot-avatar.svg" alt="AI" className="w-7 h-7 sm:w-8 sm:h-8" />
              </div>
              <h3 className="font-heading font-semibold text-base sm:text-lg mb-2">Привет! Я AI-ассистент</h3>
              <p className="text-xs sm:text-sm text-[var(--color-text-muted)] max-w-md">
                Я помогу вам составить резюме, найти работу или подготовиться к собеседованию.
                Задайте вопрос или расскажите о себе!
              </p>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-2 sm:gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[var(--color-accent-primary)]/15 flex items-center justify-center flex-shrink-0">
                    <img src="/robot-avatar.svg" alt="AI" className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] sm:max-w-[70%] px-3 sm:px-4 py-2.5 sm:py-3 rounded-[14px] sm:rounded-[16px] text-[13px] sm:text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-[var(--color-accent-primary)] text-white rounded-br-[4px]'
                      : 'bg-[var(--color-surface-card)] text-[var(--color-text-primary)] border border-[var(--color-border-default)] rounded-bl-[4px]'
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center flex-shrink-0">
                    <User size={12} className="text-[var(--color-text-muted)] sm:hidden" />
                    <User size={14} className="text-[var(--color-text-muted)] hidden sm:block" />
                  </div>
                )}
              </div>
            ))
          )}
          {sending && (
            <div className="flex gap-2 sm:gap-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[var(--color-accent-primary)]/15 flex items-center justify-center">
                <img src="/robot-avatar.svg" alt="AI" className="w-4 h-4" />
              </div>
              <div className="px-3 sm:px-4 py-2.5 sm:py-3 rounded-[14px] sm:rounded-[16px] bg-[var(--color-surface-card)] border border-[var(--color-border-default)]">
                <Loader2 size={14} className="animate-spin text-[var(--color-accent-primary)] sm:hidden" />
                <Loader2 size={16} className="animate-spin text-[var(--color-accent-primary)] hidden sm:block" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-3 sm:p-4 border-t border-[var(--color-border-default)] bg-[var(--color-bg-secondary)]">
          <div className="flex gap-2 sm:gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Напишите сообщение..."
              className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 rounded-[10px] sm:rounded-[12px] bg-[var(--color-surface-card)] border border-[var(--color-border-default)] text-[13px] sm:text-sm text-[var(--color-text-primary)] placeholder:text-[var(--color-text-subtle)] focus:outline-none focus:border-[var(--color-accent-primary)] focus:ring-2 focus:ring-[var(--color-accent-primary-muted)] transition-all"
              disabled={sending}
            />
            <Button onClick={sendMessage} disabled={!input.trim() || sending} className="h-10 sm:h-11">
              <Send size={14} className="sm:hidden" />
              <Send size={16} className="hidden sm:block" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
