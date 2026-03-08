import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import EventTicker from './components/EventTicker';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import ApprovalModal from './components/ApprovalModal';
import { ApprovalProvider, useApproval } from './context/ApprovalContext';
import { Activity } from 'lucide-react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Simulation = lazy(() => import('./pages/Simulation'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <Activity className="w-8 h-8 text-amber animate-spin" />
    </div>
  );
}

function GlobalApprovalModal() {
  const { showModal, setShowModal } = useApproval();
  if (!showModal) return null;
  return <ApprovalModal onClose={() => setShowModal(false)} />;
}

export default function App() {
  return (
    <ApprovalProvider>
    <div className="h-screen w-screen flex bg-bg text-text font-outfit overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Event Ticker */}
        <EventTicker />

        {/* Navbar */}
        <Navbar />

        {/* Content */}
        <main className="flex-1 overflow-hidden">
          <Suspense fallback={<LoadingFallback />}>
            <Routes>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/simulation" element={<Simulation />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>

        {/* Footer Status Bar */}
        <Footer />
      </div>

      {/* Global Approval Modal */}
      <GlobalApprovalModal />
    </div>
    </ApprovalProvider>
  );
}
