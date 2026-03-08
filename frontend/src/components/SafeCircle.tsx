import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  getUsers,
  getCircleMessages,
  sendCircleMessage,
  getCircleRequests,
  handleCircleRequest,
} from '../lib/api';
import type { User } from '../types/report';
import type { CircleMessage, CircleRequest } from '../lib/api';

interface SafeCircleProps {
  userId: string;
}

const MOCK_SAFE_CIRCLES: Record<string, string[]> = {
  user_001: ['user_002', 'user_003'],
  user_002: ['user_001', 'user_005'],
  user_003: ['user_001', 'user_004'],
  user_004: ['user_003'],
  user_005: ['user_002'],
};

const CIRCLE_OWNER = 'user_001';

function formatTime(iso: string): string {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function SafeCircle({ userId }: SafeCircleProps) {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [isSafe, setIsSafe] = useState(false);
  const [contactStatuses, setContactStatuses] = useState<Record<string, boolean>>({});

  const [messages, setMessages] = useState<CircleMessage[]>([]);
  const [newMsg, setNewMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const [isMember, setIsMember] = useState(false);
  const [loadingChat, setLoadingChat] = useState(true);

  const [requests, setRequests] = useState<CircleRequest[]>([]);

  const chatEndRef = useRef<HTMLDivElement>(null);

  const isAdmin = user?.role === 'Admin';

  useEffect(() => {
    getUsers().then(setUsers);
  }, []);

  useEffect(() => {
    setLoadingChat(true);
    getCircleMessages(CIRCLE_OWNER)
      .then(msgs => {
        setMessages(msgs);
        setIsMember(true);
      })
      .catch(() => {
        setIsMember(false);
      })
      .finally(() => setLoadingChat(false));

    if (isAdmin) {
      getCircleRequests(CIRCLE_OWNER).then(setRequests).catch(() => {});
    }
  }, [isAdmin]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const circleIds = MOCK_SAFE_CIRCLES[userId] || [];
  const contacts = users.filter(u => circleIds.includes(u.id));
  const currentUser = users.find(u => u.id === userId);

  const toggleSafe = () => setIsSafe(!isSafe);

  const toggleContactStatus = (contactId: string) => {
    setContactStatuses(prev => ({ ...prev, [contactId]: !prev[contactId] }));
  };

  const handleSend = async () => {
    if (!newMsg.trim() || sending) return;
    setSending(true);
    setChatError('');
    try {
      const msg = await sendCircleMessage(CIRCLE_OWNER, newMsg.trim());
      setMessages(prev => [...prev, msg]);
      setNewMsg('');
    } catch {
      setChatError('Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  const handleApprove = async (reqId: string) => {
    try {
      await handleCircleRequest(CIRCLE_OWNER, reqId, 'approved');
      setRequests(prev => prev.filter(r => r.id !== reqId));
    } catch { /* ignore */ }
  };

  const handleDeny = async (reqId: string) => {
    try {
      await handleCircleRequest(CIRCLE_OWNER, reqId, 'denied');
      setRequests(prev => prev.filter(r => r.id !== reqId));
    } catch { /* ignore */ }
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-calm-900 mb-1">Safe Circle</h2>
      <p className="text-sm text-calm-600 mb-5">
        Share your status with trusted contacts. Only members of your circle can see your updates.
      </p>

      {/* Current user status */}
      <div className="bg-white rounded-xl border border-calm-200 p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-calm-800">
              {currentUser?.username || 'You'}
            </p>
            <p className="text-xs text-calm-500">{currentUser?.neighborhood}</p>
          </div>
          <button
            onClick={toggleSafe}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
              isSafe
                ? 'bg-green-100 text-green-700 border border-green-300 shadow-sm'
                : 'bg-calm-100 text-calm-600 border border-calm-200 hover:bg-calm-200'
            }`}
          >
            {isSafe ? '✓ I\'m Safe' : 'Mark as Safe'}
          </button>
        </div>
      </div>

      {/* Trusted contacts */}
      <h3 className="text-sm font-semibold text-calm-800 mb-3">
        Trusted Contacts ({contacts.length})
      </h3>
      {contacts.length === 0 ? (
        <p className="text-sm text-calm-500">No contacts in your Safe Circle.</p>
      ) : (
        <div className="space-y-2 mb-6">
          {contacts.map(contact => (
            <div
              key={contact.id}
              className="bg-white rounded-lg border border-calm-200 p-3 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-calm-200 rounded-full flex items-center justify-center text-sm font-medium text-calm-700">
                  {contact.username.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-medium text-calm-800">{contact.username}</p>
                  <p className="text-xs text-calm-500">{contact.neighborhood}</p>
                </div>
              </div>
              <button
                onClick={() => toggleContactStatus(contact.id)}
                className="text-xs text-calm-500 hover:text-calm-700"
              >
                {contactStatuses[contact.id] ? (
                  <span className="text-green-600 font-medium">Safe ✓</span>
                ) : (
                  <span className="text-calm-400">Status unknown</span>
                )}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Admin: Pending join requests */}
      {isAdmin && requests.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-calm-800 mb-3">
            Pending Requests ({requests.length})
          </h3>
          <div className="space-y-2">
            {requests.map(req => (
              <div
                key={req.id}
                className="bg-white rounded-lg border border-calm-200 p-3 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center text-sm font-medium text-amber-700">
                    {req.requester_name.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-calm-800">{req.requester_name}</p>
                    <p className="text-xs text-calm-500">{formatTime(req.created_at)}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleApprove(req.id)}
                    className="text-xs font-medium px-3 py-1 rounded bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleDeny(req.id)}
                    className="text-xs font-medium px-3 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                  >
                    Deny
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Group Chat */}
      <h3 className="text-sm font-semibold text-calm-800 mb-3">Group Chat</h3>
      {loadingChat ? (
        <p className="text-sm text-calm-500">Loading chat...</p>
      ) : !isMember ? (
        <div className="bg-white rounded-xl border border-calm-200 p-6 text-center">
          <p className="text-sm text-calm-600 mb-3">You are not a member of this circle's chat.</p>
          <p className="text-xs text-calm-400">Contact an admin to request access.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-calm-200 overflow-hidden">
          <div className="h-80 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <p className="text-sm text-calm-400 text-center py-8">No messages yet.</p>
            )}
            {messages.map(msg => {
              const isOwn = msg.sender_id === userId;
              return (
                <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[75%] ${isOwn ? 'order-2' : ''}`}>
                    {!isOwn && (
                      <p className="text-xs font-medium text-calm-600 mb-0.5">{msg.sender_name}</p>
                    )}
                    <div
                      className={`px-3 py-2 rounded-lg text-sm ${
                        isOwn
                          ? 'bg-calm-600 text-white rounded-br-sm'
                          : 'bg-calm-100 text-calm-800 rounded-bl-sm'
                      }`}
                    >
                      {msg.content}
                    </div>
                    <p className={`text-[10px] text-calm-400 mt-0.5 ${isOwn ? 'text-right' : ''}`}>
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </div>
              );
            })}
            <div ref={chatEndRef} />
          </div>

          {chatError && (
            <div className="px-4 py-1 text-xs text-danger">{chatError}</div>
          )}

          <div className="border-t border-calm-200 p-3 flex gap-2">
            <input
              type="text"
              value={newMsg}
              onChange={e => setNewMsg(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
              maxLength={2000}
            />
            <button
              onClick={handleSend}
              disabled={sending || !newMsg.trim()}
              className="px-4 py-2 bg-calm-600 text-white text-sm font-medium rounded-lg hover:bg-calm-700 transition-colors disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      )}

      <div className="mt-6 p-3 bg-calm-100 rounded-lg text-xs text-calm-600">
        🔒 Safe Circle data is private. In production, statuses would be end-to-end encrypted and only visible to circle members.
      </div>
    </div>
  );
}
