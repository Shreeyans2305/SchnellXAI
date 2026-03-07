import { useEffect, useState, useRef, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, useMap } from 'react-leaflet';
import { getHubs, getShipmentLocations } from '../services/api';
import { Map as MapIcon } from 'lucide-react';

function AnimatedMarker({ position, status, id }) {
  const color = status === 'DELAYED' ? '#b32826' : status === 'AT RISK' ? '#f5a623' : '#42d65c';

  return (
    <CircleMarker center={position} radius={5} pathOptions={{ color, fillColor: color, fillOpacity: 0.9, weight: 2 }}>
      <Popup>
        <div className="text-xs font-mono">
          <div className="font-bold">{id}</div>
          <div>{status}</div>
        </div>
      </Popup>
    </CircleMarker>
  );
}

function MapContent({ hubs, shipments }) {
  return (
    <>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap'
      />

      {/* Hub markers */}
      {hubs.map((hub) => (
        <CircleMarker
          key={hub.id}
          center={[hub.lat, hub.lng]}
          radius={hub.status === 'congested' ? 10 : 7}
          pathOptions={{
            color: hub.status === 'congested' ? '#b32826' : '#f5a623',
            fillColor: hub.status === 'congested' ? '#b32826' : '#f5a623',
            fillOpacity: 0.3,
            weight: 1.5,
          }}
        >
          <Popup>
            <div className="text-xs">
              <div className="font-bold">{hub.name}</div>
              <div>Shipments: {hub.shipments}</div>
              <div>Status: {hub.status}</div>
            </div>
          </Popup>
        </CircleMarker>
      ))}

      {/* Route lines */}
      {shipments.map((s) => (
        <Polyline
          key={`route-${s.id}`}
          positions={[[s.from.lat, s.from.lng], [s.lat, s.lng], [s.to.lat, s.to.lng]]}
          pathOptions={{
            color: s.status === 'DELAYED' ? '#b32826' : s.status === 'AT RISK' ? '#f5a623' : '#42d65c',
            weight: 1.5,
            opacity: 0.4,
            dashArray: '8 6',
          }}
        />
      ))}

      {/* Shipment markers */}
      {shipments.map((s) => (
        <AnimatedMarker key={s.id} position={[s.lat, s.lng]} status={s.status} id={s.id} />
      ))}
    </>
  );
}

export default function ShipmentMap() {
  const [hubs, setHubs] = useState([]);
  const [shipments, setShipments] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const [h, s] = await Promise.all([getHubs(), getShipmentLocations()]);
      setHubs(h);
      setShipments(s);
    };
    fetchData();
    const id = setInterval(fetchData, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="bg-surface border border-border rounded-2xl overflow-hidden shadow-card">
      <div className="flex items-center gap-2 p-4 border-b border-border">
        <MapIcon className="w-4 h-4 text-amber" />
        <h3 className="text-sm font-semibold text-text">Live Shipment Map</h3>
        <span className="text-[10px] text-muted ml-auto font-mono bg-bg px-2 py-0.5 rounded-lg">REAL-TIME</span>
        <span className="w-2 h-2 rounded-full bg-green animate-pulse" />
      </div>
      <div className="h-[500px]">
        <MapContainer
          center={[22.0, 78.0]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          zoomControl={false}
        >
          <MapContent hubs={hubs} shipments={shipments} />
        </MapContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 p-3 border-t border-border">
        {[
          { color: 'bg-green', label: 'On Track' },
          { color: 'bg-amber', label: 'At Risk' },
          { color: 'bg-red', label: 'Delayed' },
          { color: 'bg-amber/50', label: 'Hub' },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${l.color}`} />
            <span className="text-[10px] text-muted">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
