'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, X, FileText } from 'lucide-react';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import { showToast, getErrorMessage } from '@/lib/utils';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ResumeGeneratorModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function ResumeGeneratorModal({ open, onClose, onCreated }: ResumeGeneratorModalProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [resumeData, setResumeData] = useState<Record<string, unknown> | null>(null);
  const [saving, setSaving] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: 'Привет! Я помогу вам создать резюме. Давайте начнём!\n\nНа какую должность вы претендуете? (например: Junior Frontend Developer, Python Developer, SMM-менеджер)',
      }]);
    }
  }, [open]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    setSending(true);
    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');

    try {
      const history = [...messages, userMsg].map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await api.post('/ai/resume-chat/', {
        message: text,
        history: history.slice(0, -1),
      });

      const data = res.data;
      const assistantMsg: Message = { role: 'assistant', content: data.message };
      setMessages((prev) => [...prev, assistantMsg]);

      if (data.resume_data) {
        setResumeData(data.resume_data);
        showToast('Резюме сгенерировано!', 'success');
      }
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
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

  const saveResume = async () => {
    if (!resumeData) return;
    setSaving(true);
    try {
      await api.post('/resumes/', {
        title: resumeData.title || 'Резюме',
        about: resumeData.about || '',
        skills: resumeData.skills || [],
        schedule_type: resumeData.schedule_type || 'flexible',
        work_format: resumeData.work_format || 'online',
      });
      showToast('Резюме сохранено!', 'success');
      onCreated();
      handleClose();
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    setMessages([]);
    setInput('');
    setResumeData(null);
    setSending(false);
    setSaving(false);
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={handleClose} />
      <div className="relative z-10 w-full max-w-xl mx-4 h-[85vh] bg-surface-card rounded-2xl border border-border-default shadow-xl flex flex-col animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-default">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent-primary/10 flex items-center justify-center">
              <FileText size={18} className="text-accent-primary" />
            </div>
            <div>
              <h2 className="font-heading font-semibold text-sm">Создание резюме с ИИ</h2>
              <p className="text-[11px] text-text-muted">ИИ задаст вопросы и создаст резюме</p>
            </div>
          </div>
          <button onClick={handleClose} className="p-2 rounded-lg hover:bg-surface-hover transition-colors text-text-muted">
            <X size={18} />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-accent-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot size={14} className="text-accent-primary" />
                </div>
              )}
              <div className={`max-w-[80%] px-4 py-2.5 rounded-2xl text-[13px] leading-relaxed whitespace-pre-line ${
                msg.role === 'user'
                  ? 'bg-accent-primary text-white rounded-br-md'
                  : 'bg-surface-hover text-text-primary border border-border-default rounded-bl-md'
              }`}>
                {msg.content}
              </div>
              {msg.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-surface-hover flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User size={14} className="text-text-muted" />
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="flex gap-2.5">
              <div className="w-8 h-8 rounded-full bg-accent-primary/10 flex items-center justify-center">
                <Bot size={14} className="text-accent-primary" />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-surface-hover border border-border-default rounded-bl-md">
                <Loader2 size={14} className="animate-spin text-accent-primary" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Resume preview + save button */}
        {resumeData && (
          <div className="mx-5 mb-3 p-4 rounded-xl bg-accent-primary/5 border border-accent-primary/20">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles size={14} className="text-accent-primary" />
              <span className="text-[13px] font-semibold text-accent-primary">Резюме готово!</span>
            </div>
            <p className="text-[12px] text-text-muted mb-1"><b>Должность:</b> {String(resumeData.title)}</p>
            <p className="text-[12px] text-text-muted mb-1"><b>Навыки:</b> {Array.isArray(resumeData.skills) ? resumeData.skills.join(', ') : ''}</p>
            <p className="text-[12px] text-text-muted mb-3"><b>График:</b> {String(resumeData.schedule_type)} | <b>Формат:</b> {String(resumeData.work_format)}</p>
            <Button onClick={saveResume} loading={saving} className="w-full" size="sm">
              <Sparkles size={14} className="mr-1" />
              Сохранить резюме
            </Button>
          </div>
        )}

        {/* Input */}
        {!resumeData && (
          <div className="px-5 pb-4 pt-2 border-t border-border-default">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ответьте на вопрос ИИ..."
                className="flex-1 px-4 py-2.5 rounded-xl bg-surface-hover border border-border-default text-[13px] text-text-primary placeholder:text-text-subtle focus:outline-none focus:border-accent-primary transition-all"
                disabled={sending}
                autoFocus
              />
              <Button onClick={sendMessage} disabled={!input.trim() || sending} className="px-3">
                <Send size={16} />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
