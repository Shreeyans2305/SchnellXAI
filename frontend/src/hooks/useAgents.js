import { useState, useEffect, useCallback } from 'react';
import { getAgents } from '../services/api';

export function useAgents(pollInterval = 5000) {
  const [agents, setAgents] = useState([]);
  const [edges, setEdges] = useState([]);
  const [extra, setExtra] = useState({});
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const data = await getAgents();
      setAgents(data.agents || []);
      setEdges(data.edges || []);
      setExtra({ currentAgent: data.currentAgent || '' });
    } catch {
      // keep existing data
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollInterval);
    return () => clearInterval(id);
  }, [fetch, pollInterval]);

  return { agents, edges, extra, loading, refetch: fetch };
}
