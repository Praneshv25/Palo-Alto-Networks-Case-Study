import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  searchUsers,
  getMyCircleMembers,
  addCircleMember,
  removeCircleMember,
  getMyMemberships,
  getCircleMessages,
  sendCircleMessage,
} from '../lib/api';
import type { User } from '../types/report';
import type { CircleMessage, CircleMembership } from '../lib/api';

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

function ChatPanel({ circleOwnerId, userId }: { circleOwnerId: string; userId: string }) {
  const [messages, setMessages] = useState<CircleMessage[]>([]);
  const [newMsg, setNewMsg] = useState('');
  const [sending, setSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const [loading, setLoading] = useState(true);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setLoading(true);
    getCircleMessages(circleOwnerId)
      .then(setMessages)
      .catch(() => setChatError('Could not load messages.'))
      .finally(() => setLoading(false));
  }, [circleOwnerId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!newMsg.trim() || sending) return;
    setSending(true);
    setChatError('');
    try {
      const msg = await sendCircleMessage(circleOwnerId, newMsg.trim());
      setMessages(prev => [...prev, msg]);
      setNewMsg('');
    } catch {
      setChatError('Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  if (loading) return <p className="text-sm text-calm-500 py-4">Loading chat...</p>;

  return (
    <div className="bg-white rounded-xl border border-calm-200 overflow-hidden">
      <div className="h-72 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-calm-400 text-center py-8">No messages yet. Start the conversation!</p>
        )}
        {messages.map(msg => {
          const isOwn = msg.sender_id === userId;
          return (
            <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
              <div className="max-w-[75%]">
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

      {chatError && <div className="px-4 py-1 text-xs text-danger">{chatError}</div>}

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
  );
}

export default function SafeCircle({ userId }: { userId: string }) {
  const { user } = useAuth();
  const [members, setMembers] = useState<User[]>([]);
  const [memberships, setMemberships] = useState<CircleMembership[]>([]);
  const [loadingCircle, setLoadingCircle] = useState(true);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [searching, setSearching] = useState(false);

  const [openChat, setOpenChat] = useState<string | null>(null);

  useEffect(() => {
    setLoadingCircle(true);
    Promise.all([getMyCircleMembers(), getMyMemberships()])
      .then(([m, ms]) => {
        setMembers(m);
        setMemberships(ms);
      })
      .finally(() => setLoadingCircle(false));
  }, []);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    const timeout = setTimeout(() => {
      setSearching(true);
      searchUsers(searchQuery.trim())
        .then(setSearchResults)
        .finally(() => setSearching(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [searchQuery]);

  const memberIds = new Set(members.map(m => m.id));
  const filteredResults = searchResults.filter(
    u => u.id !== userId && !memberIds.has(u.id)
  );

  const handleAdd = async (contactId: string) => {
    try {
      const added = await addCircleMember(contactId);
      setMembers(prev => [...prev, added]);
      setSearchQuery('');
      setSearchResults([]);
    } catch { /* ignore */ }
  };

  const handleRemove = async (contactId: string) => {
    try {
      await removeCircleMember(contactId);
      setMembers(prev => prev.filter(m => m.id !== contactId));
    } catch { /* ignore */ }
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-calm-900 mb-1">Safe Circle</h2>
      <p className="text-sm text-calm-600 mb-5">
        Your trusted contacts. Add people you trust and chat with your circle.
      </p>

      {/* Section A: My Safe Circle */}
      <h3 className="text-sm font-semibold text-calm-800 mb-3">My Safe Circle</h3>

      {/* Search to add */}
      <div className="relative mb-4">
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search users to add..."
          className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
        />
        {searchQuery.trim() && (
          <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-white border border-calm-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
            {searching && (
              <p className="text-xs text-calm-500 p-3">Searching...</p>
            )}
            {!searching && filteredResults.length === 0 && (
              <p className="text-xs text-calm-500 p-3">No users found.</p>
            )}
            {filteredResults.map(u => (
              <button
                key={u.id}
                onClick={() => handleAdd(u.id)}
                className="w-full text-left px-3 py-2 hover:bg-calm-50 flex items-center justify-between gap-2 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 bg-calm-200 rounded-full flex items-center justify-center text-xs font-medium text-calm-700">
                    {u.username.charAt(0)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-calm-800">{u.username}</p>
                    <p className="text-xs text-calm-500">{u.neighborhood}</p>
                  </div>
                </div>
                <span className="text-xs text-calm-500">+ Add</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {loadingCircle ? (
        <p className="text-sm text-calm-500">Loading circle...</p>
      ) : members.length === 0 ? (
        <p className="text-sm text-calm-500 mb-4">No one in your circle yet. Search above to add people.</p>
      ) : (
        <div className="space-y-2 mb-4">
          {members.map(contact => (
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
                onClick={() => handleRemove(contact.id)}
                className="text-xs text-calm-400 hover:text-red-500 transition-colors"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      {/* My circle chat */}
      <h4 className="text-xs font-semibold text-calm-700 mb-2 uppercase tracking-wide">My Circle Chat</h4>
      <ChatPanel circleOwnerId={userId} userId={userId} />

      {/* Section B: Circles I'm In */}
      <h3 className="text-sm font-semibold text-calm-800 mt-8 mb-3">Circles I'm In</h3>
      {memberships.length === 0 ? (
        <p className="text-sm text-calm-500">You haven't been added to any other circles yet.</p>
      ) : (
        <div className="space-y-2">
          {memberships.map(m => (
            <div key={m.owner_id}>
              <button
                onClick={() => setOpenChat(openChat === m.owner_id ? null : m.owner_id)}
                className="w-full bg-white rounded-lg border border-calm-200 p-3 flex items-center justify-between hover:bg-calm-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-calm-300 rounded-full flex items-center justify-center text-sm font-medium text-calm-800">
                    {m.owner_name.charAt(0)}
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-medium text-calm-800">{m.owner_name}'s Circle</p>
                    <p className="text-xs text-calm-500">{m.owner_neighborhood}</p>
                  </div>
                </div>
                <span className={`text-xs text-calm-400 transition-transform ${openChat === m.owner_id ? 'rotate-90' : ''}`}>
                  ▸
                </span>
              </button>
              {openChat === m.owner_id && (
                <div className="mt-2 mb-2">
                  <ChatPanel circleOwnerId={m.owner_id} userId={userId} />
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 p-3 bg-calm-100 rounded-lg text-xs text-calm-600">
        🔒 Safe Circle data is private. In production, statuses would be end-to-end encrypted and only visible to circle members.
      </div>
    </div>
  );
}
