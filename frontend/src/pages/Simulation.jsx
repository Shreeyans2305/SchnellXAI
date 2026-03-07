import { useMemo, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMapEvents } from 'react-leaflet';
import { AlertTriangle, Network, Save, Plus, Factory, Truck, Route, Sparkles, RotateCcw, ChevronRight, CheckCircle2 } from 'lucide-react';
import { generateDisruption, saveSimulationScenario } from '../services/api';

function MapClickCapture({ onClick }) {
  useMapEvents({
    click: (event) => onClick(event.latlng),
  });
  return null;
}

export default function Simulation() {
  const [scenario, setScenario] = useState({ warehouses: [], routes: [], carriers: [], shipments: [] });
  const [saving, setSaving] = useState(false);
  const [scenarioSaved, setScenarioSaved] = useState(false);
  const [lastMessage, setLastMessage] = useState('');
  const [pipeline, setPipeline] = useState(null);

  const [warehouseDraft, setWarehouseDraft] = useState({ name: '', lat: '', lng: '' });
  const [routeDraft, setRouteDraft] = useState({ fromWarehouseId: '', toWarehouseId: '', distanceKm: 400, typicalEtaMinutes: 180 });
  const [carrierDraft, setCarrierDraft] = useState({ name: '', reliability: 90, capacity: 250 });
  const [shipmentDraft, setShipmentDraft] = useState({ routeId: '', carrierId: '', progress: 10, risk: 20, status: 'ON TRACK', slaMinutes: 420, etaMinutes: 220, notes: '' });
  const [disruptionDraft, setDisruptionDraft] = useState({ type: 'late_pickup', targetShipmentId: '', targetWarehouseId: '', severity: 60 });

  const warehousesById = useMemo(() => {
    const map = new Map();
    scenario.warehouses.forEach((w) => map.set(Number(w.id), w));
    return map;
  }, [scenario.warehouses]);

  const isScenarioComplete = useMemo(() => {
    return scenario.warehouses.length >= 2
      && scenario.routes.length >= 1
      && scenario.carriers.length >= 1
      && scenario.shipments.length >= 1;
  }, [scenario]);

  const canCreateRoutes = scenario.warehouses.length >= 2;
  const canCreateShipments = scenario.routes.length >= 1 && scenario.carriers.length >= 1;
  const canRunDisruptions = isScenarioComplete && scenarioSaved;

  const shipmentMarkers = useMemo(() => {
    return scenario.shipments
      .map((s) => {
        const route = scenario.routes.find((r) => r.id === s.routeId);
        if (!route) return null;
        const from = warehousesById.get(Number(route.fromWarehouseId));
        const to = warehousesById.get(Number(route.toWarehouseId));
        if (!from || !to) return null;
        const ratio = Math.max(0, Math.min(1, Number(s.progress) / 100));
        return {
          id: s.id,
          status: s.status,
          from,
          to,
          lat: from.lat + (to.lat - from.lat) * ratio,
          lng: from.lng + (to.lng - from.lng) * ratio,
        };
      })
      .filter(Boolean);
  }, [scenario.shipments, scenario.routes, warehousesById]);

  const addWarehouse = () => {
    if (!warehouseDraft.name || warehouseDraft.lat === '' || warehouseDraft.lng === '') return;
    const nextId = scenario.warehouses.reduce((max, w) => Math.max(max, Number(w.id)), 0) + 1;
    const nextScenario = {
      ...scenario,
      warehouses: [...scenario.warehouses, { id: nextId, name: warehouseDraft.name, lat: Number(warehouseDraft.lat), lng: Number(warehouseDraft.lng), status: 'active' }],
    };
    setScenario(nextScenario);
    setScenarioSaved(false);
    setRouteDraft((prev) => ({
      ...prev,
      fromWarehouseId: prev.fromWarehouseId || nextScenario.warehouses?.[0]?.id || '',
      toWarehouseId: prev.toWarehouseId || nextScenario.warehouses?.[1]?.id || nextScenario.warehouses?.[0]?.id || '',
    }));
    setDisruptionDraft((prev) => ({ ...prev, targetWarehouseId: prev.targetWarehouseId || nextId }));
    setWarehouseDraft({ name: '', lat: '', lng: '' });
  };

  const addRoute = () => {
    if (!routeDraft.fromWarehouseId || !routeDraft.toWarehouseId) return;
    const nextIndex = scenario.routes.length + 1001;
    const nextRoute = {
      id: `RTE-${nextIndex}`,
      fromWarehouseId: Number(routeDraft.fromWarehouseId),
      toWarehouseId: Number(routeDraft.toWarehouseId),
      distanceKm: Number(routeDraft.distanceKm),
      typicalEtaMinutes: Number(routeDraft.typicalEtaMinutes),
    };
    setScenario((prev) => ({
      ...prev,
      routes: [...prev.routes, nextRoute],
    }));
    setScenarioSaved(false);
    setShipmentDraft((prev) => ({ ...prev, routeId: prev.routeId || nextRoute.id }));
  };

  const addCarrier = () => {
    if (!carrierDraft.name) return;
    const nextId = scenario.carriers.reduce((max, c) => Math.max(max, Number(c.id)), 0) + 1;
    setScenario((prev) => ({
      ...prev,
      carriers: [...prev.carriers, { id: nextId, ...carrierDraft, reliability: Number(carrierDraft.reliability), capacity: Number(carrierDraft.capacity) }],
    }));
    setScenarioSaved(false);
    setShipmentDraft((prev) => ({ ...prev, carrierId: prev.carrierId || nextId }));
    setCarrierDraft({ name: '', reliability: 90, capacity: 250 });
  };

  const addShipment = () => {
    if (!shipmentDraft.routeId || !shipmentDraft.carrierId) return;
    const nextId = `SHP-${Math.floor(1000 + Math.random() * 8999)}`;
    setScenario((prev) => ({
      ...prev,
      shipments: [
        ...prev.shipments,
        {
          id: nextId,
          routeId: shipmentDraft.routeId,
          carrierId: Number(shipmentDraft.carrierId),
          progress: Number(shipmentDraft.progress),
          risk: Number(shipmentDraft.risk),
          status: shipmentDraft.status,
          slaMinutes: Number(shipmentDraft.slaMinutes),
          etaMinutes: Number(shipmentDraft.etaMinutes),
          notes: shipmentDraft.notes,
        },
      ],
    }));
    setScenarioSaved(false);
    setDisruptionDraft((prev) => ({ ...prev, targetShipmentId: prev.targetShipmentId || nextId }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await saveSimulationScenario(scenario);
      setScenario(res.data || scenario);
      setScenarioSaved(true);
      setLastMessage('Scenario saved. New logistics graph is active in backend.');
    } catch {
      setLastMessage('Failed to save scenario.');
    } finally {
      setSaving(false);
    }
  };

  const resetAllSimulationData = async () => {
    const confirmed = window.confirm('Reset all simulation data (warehouses, routes, carriers, shipments) and save empty scenario?');
    if (!confirmed) return;

    const emptyScenario = { warehouses: [], routes: [], carriers: [], shipments: [] };
    setScenario(emptyScenario);
    setScenarioSaved(false);
    setPipeline(null);
    setWarehouseDraft({ name: '', lat: '', lng: '' });
    setRouteDraft({ fromWarehouseId: '', toWarehouseId: '', distanceKm: 400, typicalEtaMinutes: 180 });
    setCarrierDraft({ name: '', reliability: 90, capacity: 250 });
    setShipmentDraft({ routeId: '', carrierId: '', progress: 10, risk: 20, status: 'ON TRACK', slaMinutes: 420, etaMinutes: 220, notes: '' });
    setDisruptionDraft({ type: 'late_pickup', targetShipmentId: '', targetWarehouseId: '', severity: 60 });

    try {
      await saveSimulationScenario(emptyScenario);
      setScenarioSaved(true);
      setLastMessage('All simulation data reset and saved. Start by adding warehouses.');
    } catch {
      setLastMessage('Local reset completed, but backend save failed.');
    }
  };

  const triggerDisruption = async (type) => {
    if (!canRunDisruptions) {
      setLastMessage('Add complete scenario data and save it before generating disruptions.');
      return;
    }
    try {
      const payload = {
        ...disruptionDraft,
        type,
        targetShipmentId: disruptionDraft.targetShipmentId || undefined,
        targetWarehouseId: disruptionDraft.targetWarehouseId ? Number(disruptionDraft.targetWarehouseId) : undefined,
        severity: Number(disruptionDraft.severity),
      };
      const res = await generateDisruption(payload);
      setLastMessage(res.data?.message || 'Disruption generated.');
      setPipeline(res.data?.pipeline || null);
    } catch {
      setLastMessage('Failed to generate disruption.');
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-5 px-6 pb-6 overflow-y-auto h-full">
      <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-card">
        <div className="flex items-center gap-2 p-4 border-b border-border">
          <Network className="w-4 h-4 text-amber" />
          <h3 className="text-sm font-semibold text-text">Simulation Network Builder</h3>
          <span className="ml-auto text-[10px] text-muted">Start empty. Click map to set warehouse coordinates</span>
        </div>
        <div className="h-[480px]">
          <MapContainer center={[22.5, 79]} zoom={5} style={{ height: '100%', width: '100%' }} zoomControl={false}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap" />
            <MapClickCapture
              onClick={(latlng) => setWarehouseDraft((prev) => ({ ...prev, lat: latlng.lat.toFixed(4), lng: latlng.lng.toFixed(4) }))}
            />

            {scenario.routes.map((route) => {
              const from = warehousesById.get(Number(route.fromWarehouseId));
              const to = warehousesById.get(Number(route.toWarehouseId));
              if (!from || !to) return null;
              return (
                <Polyline
                  key={route.id}
                  positions={[[from.lat, from.lng], [to.lat, to.lng]]}
                  pathOptions={{ color: '#f5a623', weight: 2, opacity: 0.5, dashArray: '8 6' }}
                />
              );
            })}

            {scenario.warehouses.map((hub) => (
              <CircleMarker
                key={hub.id}
                center={[hub.lat, hub.lng]}
                radius={hub.status === 'congested' ? 10 : 7}
                pathOptions={{ color: hub.status === 'congested' ? '#b32826' : '#f5a623', fillOpacity: 0.35 }}
              >
                <Popup>
                  <div className="text-xs">
                    <div className="font-bold">{hub.name}</div>
                    <div>Status: {hub.status}</div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {shipmentMarkers.map((s) => (
              <CircleMarker
                key={s.id}
                center={[s.lat, s.lng]}
                radius={5}
                pathOptions={{
                  color: s.status === 'DELAYED' ? '#b32826' : s.status === 'AT RISK' ? '#f5a623' : '#42d65c',
                  fillOpacity: 0.9,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="text-xs font-mono">
                    <div className="font-bold">{s.id}</div>
                    <div>{s.status}</div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        <div className="p-4 border-t border-border flex items-center gap-2">
          <button
            onClick={handleSave}
            disabled={saving || !isScenarioComplete}
            className="px-3 py-2 text-xs rounded-xl bg-amber text-white font-semibold flex items-center gap-1 disabled:opacity-60"
          >
            <Save className="w-3 h-3" />
            {saving ? 'Saving...' : 'Save Scenario'}
          </button>
          <button
            onClick={resetAllSimulationData}
            className="px-3 py-2 text-xs rounded-xl bg-bg border border-border text-text font-semibold flex items-center gap-1 hover:bg-border/30"
          >
            <RotateCcw className="w-3 h-3" />
            Reset All Simulation Data
          </button>
          <span className={`text-[10px] ${scenarioSaved ? 'text-green' : 'text-muted'}`}>
            {scenarioSaved ? 'Scenario saved' : 'Unsaved scenario'}
          </span>
          <span className="text-xs text-muted">{lastMessage}</span>
        </div>
      </div>

      <div className="space-y-5">
        {/* Flowchart with counters on top */}
        <div className="bg-surface border border-border rounded-2xl p-5 shadow-card">
          <h3 className="text-sm font-semibold text-text mb-3">Scenario Build Progress</h3>
          
          {/* Counters */}
          <div className="grid grid-cols-4 gap-2 text-[11px] mb-4">
            <div className="bg-bg border border-border rounded-xl px-2 py-1.5 text-center">
              <div className="text-muted text-[10px]">Warehouses</div>
              <div className="text-amber font-bold text-base">{scenario.warehouses.length}</div>
            </div>
            <div className="bg-bg border border-border rounded-xl px-2 py-1.5 text-center">
              <div className="text-muted text-[10px]">Routes</div>
              <div className="text-amber font-bold text-base">{scenario.routes.length}</div>
            </div>
            <div className="bg-bg border border-border rounded-xl px-2 py-1.5 text-center">
              <div className="text-muted text-[10px]">Carriers</div>
              <div className="text-amber font-bold text-base">{scenario.carriers.length}</div>
            </div>
            <div className="bg-bg border border-border rounded-xl px-2 py-1.5 text-center">
              <div className="text-muted text-[10px]">Shipments</div>
              <div className="text-amber font-bold text-base">{scenario.shipments.length}</div>
            </div>
          </div>

          {/* Visual Flowchart */}
          <div className="flex items-center justify-between text-[10px]">
            <div className={`flex flex-col items-center gap-1 ${scenario.warehouses.length >= 2 ? 'text-green' : 'text-muted'}`}>
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${scenario.warehouses.length >= 2 ? 'border-green bg-green/10' : 'border-border bg-bg'}`}>
                {scenario.warehouses.length >= 2 ? <CheckCircle2 className="w-5 h-5" /> : <Factory className="w-5 h-5" />}
              </div>
              <div className="font-semibold">Warehouses</div>
              <div className="text-[9px]">Min: 2</div>
            </div>
            
            <ChevronRight className="w-4 h-4 text-border" />
            
            <div className={`flex flex-col items-center gap-1 ${canCreateRoutes && scenario.routes.length >= 1 ? 'text-green' : 'text-muted'}`}>
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${canCreateRoutes && scenario.routes.length >= 1 ? 'border-green bg-green/10' : 'border-border bg-bg'}`}>
                {canCreateRoutes && scenario.routes.length >= 1 ? <CheckCircle2 className="w-5 h-5" /> : <Route className="w-5 h-5" />}
              </div>
              <div className="font-semibold">Routes</div>
              <div className="text-[9px]">Min: 1</div>
            </div>
            
            <ChevronRight className="w-4 h-4 text-border" />
            
            <div className={`flex flex-col items-center gap-1 ${scenario.carriers.length >= 1 ? 'text-green' : 'text-muted'}`}>
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${scenario.carriers.length >= 1 ? 'border-green bg-green/10' : 'border-border bg-bg'}`}>
                {scenario.carriers.length >= 1 ? <CheckCircle2 className="w-5 h-5" /> : <Truck className="w-5 h-5" />}
              </div>
              <div className="font-semibold">Carriers</div>
              <div className="text-[9px]">Min: 1</div>
            </div>
            
            <ChevronRight className="w-4 h-4 text-border" />
            
            <div className={`flex flex-col items-center gap-1 ${isScenarioComplete ? 'text-green' : 'text-muted'}`}>
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${isScenarioComplete ? 'border-green bg-green/10' : 'border-border bg-bg'}`}>
                {isScenarioComplete ? <CheckCircle2 className="w-5 h-5" /> : <Network className="w-5 h-5" />}
              </div>
              <div className="font-semibold">Shipments</div>
              <div className="text-[9px]">Min: 1</div>
            </div>
            
            <ChevronRight className="w-4 h-4 text-border" />
            
            <div className={`flex flex-col items-center gap-1 ${scenarioSaved ? 'text-green' : 'text-muted'}`}>
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${scenarioSaved ? 'border-green bg-green/10' : 'border-border bg-bg'}`}>
                {scenarioSaved ? <CheckCircle2 className="w-5 h-5" /> : <Save className="w-5 h-5" />}
              </div>
              <div className="font-semibold">Save</div>
              <div className="text-[9px]">Required</div>
            </div>
            
            <ChevronRight className="w-4 h-4 text-border" />
            
            <div className={`flex flex-col items-center gap-1 ${canRunDisruptions ? 'text-green' : 'text-muted'}`}>
              <div className={`w-12 h-12 rounded-xl border-2 flex items-center justify-center ${canRunDisruptions ? 'border-green bg-green/10' : 'border-border bg-bg'}`}>
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="font-semibold">Disrupt</div>
              <div className="text-[9px]">Ready</div>
            </div>
          </div>
        </div>

        {/* Step 1: Warehouses */}
        <div className="bg-surface border border-border rounded-2xl p-5 space-y-4 shadow-card">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue/20 border border-blue/40 flex items-center justify-center text-xs font-bold text-blue">1</div>
            <Factory className="w-4 h-4 text-blue" />
            <h3 className="text-sm font-semibold text-text">Add Warehouses</h3>
            <span className="ml-auto text-[10px] text-muted">Minimum 2 required</span>
          </div>
          <div className="text-[11px] text-muted bg-bg border border-border rounded-xl p-2">
            💡 <strong>Tip:</strong> Click anywhere on the map to auto-fill the latitude and longitude fields below.
          </div>
          
          <div className="space-y-2">
            <div>
              <label className="text-[10px] text-muted mb-1 block">Warehouse Name (e.g., "Mumbai Hub")</label>
              <input 
                value={warehouseDraft.name} 
                onChange={(e) => setWarehouseDraft((p) => ({ ...p, name: e.target.value }))} 
                placeholder="Enter warehouse name" 
                className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs text-text"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Latitude (click map)</label>
                <input 
                  value={warehouseDraft.lat} 
                  onChange={(e) => setWarehouseDraft((p) => ({ ...p, lat: e.target.value }))} 
                  placeholder="e.g., 19.0760" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs text-text"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Longitude (click map)</label>
                <input 
                  value={warehouseDraft.lng} 
                  onChange={(e) => setWarehouseDraft((p) => ({ ...p, lng: e.target.value }))} 
                  placeholder="e.g., 72.8777" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs text-text"
                />
              </div>
            </div>
            <button 
              onClick={addWarehouse} 
              className="w-full bg-blue/10 border border-blue/30 rounded-xl text-xs px-3 py-2.5 flex items-center justify-center gap-2 hover:bg-blue/20 font-semibold text-blue"
            >
              <Plus className="w-4 h-4" />
              Add Warehouse to Map
            </button>
          </div>
        </div>

        {/* Step 2: Routes */}
        <div className={`bg-surface border rounded-2xl p-5 space-y-4 shadow-card ${canCreateRoutes ? 'border-border' : 'border-border opacity-60'}`}>
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${canCreateRoutes ? 'bg-amber/20 border border-amber/40 text-amber' : 'bg-bg border border-border text-muted'}`}>2</div>
            <Route className={`w-4 h-4 ${canCreateRoutes ? 'text-amber' : 'text-muted'}`} />
            <h3 className={`text-sm font-semibold ${canCreateRoutes ? 'text-text' : 'text-muted'}`}>Add Routes Between Warehouses</h3>
            <span className="ml-auto text-[10px] text-muted">Minimum 1 required</span>
          </div>
          {!canCreateRoutes && (
            <div className="text-[11px] text-amber bg-amber/5 border border-amber/20 rounded-xl p-2">
              ⚠️ Add at least 2 warehouses first to unlock route creation.
            </div>
          )}
          
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Starting Warehouse</label>
                <select 
                  disabled={!canCreateRoutes} 
                  value={routeDraft.fromWarehouseId} 
                  onChange={(e) => setRouteDraft((p) => ({ ...p, fromWarehouseId: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="">Select origin</option>
                  {scenario.warehouses.map((w) => <option key={`from-${w.id}`} value={w.id}>{w.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Destination Warehouse</label>
                <select 
                  disabled={!canCreateRoutes} 
                  value={routeDraft.toWarehouseId} 
                  onChange={(e) => setRouteDraft((p) => ({ ...p, toWarehouseId: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="">Select destination</option>
                  {scenario.warehouses.map((w) => <option key={`to-${w.id}`} value={w.id}>{w.name}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Distance (kilometers)</label>
                <input 
                  disabled={!canCreateRoutes} 
                  type="number" 
                  value={routeDraft.distanceKm} 
                  onChange={(e) => setRouteDraft((p) => ({ ...p, distanceKm: e.target.value }))} 
                  placeholder="e.g., 1410" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Typical ETA (minutes)</label>
                <input 
                  disabled={!canCreateRoutes} 
                  type="number" 
                  value={routeDraft.typicalEtaMinutes} 
                  onChange={(e) => setRouteDraft((p) => ({ ...p, typicalEtaMinutes: e.target.value }))} 
                  placeholder="e.g., 420" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                />
              </div>
            </div>
            <button 
              disabled={!canCreateRoutes} 
              onClick={addRoute} 
              className="w-full bg-amber/10 border border-amber/30 rounded-xl text-xs px-3 py-2.5 flex items-center justify-center gap-2 disabled:opacity-40 hover:bg-amber/20 font-semibold text-amber"
            >
              <Route className="w-4 h-4" />
              Add Route Connection
            </button>
          </div>
        </div>

        {/* Step 3: Carriers */}
        <div className="bg-surface border border-border rounded-2xl p-5 space-y-4 shadow-card">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-green/20 border border-green/40 flex items-center justify-center text-xs font-bold text-green">3</div>
            <Truck className="w-4 h-4 text-green" />
            <h3 className="text-sm font-semibold text-text">Add Carriers</h3>
            <span className="ml-auto text-[10px] text-muted">Minimum 1 required</span>
          </div>
          
          <div className="space-y-2">
            <div>
              <label className="text-[10px] text-muted mb-1 block">Carrier Name (e.g., "BlueDart", "Delhivery")</label>
              <input 
                value={carrierDraft.name} 
                onChange={(e) => setCarrierDraft((p) => ({ ...p, name: e.target.value }))} 
                placeholder="Enter carrier name" 
                className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs text-text"
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Reliability Score (0-100)</label>
                <input 
                  type="number" 
                  value={carrierDraft.reliability} 
                  onChange={(e) => setCarrierDraft((p) => ({ ...p, reliability: e.target.value }))} 
                  placeholder="e.g., 90" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs text-text"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Capacity (vehicles)</label>
                <input 
                  type="number" 
                  value={carrierDraft.capacity} 
                  onChange={(e) => setCarrierDraft((p) => ({ ...p, capacity: e.target.value }))} 
                  placeholder="e.g., 250" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs text-text"
                />
              </div>
            </div>
            <button 
              onClick={addCarrier} 
              className="w-full bg-green/10 border border-green/30 rounded-xl text-xs px-3 py-2.5 flex items-center justify-center gap-2 hover:bg-green/20 font-semibold text-green"
            >
              <Plus className="w-4 h-4" />
              Add Carrier to Fleet
            </button>
          </div>
        </div>

        {/* Step 4: Shipments */}
        <div className={`bg-surface border rounded-2xl p-5 space-y-4 shadow-card ${canCreateShipments ? 'border-border' : 'border-border opacity-60'}`}>
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${canCreateShipments ? 'bg-purple/20 border border-purple/40 text-purple' : 'bg-bg border border-border text-muted'}`}>4</div>
            <Network className={`w-4 h-4 ${canCreateShipments ? 'text-purple' : 'text-muted'}`} />
            <h3 className={`text-sm font-semibold ${canCreateShipments ? 'text-text' : 'text-muted'}`}>Add Shipments</h3>
            <span className="ml-auto text-[10px] text-muted">Minimum 1 required</span>
          </div>
          {!canCreateShipments && (
            <div className="text-[11px] text-purple bg-purple/5 border border-purple/20 rounded-xl p-2">
              ⚠️ Add at least 1 route and 1 carrier first to unlock shipment creation.
            </div>
          )}
          
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Route (Origin → Destination)</label>
                <select 
                  disabled={!canCreateShipments} 
                  value={shipmentDraft.routeId} 
                  onChange={(e) => setShipmentDraft((p) => ({ ...p, routeId: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="">Select route</option>
                  {scenario.routes.map((r) => <option key={r.id} value={r.id}>{r.id}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Carrier Company</label>
                <select 
                  disabled={!canCreateShipments} 
                  value={shipmentDraft.carrierId} 
                  onChange={(e) => setShipmentDraft((p) => ({ ...p, carrierId: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="">Select carrier</option>
                  {scenario.carriers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Progress %</label>
                <input 
                  disabled={!canCreateShipments} 
                  type="number" 
                  value={shipmentDraft.progress} 
                  onChange={(e) => setShipmentDraft((p) => ({ ...p, progress: e.target.value }))} 
                  placeholder="0-100" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Risk Score</label>
                <input 
                  disabled={!canCreateShipments} 
                  type="number" 
                  value={shipmentDraft.risk} 
                  onChange={(e) => setShipmentDraft((p) => ({ ...p, risk: e.target.value }))} 
                  placeholder="0-100" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                />
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Status</label>
                <select 
                  disabled={!canCreateShipments} 
                  value={shipmentDraft.status} 
                  onChange={(e) => setShipmentDraft((p) => ({ ...p, status: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="ON TRACK">ON TRACK</option>
                  <option value="AT RISK">AT RISK</option>
                  <option value="DELAYED">DELAYED</option>
                </select>
              </div>
            </div>
            <button 
              disabled={!canCreateShipments} 
              onClick={addShipment} 
              className="w-full bg-purple/10 border border-purple/30 rounded-xl text-xs px-3 py-2.5 flex items-center justify-center gap-2 disabled:opacity-40 hover:bg-purple/20 font-semibold text-purple"
            >
              <Plus className="w-4 h-4" />
              Add Shipment to Scenario
            </button>
          </div>
        </div>

        {/* Step 5 & 6: Disruptions */}
        <div className="bg-surface border border-border rounded-2xl p-5 space-y-4 shadow-card">
          <div className="flex items-center gap-2">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${canRunDisruptions ? 'bg-red/10 border border-red/40 text-red' : 'bg-bg border border-border text-muted'}`}>5</div>
            <AlertTriangle className={`w-4 h-4 ${canRunDisruptions ? 'text-red' : 'text-muted'}`} />
            <h3 className={`text-sm font-semibold ${canRunDisruptions ? 'text-text' : 'text-muted'}`}>Generate Disruptions</h3>
          </div>
          {!canRunDisruptions && (
            <div className="text-[11px] text-red bg-red/5 border border-red/20 rounded-xl p-2">
              ⚠️ Complete all steps above and save the scenario first to unlock disruption generation.
            </div>
          )}
          
          <div className="space-y-2">
            <div className="grid grid-cols-3 gap-2">
              <div>
                <label className="text-[10px] text-muted mb-1 block">Target Shipment (optional)</label>
                <select 
                  disabled={!canRunDisruptions}
                  value={disruptionDraft.targetShipmentId} 
                  onChange={(e) => setDisruptionDraft((p) => ({ ...p, targetShipmentId: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="">Auto-select highest risk</option>
                  {scenario.shipments.map((s) => <option key={s.id} value={s.id}>{s.id}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Target Warehouse (optional)</label>
                <select 
                  disabled={!canRunDisruptions}
                  value={disruptionDraft.targetWarehouseId} 
                  onChange={(e) => setDisruptionDraft((p) => ({ ...p, targetWarehouseId: e.target.value }))} 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                >
                  <option value="">Auto-select</option>
                  {scenario.warehouses.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] text-muted mb-1 block">Severity (1-100)</label>
                <input 
                  disabled={!canRunDisruptions}
                  type="number" 
                  value={disruptionDraft.severity} 
                  onChange={(e) => setDisruptionDraft((p) => ({ ...p, severity: e.target.value }))} 
                  placeholder="60" 
                  className="w-full bg-bg border border-border rounded-xl px-3 py-2 text-xs disabled:opacity-40 text-text"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button 
                disabled={!canRunDisruptions} 
                onClick={() => triggerDisruption('late_pickup')} 
                className="bg-red/5 border border-red/20 rounded-xl text-xs py-2.5 disabled:opacity-40 hover:bg-red/10 font-semibold text-red"
              >
                📦 Late Pickup
              </button>
              <button 
                disabled={!canRunDisruptions} 
                onClick={() => triggerDisruption('warehouse_congestion')} 
                className="bg-red/5 border border-red/20 rounded-xl text-xs py-2.5 disabled:opacity-40 hover:bg-red/10 font-semibold text-red"
              >
                🏭 Warehouse Congestion
              </button>
              <button 
                disabled={!canRunDisruptions} 
                onClick={() => triggerDisruption('inaccurate_eta')} 
                className="bg-red/5 border border-red/20 rounded-xl text-xs py-2.5 disabled:opacity-40 hover:bg-red/10 font-semibold text-red"
              >
                ⏱️ Inaccurate ETA
              </button>
              <button 
                disabled={!canRunDisruptions} 
                onClick={() => triggerDisruption('cascading_reroute')} 
                className="bg-red/5 border border-red/20 rounded-xl text-xs py-2.5 disabled:opacity-40 hover:bg-red/10 font-semibold text-red"
              >
                🔄 Cascading Reroute
              </button>
            </div>
          </div>

          {pipeline && (
            <div className="border border-border rounded-xl p-3 bg-bg space-y-2">
              <div className="flex items-center gap-1 text-xs text-amber"><Sparkles className="w-3 h-3" />Pipeline executed immediately</div>
              <div className="text-[11px] text-text/70">Observer: {(pipeline.observer?.observations || []).length} observation groups</div>
              <div className="text-[11px] text-text/70">Reasoner: {(pipeline.reasoner?.hypotheses || []).length} hypotheses</div>
              <div className="text-[11px] text-text/70">Decider: {(pipeline.decider?.actions || []).length} actions</div>
              <div className="text-[11px] text-text/70">Queued approvals: {pipeline.queuedApprovals}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
