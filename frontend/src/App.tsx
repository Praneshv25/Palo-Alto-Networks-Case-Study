import { useState } from 'react';
import { useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import ReportFeed from './components/ReportFeed';
import CreateReportForm from './components/CreateReportForm';
import SafeCircle from './components/SafeCircle';
import LoginScreen from './components/LoginScreen';

export default function App() {
  const { user, loading } = useAuth();
  const [view, setView] = useState<'feed' | 'create' | 'circle'>('feed');

  if (loading) {
    return (
      <div className="min-h-screen bg-calm-50 flex items-center justify-center">
        <p className="text-calm-500 text-sm">Loading...</p>
      </div>
    );
  }

  if (!user) return <LoginScreen />;

  return (
    <Layout currentView={view} onNavigate={setView}>
      {view === 'feed' && <ReportFeed userId={user.id} />}
      {view === 'create' && (
        <CreateReportForm onCreated={() => setView('feed')} />
      )}
      {view === 'circle' && <SafeCircle userId={user.id} />}
    </Layout>
  );
}
