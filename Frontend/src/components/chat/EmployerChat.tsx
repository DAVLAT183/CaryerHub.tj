'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, User as UserIcon, Building2, ArrowLeft, MessageSquare } from 'lucide-react';
import api from '@/lib/api';
import Button from '@/components/ui/Button';
import { showToast, getErrorMessage, mediaUrl } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { useWebSocket } from '@/hooks/useWebSocket';

interface User {
  id: number;
  username: string;
  email: string;
  avatar: string | null;
  role: string;
}

interface DirectMessage {
  id: number;
  sender_id: number | null;
  recipient_id: number | null;
  content: string;
  created_at: string;
  is_read: boolean;
}

interface Conversation {
  user: User;
  last_message: DirectMessage | null;
  unread_count: number;
}

interface EmployerChatProps {
  initialUserId?: number;
}

export default function EmployerChat({ initialUserId }: EmployerChatProps) {
  const { user, loading: authLoading } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeUser, setActiveUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<DirectMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleWsMessage = useCallback((data: Record<string, unknown>) => {
    if (data.type === 'chat_message' && activeUser && data.sender_id === activeUser.id) {
      const newMsg: DirectMessage = {
        id: Date.now(),
        sender_id: data.sender_id as number,
        recipient_id: user?.id || 0,
        content: data.message as string,
        created_at: new Date().toISOString(),
        is_read: false,
      };
      setMessages((prev) => [...prev, newMsg]);
    }
  }, [activeUser, user]);

  const roomName = activeUser && user ? [Math.min(user.id, activeUser.id), Math.max(user.id, activeUser.id)].join('_') : '';
  const { isConnected } = useWebSocket({
    path: `/ws/chat/${roomName}/`,
    onMessage: handleWsMessage,
    enabled: !!activeUser && !!user,
  });

  const isStudent = user?.role === 'student';
  const otherRoleLabel = isStudent ? 'Работодатель' : 'Студент';
  const headerLabel = isStudent ? 'Чат с работодателями' : 'Чат со студентами';

  useEffect(() => {
    if (!authLoading) {
      loadConversations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const partnersPath = isStudent ? '/messages/employers/' : '/messages/students/';
      const [convRes, partnersRes] = await Promise.all([
        api.get('/messages/conversations/'),
        api.get(partnersPath).catch(() => ({ data: [] as User[] })),
      ]);

      const merged: Conversation[] = [...convRes.data];
      const knownIds = new Set(merged.map((c) => c.user.id));

      for (const partner of partnersRes.data as User[]) {
        if (!knownIds.has(partner.id)) {
          merged.push({ user: partner, last_message: null, unread_count: 0 });
          knownIds.add(partner.id);
        }
      }

      setConversations(merged);

      if (initialUserId) {
        const conv = merged.find((c) => c.user.id === initialUserId);
        if (conv) {
          openChat(conv.user);
        } else {
          try {
            const userRes = await api.get(`/users/${initialUserId}/`);
            openChat(userRes.data);
          } catch {
            setActiveUser({ id: initialUserId, username: otherRoleLabel, email: '', avatar: null, role: isStudent ? 'employer' : 'student' });
          }
        }
      }
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setLoading(false);
    }
  };

  const openChat = async (user: User) => {
    setActiveUser(user);
    try {
      const res = await api.get(`/messages/${user.id}/`);
      setMessages(res.data);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || !activeUser || sending) return;

    setSending(true);
    setInput('');

    try {
      const res = await api.post(`/messages/${activeUser.id}/`, { content: text });
      setMessages((prev) => [...prev, res.data]);
      loadConversations();
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
      setInput(text);
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

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  if (activeUser) {
    return (
      <div className="flex flex-col h-full">
        <div className="p-3 sm:p-4 border-b border-[var(--color-border-default)] bg-[var(--color-bg-secondary)]">
          <div className="flex items-center gap-2 sm:gap-3">
            <button
              onClick={() => { setActiveUser(null); setMessages([]); }}
              className="p-1.5 sm:p-2 rounded-full hover:bg-[var(--color-surface-hover)] transition-colors flex-shrink-0"
            >
              <ArrowLeft size={16} className="text-[var(--color-text-muted)] sm:hidden" />
              <ArrowLeft size={18} className="text-[var(--color-text-muted)] hidden sm:block" />
            </button>
            <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center flex-shrink-0">
              {activeUser.avatar ? (
                <img src={mediaUrl(activeUser.avatar)} alt="" className="w-full h-full rounded-full object-cover" />
              ) : isStudent ? (
                <Building2 size={14} className="text-[var(--color-text-muted)] sm:hidden" />
              ) : (
                <UserIcon size={14} className="text-[var(--color-text-muted)] sm:hidden" />
              )}
              {activeUser.avatar ? null : isStudent ? (
                <Building2 size={16} className="text-[var(--color-text-muted)] hidden sm:block" />
              ) : (
                <UserIcon size={16} className="text-[var(--color-text-muted)] hidden sm:block" />
              )}
            </div>
            <div className="min-w-0">
              <h3 className="font-heading font-semibold text-xs sm:text-sm truncate">{activeUser.username}</h3>
              <p className="text-[10px] sm:text-xs text-[var(--color-text-muted)]">{otherRoleLabel}</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center mb-2 sm:mb-3">
                <MessageSquare size={18} className="text-[var(--color-text-muted)] sm:hidden" />
                <MessageSquare size={22} className="text-[var(--color-text-muted)] hidden sm:block" />
              </div>
              <p className="text-xs sm:text-sm text-[var(--color-text-muted)]">Начните разговор</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.sender_id === activeUser.id ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-[80%] sm:max-w-[70%] px-3 sm:px-4 py-2.5 sm:py-3 rounded-[14px] sm:rounded-[16px] text-[13px] sm:text-sm leading-relaxed ${
                    msg.sender_id === activeUser.id
                      ? 'bg-[var(--color-surface-card)] text-[var(--color-text-primary)] border border-[var(--color-border-default)] rounded-bl-[4px]'
                      : 'bg-[var(--color-accent-primary)] text-white rounded-br-[4px]'
                  }`}
                >
                  <p>{msg.content}</p>
                  <p className={`text-[9px] sm:text-[10px] mt-1 ${msg.sender_id === activeUser.id ? 'text-[var(--color-text-muted)]' : 'text-white/70'}`}>
                    {formatTime(msg.created_at)}
                  </p>
                </div>
              </div>
            ))
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
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-[var(--color-border-default)] bg-[var(--color-bg-secondary)]">
        <h3 className="font-heading font-semibold">{headerLabel}</h3>
        <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{isStudent ? 'Откликнитесь на вакансию, чтобы начать чат' : 'Студенты напишут вам после отклика'}</p>
      </div>
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center text-[var(--color-text-muted)] text-sm">Загрузка...</div>
        ) : conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Building2 size={36} className="text-[var(--color-text-muted)] mb-3" />
            <p className="text-sm text-[var(--color-text-muted)]">Нет диалогов</p>
            <p className="text-xs text-[var(--color-text-subtle)] mt-1">{isStudent ? 'Откликнитесь на вакансию, чтобы начать чат' : 'Студенты напишут вам после отклика'}</p>
          </div>
        ) : (
          conversations.map((conv) => (
            <button
              key={conv.user.id}
              onClick={() => openChat(conv.user)}
              className="w-full text-left px-4 py-4 border-b border-[var(--color-border-default)] hover:bg-[var(--color-surface-hover)] transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[var(--color-surface-hover)] flex items-center justify-center flex-shrink-0">
                  {conv.user.avatar ? (
                    <img src={mediaUrl(conv.user.avatar)} alt="" className="w-full h-full rounded-full object-cover" />
                  ) : isStudent ? (
                    <Building2 size={16} className="text-[var(--color-text-muted)]" />
                  ) : (
                    <UserIcon size={16} className="text-[var(--color-text-muted)]" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-sm text-[var(--color-text-primary)]">
                      {conv.user.username}
                    </span>
                    {conv.unread_count > 0 && (
                      <span className="w-5 h-5 rounded-full bg-[var(--color-accent-primary)] text-white text-[10px] font-bold flex items-center justify-center">
                        {conv.unread_count}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--color-text-muted)] truncate mt-0.5">
                    {conv.last_message
                      ? conv.last_message.content
                      : isStudent
                        ? 'Напишите первым'
                        : 'Напишите студенту'}
                  </p>
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
}
