import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { Analytics } from './components/Analytics';
import { Transcripts } from './components/Transcripts';
import { Settings } from './components/Settings';

export default function App() {
  return (
    <div className="flex h-screen bg-black text-white">
      <Sidebar />
      
      <main className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <div className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/transcripts" element={<Transcripts />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
