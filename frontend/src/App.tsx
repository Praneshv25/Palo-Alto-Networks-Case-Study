import { useState } from 'react';
import Layout from './components/Layout';
import ReportFeed from './components/ReportFeed';
import CreateReportForm from './components/CreateReportForm';
import SafeCircle from './components/SafeCircle';

const DEFAULT_USER = 'user_002';

export default function App() {
  const [view, setView] = useState<'feed' | 'create' | 'circle'>('feed');

  return (
    <Layout currentView={view} onNavigate={setView}>
      {view === 'feed' && <ReportFeed userId={DEFAULT_USER} />}
      {view === 'create' && (
        <CreateReportForm onCreated={() => setView('feed')} />
      )}
      {view === 'circle' && <SafeCircle userId={DEFAULT_USER} />}
    </Layout>
  );
}
