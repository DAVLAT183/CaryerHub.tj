'use client';

import { useState, useRef, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { X, Send, Loader2, Sparkles, MessageSquare, Bot } from 'lucide-react';
import api from '@/lib/api';
import { showToast, getErrorMessage } from '@/lib/utils';
import { clsx } from '@/lib/utils';
import Button from '@/components/ui/Button';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function MiniAIChat() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    try {
      const payload: { message: string; session_id?: number } = { message: text };
      if (sessionId) {
        payload.session_id = sessionId;
      }

      const res = await api.post('/chat/send/', payload);
      const data = res.data;

      const assistantMsg: Message = { role: 'assistant', content: data.assistant_message.content };
      setMessages((prev) => [...prev, assistantMsg]);

      if (!sessionId) {
        setSessionId(data.session_id);
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
      handleSend();
    }
  };

  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (!isOpen && messages.length === 0) {
      setMessages([{ role: 'assistant', content: 'Привет! Я AI-консультант по карьере. Чем могу помочь? Могу подсказать с резюме, поиском работы или подготовкой к собеседованию.' }]);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
    setInput('');
  };

  const suggestedQuestions = [
    'Как составить резюме?',
    'Какие навыки нужны для Junior?',
    'Как подготовиться к собеседованию?',
  ];

  if (pathname === '/chat') return null;

  return (
    <div className="fixed bottom-5 right-5 z-[500]">
      {/* Chat Button */}
      {!isOpen && (
        <button
          type="button"
          onClick={toggleChat}
          className="group w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-gradient-to-br from-accent-primary to-accent-cyan text-white flex items-center justify-center shadow-[0_8px_24px_rgba(16,185,129,0.35)] hover:shadow-[0_10px_28px_rgba(16,185,129,0.45)] hover:scale-105 active:scale-95 transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2"
          aria-label="Открыть AI чат"
        >
          <img
            src="/robot-avatar.svg"
            alt=""
            aria-hidden="true"
            className="w-5 h-5 sm:w-6 sm:h-6 group-hover:rotate-12 transition-transform duration-200"
          />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          ref={containerRef}
          className="fixed sm:relative bottom-0 right-0 sm:bottom-auto sm:right-auto w-full sm:w-96 h-[100dvh] sm:h-[500px] sm:max-h-[calc(100vh-4rem)] bg-bg-primary border border-border-default sm:rounded-2xl shadow-lg flex flex-col overflow-hidden animate-scale-in"
        >
          <div className="p-3 sm:p-4 border-b border-border-default bg-bg-secondary flex items-center justify-between">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-accent-primary flex items-center justify-center">
                <img src="/robot-avatar.svg" alt="AI" className="w-5 h-5 sm:w-6 sm:h-6" />
              </div>
              <div>
                <h3 className="font-heading font-semibold text-xs sm:text-sm">AI Карьерный консультант</h3>
                <p className="text-[10px] sm:text-xs text-text-muted hidden sm:block">Поможет с резюме и поиском работы</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={clearChat}
                className="p-1.5 sm:p-2 rounded-lg hover:bg-surface-hover transition-colors text-text-muted hover:text-text-primary"
                title="Новый чат"
              >
                <Sparkles size={12} className="sm:hidden" />
                <Sparkles size={14} className="hidden sm:block" />
              </button>
              <button
                onClick={toggleChat}
                className="p-1.5 sm:p-2 rounded-lg hover:bg-surface-hover transition-colors text-text-muted hover:text-text-primary"
                title="Закрыть"
              >
                <X size={12} className="sm:hidden" />
                <X size={14} className="hidden sm:block" />
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center px-4">
                <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-accent-primary/10 flex items-center justify-center mb-3 sm:mb-4">
                  <img src="/robot-avatar.svg" alt="AI" className="w-7 h-7 sm:w-8 sm:h-8" />
                </div>
                <h3 className="font-heading font-semibold text-base sm:text-lg mb-2">Привет! Я AI-ассистент</h3>
                <p className="text-xs sm:text-sm text-text-muted max-w-md mb-4">
                  Я помогу вам составить резюме, найти работу или подготовиться к собеседованию.
                </p>
                <div className="flex flex-col gap-2 w-full max-w-xs">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => { setInput(q); }}
                      className="text-xs text-left px-3 py-2 rounded-lg border border-border-default hover:border-accent-primary/30 hover:bg-accent-primary/5 text-text-muted hover:text-text-primary transition-all"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, i) => (
                <div
                  key={i}
                  className={clsx(
                    'flex gap-2 sm:gap-3',
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  )}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-accent-primary/15 flex items-center justify-center flex-shrink-0">
                      <Bot size={12} className="text-accent-primary sm:hidden" />
                      <Bot size={14} className="text-accent-primary hidden sm:block" />
                    </div>
                  )}
                  <div
                    className={clsx(
                      'max-w-[80%] sm:max-w-[75%] px-3 sm:px-4 py-2.5 sm:py-3 rounded-[14px] sm:rounded-[16px] text-[13px] sm:text-sm leading-relaxed',
                      msg.role === 'user'
                        ? 'bg-accent-primary text-white rounded-br-[4px]'
                        : 'bg-surface-card text-text-primary border border-border-default rounded-bl-[4px]'
                    )}
                  >
                    {msg.content}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-surface-hover flex items-center justify-center flex-shrink-0">
                      <MessageSquare size={12} className="text-text-muted sm:hidden" />
                      <MessageSquare size={14} className="text-text-muted hidden sm:block" />
                    </div>
                  )}
                </div>
              ))
            )}
            {sending && (
              <div className="flex gap-2 sm:gap-3">
                <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-accent-primary/15 flex items-center justify-center">
                  <Bot size={12} className="text-accent-primary sm:hidden" />
                  <Bot size={14} className="text-accent-primary hidden sm:block" />
                </div>
                <div className="px-3 sm:px-4 py-2.5 sm:py-3 rounded-[14px] sm:rounded-[16px] bg-surface-card border border-border-default">
                  <Loader2 size={14} className="animate-spin text-accent-primary sm:hidden" />
                  <Loader2 size={16} className="animate-spin text-accent-primary hidden sm:block" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="p-3 sm:p-4 border-t border-border-default bg-bg-secondary">
            <div className="flex gap-2 sm:gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Напишите сообщение..."
                className="flex-1 px-3 sm:px-4 py-2.5 sm:py-3 rounded-[10px] sm:rounded-[12px] bg-surface-card border border-border-default text-[13px] sm:text-sm text-text-primary placeholder:text-text-subtle focus:outline-none focus:border-accent-primary focus:ring-2 focus:ring-accent-primary-muted transition-all"
                disabled={sending}
                autoFocus
              />
              <Button onClick={handleSend} disabled={!input.trim() || sending} className="h-10 sm:h-11">
                <Send size={14} className="sm:hidden" />
                <Send size={16} className="hidden sm:block" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}