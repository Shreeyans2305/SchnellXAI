import ShipmentMap from '../components/ShipmentMap';
import SimulationPanel from '../components/SimulationPanel';

export default function Simulation() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4 overflow-y-auto h-full">
      {/* Left — Map */}
      <div>
        <ShipmentMap />
      </div>

      {/* Right — Simulation + Cascade + Reasoning */}
      <div>
        <SimulationPanel />
      </div>
    </div>
  );
}
