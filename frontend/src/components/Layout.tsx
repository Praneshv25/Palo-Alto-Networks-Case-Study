import { type ReactNode, useEffect, useState } from 'react';
import { healthCheck } from '../lib/api';

interface LayoutProps {
  children: ReactNode;
  currentView: 'feed' | 'create' | 'circle';
  onNavigate: (view: 'feed' | 'create' | 'circle') => void;
}

export default function Layout({ children, currentView, onNavigate }: LayoutProps) {
  const [aiStatus, setAiStatus] = useState<string>('checking');

  useEffect(() => {
    healthCheck()
      .then(h => setAiStatus(h.ai_service))
      .catch(() => setAiStatus('error'));
  }, []);

  return (
    <div className="min-h-screen bg-calm-50">
      <header className="bg-gradient-to-r from-calm-700 to-calm-600 text-white shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-lg flex items-center justify-center text-lg">
              🛡️
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Community Guardian</h1>
              <p className="text-calm-200 text-xs">Noise to Signal. Panic to Action.</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`inline-block w-2 h-2 rounded-full ${
              aiStatus === 'connected' ? 'bg-green-300' :
              aiStatus === 'checking' ? 'bg-yellow-300 animate-pulse' : 'bg-red-300'
            }`} />
            <span className="text-xs text-calm-200">
              AI {aiStatus === 'connected' ? 'Online' : aiStatus === 'checking' ? '...' : 'Offline'}
            </span>
          </div>
        </div>
        <nav className="max-w-5xl mx-auto px-4 flex gap-1 pb-0">
          {([
            ['feed', 'Signal Feed'],
            ['create', 'Report Incident'],
            ['circle', 'Safe Circle'],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => onNavigate(key)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
                currentView === key
                  ? 'bg-calm-50 text-calm-800'
                  : 'text-calm-200 hover:bg-white/10'
              }`}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-6">
        {children}
      </main>
    </div>
  );
}
