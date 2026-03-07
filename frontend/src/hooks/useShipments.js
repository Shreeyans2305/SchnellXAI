import { useState, useEffect, useCallback } from 'react';
import { getShipments, getShipmentLocations } from '../services/api';

export function useShipments(pollInterval = 30000) {
  const [shipments, setShipments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    try {
      const [s, l] = await Promise.all([getShipments(), getShipmentLocations()]);
      setShipments(s);
      setLocations(l);
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

  return { shipments, locations, loading, refetch: fetch };
}
