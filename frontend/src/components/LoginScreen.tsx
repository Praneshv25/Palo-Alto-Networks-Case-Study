import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface LoginScreenProps {
  onSignUp: () => void;
}

export default function LoginScreen({ onSignUp }: LoginScreenProps) {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.');
      return;
    }
    setSubmitting(true);
    try {
      await login(username.trim(), password.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-calm-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="w-14 h-14 bg-calm-600 rounded-xl flex items-center justify-center text-2xl mx-auto mb-3">
            🛡️
          </div>
          <h1 className="text-2xl font-bold text-calm-900">Community Guardian</h1>
          <p className="text-sm text-calm-600 mt-1">Sign in to continue</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-calm-200 shadow-sm p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-calm-800 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
              placeholder="e.g. maria"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-calm-800 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
              placeholder="Enter password"
            />
          </div>

          {error && (
            <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full px-4 py-2 bg-calm-600 text-white text-sm font-medium rounded-lg hover:bg-calm-700 transition-colors disabled:opacity-50"
          >
            {submitting ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-sm text-calm-600 mt-4">
          New here?{' '}
          <button
            onClick={onSignUp}
            className="text-calm-800 font-medium hover:underline"
          >
            Create an account
          </button>
        </p>

        <div className="mt-4 p-3 bg-calm-100 rounded-lg text-xs text-calm-600">
          <p className="font-medium mb-1">Demo accounts:</p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
            <span>maria / pass123</span>
            <span>jake / pass456</span>
            <span>aisha / pass789</span>
            <span>tom / admin123</span>
            <span>lily / pass321</span>
          </div>
        </div>
      </div>
    </div>
  );
}
