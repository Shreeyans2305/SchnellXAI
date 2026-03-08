import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getApproval } from '../services/api';

const ApprovalContext = createContext({
  pendingApproval: null,
  showModal: false,
  setShowModal: () => {},
  refresh: () => Promise.resolve(),
});

export function ApprovalProvider({ children }) {
  const [pendingApproval, setPendingApproval] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getApproval();
      if (data && data.id) {
        setPendingApproval(data);
      } else {
        setPendingApproval(null);
        setShowModal(false); // auto-close modal when no pending approval
      }
    } catch {
      setPendingApproval(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <ApprovalContext.Provider value={{ pendingApproval, showModal, setShowModal, refresh }}>
      {children}
    </ApprovalContext.Provider>
  );
}

export function useApproval() {
  return useContext(ApprovalContext);
}
