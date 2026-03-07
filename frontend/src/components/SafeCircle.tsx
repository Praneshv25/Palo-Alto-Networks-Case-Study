import { useState, useEffect } from 'react';
import { getUsers } from '../lib/api';
import type { User } from '../types/report';

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

export default function SafeCircle({ userId }: SafeCircleProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [isSafe, setIsSafe] = useState(false);
  const [contactStatuses, setContactStatuses] = useState<Record<string, boolean>>({});

  useEffect(() => {
    getUsers().then(setUsers);
  }, []);

  const circleIds = MOCK_SAFE_CIRCLES[userId] || [];
  const contacts = users.filter(u => circleIds.includes(u.id));
  const currentUser = users.find(u => u.id === userId);

  const toggleSafe = () => {
    setIsSafe(!isSafe);
    // In a real app this would broadcast to the circle
  };

  const toggleContactStatus = (contactId: string) => {
    setContactStatuses(prev => ({
      ...prev,
      [contactId]: !prev[contactId],
    }));
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
        <div className="space-y-2">
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

      <div className="mt-6 p-3 bg-calm-100 rounded-lg text-xs text-calm-600">
        🔒 Safe Circle data is private. In production, statuses would be end-to-end encrypted and only visible to circle members.
      </div>
    </div>
  );
}
