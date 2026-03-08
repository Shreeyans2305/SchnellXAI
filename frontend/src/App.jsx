import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import EventTicker from './components/EventTicker';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';
import ApprovalModal from './components/ApprovalModal';
import { ApprovalProvider, useApproval } from './context/ApprovalContext';
import { Activity, Bell } from 'lucide-react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Simulation = lazy(() => import('./pages/Simulation'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <Activity className="w-8 h-8 text-amber animate-spin" />
    </div>
  );
}

function GlobalApprovalBanner() {
  const { pendingApproval, setShowModal } = useApproval();
  if (!pendingApproval) return null;
  return (
    <button
      onClick={() => setShowModal(true)}
      className="w-full flex items-center gap-3 bg-amber/5 border-b border-amber/20 px-5 py-3 hover:bg-amber/10 transition-colors text-left group"
    >
      <div className="w-8 h-8 bg-amber/20 rounded-xl flex items-center justify-center shrink-0 animate-pulse">
        <Bell className="w-4 h-4 text-amber" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold text-amber">Pending Approval — Decider Agent</div>
        <div className="text-xs text-muted mt-0.5 truncate">{pendingApproval.action || 'Action requires human authorization'}</div>
      </div>
      <span className="text-xs text-amber border border-amber/30 px-3 py-1.5 rounded-xl font-medium group-hover:bg-amber group-hover:text-white transition-colors shrink-0">
        Review
      </span>
    </button>
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

        {/* Global Approval Banner — visible on every page */}
        <GlobalApprovalBanner />

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
