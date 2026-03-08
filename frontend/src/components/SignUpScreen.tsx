import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

interface SignUpScreenProps {
  onBackToLogin: () => void;
}

export default function SignUpScreen({ onBackToLogin }: SignUpScreenProps) {
  const { signup } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [neighborhood, setNeighborhood] = useState('');
  const [locationStatus, setLocationStatus] = useState<'idle' | 'acquiring' | 'granted' | 'denied'>('idle');
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('denied');
      return;
    }
    setLocationStatus('acquiring');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocationStatus('granted');
      },
      () => setLocationStatus('denied'),
      { timeout: 10000 }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username.trim()) { setError('Username is required.'); return; }
    if (username.trim().length < 3) { setError('Username must be at least 3 characters.'); return; }
    if (!password) { setError('Password is required.'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return; }
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    if (!neighborhood.trim()) { setError('Neighborhood is required.'); return; }

    setSubmitting(true);
    try {
      await signup({
        username: username.trim().toLowerCase(),
        password,
        neighborhood: neighborhood.trim(),
        lat: coords?.lat ?? null,
        lng: coords?.lng ?? null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sign up failed');
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
          <h1 className="text-2xl font-bold text-calm-900">Join Community Guardian</h1>
          <p className="text-sm text-calm-600 mt-1">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-calm-200 shadow-sm p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-calm-800 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
              placeholder="min. 3 characters"
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
              placeholder="min. 6 characters"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-calm-800 mb-1">Confirm Password</label>
            <input
              type="password"
              value={confirm}
              onChange={e => setConfirm(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
              placeholder="Repeat password"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-calm-800 mb-1">Neighborhood</label>
            <input
              type="text"
              value={neighborhood}
              onChange={e => setNeighborhood(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400"
              placeholder="e.g. Downtown, North PA"
            />
          </div>

          {/* Location section */}
          <div className="rounded-lg border border-calm-200 p-3 space-y-2">
            <p className="text-sm font-medium text-calm-800">Location <span className="text-calm-500 font-normal">(optional)</span></p>
            <p className="text-xs text-calm-500">Used to show nearby alerts. Never shared publicly.</p>
            {locationStatus === 'idle' && (
              <button
                type="button"
                onClick={requestLocation}
                className="w-full text-sm px-3 py-2 rounded-lg border border-calm-300 text-calm-700 hover:bg-calm-50 transition-colors flex items-center justify-center gap-2"
              >
                <span>📍</span> Use my current location
              </button>
            )}
            {locationStatus === 'acquiring' && (
              <p className="text-xs text-calm-500 text-center py-1">Acquiring location…</p>
            )}
            {locationStatus === 'granted' && coords && (
              <div className="flex items-center gap-2 text-xs text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                <span>✓</span>
                <span>Location captured ({coords.lat.toFixed(4)}, {coords.lng.toFixed(4)})</span>
              </div>
            )}
            {locationStatus === 'denied' && (
              <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                Location access denied — you can update it later in settings.
              </p>
            )}
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
            {submitting ? 'Creating account…' : 'Create Account'}
          </button>
        </form>

        <p className="text-center text-sm text-calm-600 mt-4">
          Already have an account?{' '}
          <button
            onClick={onBackToLogin}
            className="text-calm-800 font-medium hover:underline"
          >
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
