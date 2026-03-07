## SchnellXAI Logistics Backend (FastAPI + Gemma on Ollama)

This backend powers the logistics agent dashboard and simulation frontend. It exposes a multi-agent loop (observe → reason → decide → act → learn) over a simulated Indian logistics network and uses a local Gemma model running in Ollama for higher-level reasoning and explanations.

### Prerequisites

- Python 3.10+
- Node.js (for the existing frontend)
- Ollama installed and running locally
  - Install from `https://ollama.com`
  - Pull a Gemma model, for example:

```bash
ollama pull gemma:2b
```

### Setup and Run Backend

From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ensure Ollama is running (default `http://localhost:11434`) and then start the FastAPI app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app serves all APIs under `/api`, matching the frontend's Vite proxy configuration.

### Environment Variables

- `OLLAMA_HOST` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `gemma:2b`)
- `SIMULATION_TICK_SECONDS` (default `5`)
- `AUTO_EXECUTE_MAX_BLAST_RADIUS` (default `3`)
- `AUTO_EXECUTE_MAX_COST_DELTA` (default `2500`)

### Multi-Agent Loop

On startup, the backend:

- Seeds an in-memory world state (shipments, hubs, carriers, map locations).
- Launches two background loops:
  - **Simulation loop**: moves shipments along routes, updates map positions, and injects random delays/congestion.
  - **Agent loop**: runs the Observer, Reasoner, Decider, Executor, and Learner agents:
    - **Observer**: scans shipment and hub signals for anomalies and at-risk flows.
    - **Reasoner**: clusters issues and hypothesizes root causes (hub bottlenecks, carrier degradation).
    - **Decider**: proposes actions (reroutes, adjustments) under guardrails.
    - **Executor**: applies selected actions, updates shipment risk/status, and logs outcomes.
    - **Learner**: evaluates outcomes from a replay buffer and slightly adjusts parameters (e.g., carrier reliability).

The loop writes structured `AgentEvent`s that drive the EventTicker and updates dashboard metrics in real time.

### API Surface (used by the frontend)

- `GET /api/dashboard/metrics` – aggregated metrics (`DashboardMetrics`).
- `GET /api/agent/events` – recent multi-agent events (`AgentEvent[]`).
- `GET /api/agents/status` – current agent mesh: `{ agents, edges }`.
- `GET /api/shipments` – table data for shipments.
- `GET /api/carriers` – carrier cards.
- `GET /api/hubs` – map hubs.
- `GET /api/shipments/locations` – shipment locations and routes for the map.
- `GET /api/approvals/pending` – next pending approval, or `null`.
- `POST /api/approvals/execute` – body `{ id }`, executes the associated action.
- `POST /api/approvals/reject` – body `{ id }`, rejects an approval.
- `POST /api/simulation/run` – body `{ shipmentId, hub }`, returns a `SimulationResult` matching the frontend's expectations.

All responses are shaped to match the existing frontend mocks, so the React UI can switch from mock data to live backend data without changes.

### Running Frontend + Backend Together

From the project root:

```bash
# Backend (in one terminal)
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

Then open the frontend URL (typically `http://localhost:5173`) to see live agent activity, maps, approvals, and simulations driven by the backend.

