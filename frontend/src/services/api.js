import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Mock Data ──────────────────────────────────────────

const mockEvents = [
  { id: 1, time: '10:14:32', type: 'ANOMALY', flow: 'observer → reasoner', message: 'SHP-4821 Nagpur hub throughput drop −34%' },
  { id: 2, time: '10:15:01', type: 'REROUTE', flow: 'decider → executor', message: 'SHP-3192 rerouted via Pune Hub — ETA adjusted +2h' },
  { id: 3, time: '10:15:18', type: 'ALERT', flow: 'observer → decider', message: 'SHP-7734 carrier delay detected — BlueDart Nagpur' },
  { id: 4, time: '10:16:02', type: 'LEARNING', flow: 'learner → all', message: 'Route pattern Nagpur→Mumbai via Pune 12% faster historically' },
  { id: 5, time: '10:16:45', type: 'APPROVAL', flow: 'decider → human', message: 'SHP-4821 reroute requires manager approval — cost delta +₹2,400' },
  { id: 6, time: '10:17:12', type: 'EXECUTE', flow: 'executor → carrier', message: 'SHP-3192 new manifest dispatched to Delhivery' },
  { id: 7, time: '10:17:55', type: 'ANOMALY', flow: 'observer → reasoner', message: 'SHP-5567 temperature excursion detected — cold chain at risk' },
  { id: 8, time: '10:18:30', type: 'OPTIMIZE', flow: 'reasoner → decider', message: 'Cluster analysis: 3 shipments can consolidate at Pune Hub' },
];

const mockMetrics = {
  shipments: { value: 0, change: '—' },
  atRisk: { value: 0, change: '—' },
  delayed: { value: 0, change: '—' },
  agentOps: { value: 0, change: '—' },
  approvals: { value: 0, change: '—' },
  ollamaStatus: 'disconnected',
  agentsActive: 0,
  agentsTotal: 5,
};

const mockAgents = [
  { id: 'observer', name: 'Observer', status: 'active', load: 72, messagesProcessed: 3421, lastAction: 'Scanning Nagpur hub telemetry', color: '#3b82f6' },
  { id: 'reasoner', name: 'Reasoner', status: 'active', load: 58, messagesProcessed: 2180, lastAction: 'Analyzing delay correlation patterns', color: '#8b5cf6' },
  { id: 'decider', name: 'Decider', status: 'active', load: 45, messagesProcessed: 1842, lastAction: 'Evaluating reroute for SHP-4821', color: '#f5a623' },
  { id: 'executor', name: 'Executor', status: 'active', load: 63, messagesProcessed: 1567, lastAction: 'Dispatching manifest to Delhivery', color: '#42d65c' },
  { id: 'learner', name: 'Learner', status: 'active', load: 34, messagesProcessed: 980, lastAction: 'Updating route optimization model', color: '#b32826' },
];

const mockEdges = [
  { from: 'observer', to: 'reasoner', active: true },
  { from: 'observer', to: 'decider', active: false },
  { from: 'reasoner', to: 'decider', active: true },
  { from: 'reasoner', to: 'executor', active: false },
  { from: 'decider', to: 'executor', active: true },
  { from: 'executor', to: 'learner', active: true },
  { from: 'learner', to: 'observer', active: false },
  { from: 'learner', to: 'reasoner', active: true },
];

const mockShipments = [
  { id: 'SHP-4821', route: 'Mumbai → Delhi', carrier: 'BlueDart', progress: 45, eta: '2h 30m', sla: 'Standard', risk: 78, agent: 'Decider', status: 'AT RISK', notes: 'Nagpur hub congestion — reroute pending approval' },
  { id: 'SHP-3192', route: 'Chennai → Kolkata', carrier: 'Delhivery', progress: 72, eta: '1h 15m', sla: 'Express', risk: 25, agent: 'Executor', status: 'ON TRACK', notes: 'Rerouted via Pune — on schedule' },
  { id: 'SHP-7734', route: 'Bangalore → Hyderabad', carrier: 'BlueDart', progress: 30, eta: '4h 00m', sla: 'Standard', risk: 92, agent: 'Observer', status: 'DELAYED', notes: 'Carrier delay at Nagpur — awaiting update' },
  { id: 'SHP-5567', route: 'Delhi → Jaipur', carrier: 'DTDC', progress: 88, eta: '0h 45m', sla: 'Priority', risk: 15, agent: 'Executor', status: 'ON TRACK', notes: 'Final mile delivery in progress' },
  { id: 'SHP-9023', route: 'Pune → Ahmedabad', carrier: 'XpressBees', progress: 55, eta: '3h 10m', sla: 'Standard', risk: 45, agent: 'Reasoner', status: 'AT RISK', notes: 'Weather advisory on route — monitoring' },
  { id: 'SHP-1156', route: 'Kolkata → Lucknow', carrier: 'Shadowfax', progress: 20, eta: '5h 20m', sla: 'Economy', risk: 60, agent: 'Observer', status: 'AT RISK', notes: 'High traffic on NH2 — alternate route analysis' },
  { id: 'SHP-6640', route: 'Hyderabad → Chennai', carrier: 'Delhivery', progress: 95, eta: '0h 20m', sla: 'Express', risk: 5, agent: 'Executor', status: 'ON TRACK', notes: 'Arriving at destination hub' },
  { id: 'SHP-8312', route: 'Ahmedabad → Mumbai', carrier: 'DTDC', progress: 10, eta: '6h 00m', sla: 'Standard', risk: 85, agent: 'Decider', status: 'DELAYED', notes: 'Vehicle breakdown — replacement dispatched' },
];

const mockCarriers = [
  { id: 1, name: 'BlueDart', reliability: 94, active: 342, delayed: 12, trend: [88, 90, 91, 93, 94, 92, 94], logo: 'BD' },
  { id: 2, name: 'Delhivery', reliability: 91, active: 287, delayed: 18, trend: [85, 87, 89, 90, 91, 89, 91], logo: 'DL' },
  { id: 3, name: 'DTDC', reliability: 87, active: 198, delayed: 24, trend: [82, 84, 85, 86, 87, 88, 87], logo: 'DT' },
  { id: 4, name: 'XpressBees', reliability: 89, active: 156, delayed: 15, trend: [84, 86, 87, 88, 89, 90, 89], logo: 'XB' },
  { id: 5, name: 'Shadowfax', reliability: 85, active: 134, delayed: 20, trend: [80, 82, 83, 84, 85, 84, 85], logo: 'SF' },
];

const mockApproval = {
  id: 'APR-001',
  shipmentId: 'SHP-4821',
  action: 'Reroute SHP-4821 via Pune Hub',
  currentRoute: ['Mumbai', 'Nagpur', 'Delhi'],
  proposedRoute: ['Mumbai', 'Pune', 'Bhopal', 'Delhi'],
  blastRadius: 3,
  netScore: 82,
  costDelta: '+₹2,400',
  slaImpact: '+2h',
  reason: 'Nagpur hub throughput dropped 34%. Historical data shows Pune route is 12% faster during congestion events.',
};

const mockHubs = [
  { id: 1, name: 'Mumbai Hub', lat: 19.076, lng: 72.8777, shipments: 342, status: 'active' },
  { id: 2, name: 'Delhi Hub', lat: 28.7041, lng: 77.1025, shipments: 287, status: 'active' },
  { id: 3, name: 'Bangalore Hub', lat: 12.9716, lng: 77.5946, shipments: 198, status: 'active' },
  { id: 4, name: 'Chennai Hub', lat: 13.0827, lng: 80.2707, shipments: 156, status: 'active' },
  { id: 5, name: 'Kolkata Hub', lat: 22.5726, lng: 88.3639, shipments: 134, status: 'active' },
  { id: 6, name: 'Hyderabad Hub', lat: 17.385, lng: 78.4867, shipments: 178, status: 'active' },
  { id: 7, name: 'Pune Hub', lat: 18.5204, lng: 73.8567, shipments: 145, status: 'active' },
  { id: 8, name: 'Ahmedabad Hub', lat: 23.0225, lng: 72.5714, shipments: 112, status: 'active' },
  { id: 9, name: 'Jaipur Hub', lat: 26.9124, lng: 75.7873, shipments: 89, status: 'active' },
  { id: 10, name: 'Lucknow Hub', lat: 26.8467, lng: 80.9462, shipments: 95, status: 'active' },
  { id: 11, name: 'Nagpur Hub', lat: 21.1458, lng: 79.0882, shipments: 167, status: 'congested' },
  { id: 12, name: 'Bhopal Hub', lat: 23.2599, lng: 77.4126, shipments: 78, status: 'active' },
];

const mockShipmentLocations = [
  { id: 'SHP-4821', lat: 20.5, lng: 76.5, from: { lat: 19.076, lng: 72.8777 }, to: { lat: 28.7041, lng: 77.1025 }, status: 'AT RISK' },
  { id: 'SHP-3192', lat: 17.5, lng: 80.0, from: { lat: 13.0827, lng: 80.2707 }, to: { lat: 22.5726, lng: 88.3639 }, status: 'ON TRACK' },
  { id: 'SHP-7734', lat: 15.0, lng: 78.0, from: { lat: 12.9716, lng: 77.5946 }, to: { lat: 17.385, lng: 78.4867 }, status: 'DELAYED' },
  { id: 'SHP-5567', lat: 27.5, lng: 76.5, from: { lat: 28.7041, lng: 77.1025 }, to: { lat: 26.9124, lng: 75.7873 }, status: 'ON TRACK' },
  { id: 'SHP-9023', lat: 20.5, lng: 73.5, from: { lat: 18.5204, lng: 73.8567 }, to: { lat: 23.0225, lng: 72.5714 }, status: 'AT RISK' },
];

const mockSimulationResult = {
  options: [
    { id: 1, name: 'Reroute via Pune', netScore: 82, blastRadius: 3, slaImpact: '+2h', cost: '+₹2,400', recommended: true },
    { id: 2, name: 'Reroute via Ahmedabad', netScore: 68, blastRadius: 5, slaImpact: '+4h', cost: '+₹4,100', recommended: false },
    { id: 3, name: 'Wait for congestion to clear', netScore: 45, blastRadius: 8, slaImpact: '+6h', cost: '₹0', recommended: false },
  ],
  cascadeImpact: [
    { shipment: 'SHP-4821', impact: 'Primary — rerouted', severity: 'medium' },
    { shipment: 'SHP-9023', impact: 'Secondary — delayed 30m at Pune', severity: 'low' },
    { shipment: 'SHP-1156', impact: 'Tertiary — capacity reduced at hub', severity: 'low' },
  ],
  reasoning: 'The Observer detected a 34% throughput drop at Nagpur Hub. The Reasoner correlated this with historical congestion patterns and identified that Pune route has been 12% faster during similar events. The Decider evaluated three options and recommends rerouting via Pune based on optimal net score (82) with minimal blast radius (3 shipments affected).',
};

const mockScenario = {
  warehouses: [
    { id: 1, name: 'Mumbai Hub', lat: 19.076, lng: 72.8777, status: 'active' },
    { id: 2, name: 'Delhi Hub', lat: 28.7041, lng: 77.1025, status: 'active' },
    { id: 7, name: 'Pune Hub', lat: 18.5204, lng: 73.8567, status: 'active' },
    { id: 11, name: 'Nagpur Hub', lat: 21.1458, lng: 79.0882, status: 'congested' },
  ],
  routes: [
    { id: 'RTE-1001', fromWarehouseId: 1, toWarehouseId: 2, distanceKm: 1410, typicalEtaMinutes: 420 },
    { id: 'RTE-1006', fromWarehouseId: 1, toWarehouseId: 11, distanceKm: 830, typicalEtaMinutes: 260 },
    { id: 'RTE-1007', fromWarehouseId: 11, toWarehouseId: 2, distanceKm: 1030, typicalEtaMinutes: 330 },
  ],
  carriers: [
    { id: 1, name: 'BlueDart', reliability: 94, capacity: 380 },
    { id: 2, name: 'Delhivery', reliability: 91, capacity: 320 },
  ],
  shipments: [
    { id: 'SHP-4821', routeId: 'RTE-1006', carrierId: 1, progress: 45, risk: 78, status: 'AT RISK', slaMinutes: 480, etaMinutes: 150, notes: 'Congestion watch' },
    { id: 'SHP-9901', routeId: 'RTE-1001', carrierId: 2, progress: 24, risk: 42, status: 'ON TRACK', slaMinutes: 540, etaMinutes: 260, notes: 'Scheduled movement' },
  ],
};

const mockDisruptionResult = {
  message: 'Late pickup generated for SHP-4821',
  pipeline: {
    observer: { observations: [{ type: 'risky_shipments', items: [{ id: 'SHP-4821' }] }] },
    reasoner: { hypotheses: [{ type: 'hub_congestion', hub: 'Nagpur Hub' }] },
    decider: { actions: [{ id: 'ACT-SHP-4821', description: 'Reroute SHP-4821 away from congestion' }] },
    queuedApprovals: 1,
  },
};

// ── API functions with mock fallback ───────────────────

async function fetchWithFallback(endpoint, mockData) {
  try {
    const res = await api.get(endpoint);
    return res.data;
  } catch {
    return mockData;
  }
}

export const getEvents = () => fetchWithFallback('/agent/events', mockEvents);
export const getMetrics = () => fetchWithFallback('/dashboard/metrics', mockMetrics);
export const getAgents = () => fetchWithFallback('/agents/status', { agents: mockAgents, edges: mockEdges });
export const getShipments = () => fetchWithFallback('/shipments', mockShipments);
export const getCarriers = () => fetchWithFallback('/carriers', mockCarriers);
export const getApproval = () => fetchWithFallback('/approvals/pending', mockApproval);
export const getHubs = () => fetchWithFallback('/hubs', mockHubs);
export const getShipmentLocations = () => fetchWithFallback('/shipments/locations', mockShipmentLocations);

export const executeApproval = (id) =>
  api.post('/approvals/execute', { id }).catch(() => ({ data: { success: true } }));

export const rejectApproval = (id) =>
  api.post('/approvals/reject', { id }).catch(() => ({ data: { success: true } }));

export const runSimulation = (params) =>
  api.post('/simulation/run', params).catch(() => ({ data: mockSimulationResult }));

export const getSimulationScenario = () =>
  fetchWithFallback('/simulation/scenario', mockScenario);

export const saveSimulationScenario = (scenario) =>
  api.post('/simulation/scenario', scenario).catch(() => ({ data: scenario }));

export const generateSampleSystem = () =>
  api.post('/simulation/generate-sample', {}).catch(() => ({ data: null }));

export const resetState = () =>
  api.post('/simulation/reset', {}).catch(() => ({ data: { message: 'Reset failed' } }));

export const generateDisruption = (payload) =>
  api.post('/simulation/disruptions', payload, { timeout: 180000 }).catch(() => ({ data: mockDisruptionResult }));

export { mockSimulationResult };
export default api;
