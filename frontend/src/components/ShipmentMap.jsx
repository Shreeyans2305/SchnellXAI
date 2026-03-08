import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Popup, Marker } from 'react-leaflet';
import L from 'leaflet';
import { getHubs, getShipmentLocations } from '../services/api';
import { Map as MapIcon } from 'lucide-react';

/* ── Nuke Leaflet's default broken icon setup ──────────────────── */
delete L.Icon.Default.prototype._getIconUrl;

/* ── Helper: build a zero-size divIcon with an absolutely-positioned
     emoji that cannot be clipped or overridden by Leaflet CSS ──── */
function emojiIcon(emoji, fontSize = 24) {
  return L.divIcon({
    className: '',                     // no leaflet classes at all
    iconSize: [0, 0],                  // zero container → nothing to clip
    iconAnchor: [0, 0],
    popupAnchor: [0, -(fontSize / 2) - 6],
    html: `<span style="
      position:absolute;
      left:0; top:0;
      transform:translate(-50%,-50%);
      font-size:${fontSize}px;
      line-height:1;
      white-space:nowrap;
      pointer-events:auto;
      cursor:pointer;
      filter:drop-shadow(0 2px 4px rgba(0,0,0,.5));
      background:none; border:none;
    ">${emoji}</span>`,
  });
}

/* ── Concrete icons ────────────────────────────────────────────── */
function hubMarkerIcon(hub) {
  const congested = hub.status === 'congested';
  return emojiIcon(congested ? '⛔' : '🏭', congested ? 30 : 26);
}

function shipmentMarkerIcon(status) {
  const dot = status === 'DELAYED' ? '🔴' : status === 'AT RISK' ? '🟡' : '🟢';
  return emojiIcon(`📦${dot}`, 18);
}

function ShipmentMarker({ position, status, id }) {
  return (
    <Marker position={position} icon={shipmentMarkerIcon(status)}>
      <Popup>
        <div className="text-xs font-mono">
          <div className="font-bold">📦 {id}</div>
          <div>{status === 'DELAYED' ? '🔴' : status === 'AT RISK' ? '🟡' : '🟢'} {status}</div>
        </div>
      </Popup>
    </Marker>
  );
}

function MapContent({ hubs, shipments }) {
  return (
    <>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap'
      />

      {/* Route lines */}
      {shipments.map((s) => (
        <Polyline
          key={`route-${s.id}`}
          positions={[[s.from.lat, s.from.lng], [s.lat, s.lng], [s.to.lat, s.to.lng]]}
          pathOptions={{
            color: s.status === 'DELAYED' ? '#b32826' : s.status === 'AT RISK' ? '#f5a623' : '#42d65c',
            weight: 1.5,
            opacity: 0.35,
            dashArray: '8 6',
          }}
        />
      ))}

      {/* Hub (warehouse) markers — emoji */}
      {hubs.map((hub) => (
        <Marker key={hub.id} position={[hub.lat, hub.lng]} icon={hubMarkerIcon(hub)}>
          <Popup>
            <div className="text-xs">
              <div className="font-bold">
                {hub.status === 'congested' ? '⛔' : '🏭'} {hub.name}
              </div>
              <div className="mt-0.5">📦 Shipments: {hub.shipments}</div>
              <div>Status: <span className="font-semibold">{hub.status === 'congested' ? '⚠️ Congested' : '✅ Normal'}</span></div>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Shipment markers — emoji */}
      {shipments.map((s) => (
        <ShipmentMarker key={s.id} position={[s.lat, s.lng]} status={s.status} id={s.id} />
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
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 p-3 border-t border-border">
        <span className="text-[10px] text-muted/60 uppercase tracking-wider font-semibold mr-1">Shipments</span>
        {[
          { emoji: '📦🟢', label: 'On Track' },
          { emoji: '📦🟡', label: 'At Risk' },
          { emoji: '📦🔴', label: 'Delayed' },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1">
            <span className="text-xs">{l.emoji}</span>
            <span className="text-[10px] text-muted">{l.label}</span>
          </div>
        ))}

        <span className="w-px h-3 bg-border mx-1" />

        <span className="text-[10px] text-muted/60 uppercase tracking-wider font-semibold mr-1">Warehouses</span>
        {[
          { emoji: '🏭', label: 'Normal' },
          { emoji: '⛔', label: 'Congested' },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1">
            <span className="text-xs">{l.emoji}</span>
            <span className="text-[10px] text-muted">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
