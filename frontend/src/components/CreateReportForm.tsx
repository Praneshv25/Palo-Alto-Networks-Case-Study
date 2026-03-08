import { useState } from 'react';
import type { SafetyReport } from '../types/report';
import { createReport } from '../lib/api';
import TrustBadge from './TrustBadge';
import { useAuth } from '../context/AuthContext';

interface CreateReportFormProps {
  onCreated: () => void;
}

export default function CreateReportForm({ onCreated }: CreateReportFormProps) {
  const { user } = useAuth();
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<'local' | 'digital'>('local');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<SafetyReport | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (!content.trim()) {
      setError('Please describe the incident.');
      return;
    }

    setSubmitting(true);
    try {
      const report = await createReport({
        content: content.trim(),
        category,
        author_id: user!.id,
      });
      setResult(report);
      setContent('');
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-calm-900 mb-1">Report an Incident</h2>
      <p className="text-sm text-calm-600 mb-5">
        Describe what you observed. Our AI will transform your report into a calm, actionable alert for the community.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-calm-800 mb-1">
            What happened? <span className="text-danger">*</span>
          </label>
          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            rows={4}
            placeholder="Describe the incident in your own words..."
            className="w-full px-3 py-2 text-sm border border-calm-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-calm-400 resize-y"
            maxLength={5000}
          />
          <div className="text-xs text-calm-400 text-right mt-1">{content.length} / 5000</div>
        </div>

        <div>
          <label className="block text-sm font-medium text-calm-800 mb-2">
            Category <span className="text-danger">*</span>
          </label>
          <div className="flex gap-3">
            <label className={`flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer transition-colors ${
              category === 'local' ? 'bg-calm-100 border-calm-400 text-calm-800' : 'bg-white border-calm-200 text-calm-600'
            }`}>
              <input
                type="radio"
                name="category"
                value="local"
                checked={category === 'local'}
                onChange={() => setCategory('local')}
                className="sr-only"
              />
              🏘️ Local Safety
            </label>
            <label className={`flex items-center gap-2 px-4 py-2 rounded-lg border cursor-pointer transition-colors ${
              category === 'digital' ? 'bg-calm-100 border-calm-400 text-calm-800' : 'bg-white border-calm-200 text-calm-600'
            }`}>
              <input
                type="radio"
                name="category"
                value="digital"
                checked={category === 'digital'}
                onChange={() => setCategory('digital')}
                className="sr-only"
              />
              🔒 Digital Defense
            </label>
          </div>
        </div>

        <p className="text-sm text-calm-600">
          Reporting as <span className="font-medium text-calm-800">{user?.username}</span>
        </p>

        {error && (
          <div className="text-sm text-danger bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="px-6 py-2 bg-calm-600 text-white text-sm font-medium rounded-lg hover:bg-calm-700 transition-colors disabled:opacity-50"
        >
          {submitting ? 'Processing with AI...' : 'Submit Report'}
        </button>
      </form>

      {result && (
        <div className="mt-6 p-4 bg-calm-100 border border-calm-300 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-semibold text-calm-800">AI-Processed Report</span>
            <TrustBadge trustLabel={result.trustLabel} />
          </div>
          <h3 className="text-base font-semibold text-calm-900 mb-1">{result.title}</h3>
          <p className="text-sm text-calm-700 mb-2">{result.summary}</p>
          <p className="text-xs font-medium text-calm-600 mb-1">Action Checklist:</p>
          <ol className="list-decimal list-inside text-sm text-calm-700 space-y-0.5">
            {result.checklist.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
