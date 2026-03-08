# SchnellXAI

**An Agentic Logistics Intelligence Platform**

SchnellXAI is a full-stack, AI-powered logistics management platform built around a five-agent pipeline that continuously monitors, reasons about, and acts on supply chain disruptions in real time. It combines a LangGraph-orchestrated multi-agent system with a modern React dashboard, giving operators a live view of shipment health, autonomous decision-making, and human-in-the-loop approval workflows -- all powered by locally-hosted LLMs through Ollama.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Memory System](#memory-system)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Disruption Simulation](#disruption-simulation)
- [API Reference](#api-reference)
- [License](#license)

---

## Overview

Modern logistics networks generate thousands of signals per hour -- delayed pickups, hub congestion, carrier degradation, ETA drift. SchnellXAI treats these signals as first-class inputs to a structured reasoning pipeline. Instead of simple threshold alerts, the platform runs a five-stage agentic workflow every 25 seconds:

1. **Observe** anomalies across all shipments and hubs
2. **Reason** about root causes and correlate patterns
3. **Decide** on corrective actions with calibrated autonomy
4. **Execute** low-risk fixes automatically, escalate high-risk ones
5. **Learn** from outcomes to improve future decisions

The system is designed to be autonomous where possible and supervised where necessary. Routine carrier notifications and single-shipment reroutes happen without human involvement. Bulk hub reroutes affecting many shipments surface an approval request to the operator.

---

## Architecture

```
                    +------------------+
                    |   React Frontend |
                    |   (Vite + TW)    |
                    +--------+---------+
                             |
                        REST API (axios)
                             |
                    +--------+---------+
                    |   FastAPI Backend |
                    |   (uvicorn)       |
                    +--------+---------+
                             |
               +-------------+-------------+
               |                           |
    +----------+----------+     +----------+----------+
    |  LangGraph Pipeline |     |  SQLite Database    |
    |  (5-Agent Graph)    |     |  (episodes, patterns|
    |                     |     |   approvals, logs)  |
    +----------+----------+     +---------------------+
               |
        +------+------+
        | Ollama LLM  |
        | (gemma3)     |
        +-------------+
```

The backend runs a background scheduler that fires the LangGraph pipeline on a fixed 25-second interval. Between cycles, incoming disruptions are collected in a thread-safe anomaly buffer. When the pipeline runs, it drains the buffer and processes all accumulated events as a batch, preventing the system from over-reacting to individual signals.

---

## Agent Pipeline

The pipeline is a directed acyclic graph compiled by LangGraph with conditional routing:

```
Observer --> [anomalies?] --> Reasoner --> Decider --> [autonomous?] --> Executor --> Learner
    |                                                       |
    +-- (no anomalies) -------------------------------------> Learner
                                              (needs approval) ---> Learner
```

### Observer

Scans all shipments and hub states, identifies anomalies above the configured risk threshold. Uses the LLM to classify anomaly types (late pickup, hub congestion, carrier degradation, ETA mismatch, SLA breach risk) with a deterministic fallback that inspects actual hub status and shipment risk scores. Includes a severity gate that drops low-signal observations before they propagate downstream.

### Reasoner

Groups related observations, detects correlated patterns, and forms hypotheses about root causes. A pre-filter discards observations below severity 60 to prevent weak signals from snowballing into false positives. Pattern strength is classified as strong, moderate, or weak based on the number of correlated events and evidence quality.

### Decider

Translates hypotheses into concrete actions: reroute a shipment, notify a carrier, reallocate inventory, or escalate to a human. Each action is tagged as autonomous or requiring approval based on calibrated thresholds. Individual shipment reroutes and carrier notifications are autonomous by default. Only bulk hub reroutes affecting four or more shipments with risk scores at or above the human approval threshold require operator sign-off.

For non-autonomous actions, the Decider computes proposed routes with real geographic coordinates, showing the operator exactly which hubs the shipment would be rerouted through along with updated ETA estimates.

### Executor

Carries out autonomous actions using LangChain tools: `reroute_shipment`, `notify_carrier`, `reallocate_inventory`, `escalate_to_human`, and `run_what_if_simulation`. Each tool invocation is logged to short-term memory with a timestamped event trail.

### Learner

Evaluates cycle outcomes, extracts lessons, and writes them to long-term episodic memory. Patterns are indexed by a composite signature (anomaly type, hub, carrier) so future cycles can look up historical context. Confidence scores are updated incrementally based on whether actions succeeded.

---

## Memory System

SchnellXAI implements a dual-layer memory architecture:

**Short-Term Memory** -- An in-memory ring buffer (configurable window size, default 50 events) that stores the most recent agent events. Provides immediate context for the current pipeline cycle and feeds the live event ticker on the frontend.

**Long-Term Memory** -- SQLite-backed episodic storage with two core tables:

- `episodes` -- Full cycle snapshots with pattern signatures, actions taken, outcomes, and confidence deltas.
- `patterns` -- Aggregated pattern records tracking occurrence counts, average confidence, and recommended actions. Looked up by the Reasoner and Decider to inform future decisions.

Additional persistence tables include `approvals` (human-in-the-loop workflow state), `action_log` (execution audit trail), and `anomaly_log` (raw disruption history for learning context).

---

## Tech Stack

### Backend

| Component         | Technology                         |
|-------------------|------------------------------------|
| Web Framework     | FastAPI with Uvicorn               |
| Agent Orchestration | LangGraph (StateGraph)           |
| LLM Integration   | LangChain + LangChain-Ollama      |
| LLM Runtime       | Ollama (gemma3:latest)             |
| Database          | SQLite with WAL mode               |
| Configuration     | Pydantic Settings                  |
| Language          | Python 3.12                        |

### Frontend

| Component         | Technology                         |
|-------------------|------------------------------------|
| Framework         | React 18                           |
| Build Tool        | Vite 5                             |
| Styling           | Tailwind CSS 3                     |
| State Management  | Zustand                            |
| Routing           | React Router v6                    |
| Charts            | Recharts                           |
| Maps              | Leaflet + React-Leaflet            |
| Icons             | Lucide React                       |
| HTTP Client       | Axios                              |
| Typography        | Outfit + JetBrains Mono            |

---

## Project Structure

```
SchnellXAI/
|-- backend/
|   |-- main.py                    # FastAPI app entry point
|   |-- config.py                  # Pydantic settings (thresholds, URLs)
|   |-- requirements.txt
|   |-- clear_memory.py            # Utility to wipe all database tables
|   |-- agents/
|   |   |-- state.py               # AgentState TypedDict definition
|   |   |-- graph.py               # LangGraph pipeline compilation
|   |   |-- observer.py            # Anomaly detection agent
|   |   |-- reasoner.py            # Pattern correlation agent
|   |   |-- decider.py             # Action planning agent
|   |   |-- executor.py            # Tool-calling execution agent
|   |   |-- learner.py             # Outcome evaluation agent
|   |-- data/
|   |   |-- seed.py                # Sample data generation
|   |   |-- simulator.py           # Disruption injection engine
|   |-- db/
|   |   |-- store.py               # SQLite connection and schema init
|   |-- memory/
|   |   |-- schemas.py             # Dataclasses for events/episodes/patterns
|   |   |-- short_term.py          # In-memory ring buffer
|   |   |-- long_term.py           # SQLite episodic memory
|   |-- pipeline/
|   |   |-- scheduler.py           # 25-second background pipeline loop
|   |   |-- buffer.py              # Thread-safe anomaly collection buffer
|   |-- routes/
|   |   |-- agents.py              # Agent status API
|   |   |-- approvals.py           # Approval workflow API
|   |   |-- carriers.py            # Carrier data API
|   |   |-- dashboard.py           # Metrics and dashboard API
|   |   |-- hubs.py                # Hub/warehouse API
|   |   |-- shipments.py           # Shipment data and locations API
|   |   |-- simulation.py          # Scenario management and disruption API
|   |-- tools/
|       |-- reroute.py             # Shipment rerouting tool
|       |-- notify.py              # Carrier notification tool
|       |-- escalate.py            # Human escalation tool
|       |-- inventory.py           # Inventory reallocation tool
|       |-- simulate.py            # What-if simulation tool
|-- frontend/
|   |-- index.html
|   |-- package.json
|   |-- vite.config.js
|   |-- tailwind.config.js
|   |-- logo.webp
|   |-- src/
|       |-- App.jsx                # Root layout with routing
|       |-- main.jsx               # React DOM entry point
|       |-- index.css              # Tailwind imports and global styles
|       |-- components/
|       |   |-- AgentMesh.jsx      # Live agent pipeline visualization
|       |   |-- ApprovalModal.jsx  # Human approval review modal
|       |   |-- CarrierCards.jsx   # Carrier reliability cards
|       |   |-- EventTicker.jsx   # Scrolling event marquee
|       |   |-- Footer.jsx        # Status bar footer
|       |   |-- Navbar.jsx        # Metrics cards and navigation
|       |   |-- ShipmentMap.jsx   # Leaflet map with hub/shipment markers
|       |   |-- ShipmentTable.jsx # Active shipments data table
|       |   |-- Sidebar.jsx       # Navigation sidebar
|       |   |-- SimulationPanel.jsx
|       |-- context/
|       |   |-- ApprovalContext.jsx # Global approval state provider
|       |-- hooks/
|       |   |-- useAgents.js       # Agent status polling hook
|       |   |-- useShipments.js    # Shipment data polling hook
|       |-- pages/
|       |   |-- Dashboard.jsx      # Command center page
|       |   |-- Simulation.jsx     # Scenario builder and disruption page
|       |-- services/
|           |-- api.js             # Axios API client
```

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **Ollama** installed and running with the `gemma3` model pulled

### 1. Install Ollama and pull the model

```bash
# Install Ollama (macOS)
brew install ollama

# Start the Ollama server
ollama serve

# Pull the gemma3 model (in a separate terminal)
ollama pull gemma3:latest
```

### 2. Set up the backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database and start the server
python clear_memory.py --yes
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at `http://localhost:8000`. The pipeline scheduler starts automatically and runs every 25 seconds.

### 3. Set up the frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

---

## Configuration

All backend configuration is managed through environment variables or the defaults in `config.py`:

| Setting                   | Default                    | Description                                             |
|---------------------------|----------------------------|---------------------------------------------------------|
| `OLLAMA_BASE_URL`         | `http://localhost:11434`   | Ollama server URL                                       |
| `OLLAMA_MODEL`            | `gemma3:latest`            | LLM model for agent reasoning                          |
| `SHORT_TERM_WINDOW`       | `50`                       | Number of events kept in short-term memory              |
| `RISK_ANOMALY_THRESHOLD`  | `75`                       | Minimum risk score for an observation to be actionable  |
| `AUTO_ACT_THRESHOLD`      | `50`                       | Risk score above which autonomous action is considered  |
| `HUMAN_APPROVAL_THRESHOLD`| `90`                       | Risk score at or above which human approval is required |
| `DB_PATH`                 | `db/logistics.sqlite`      | SQLite database file path                               |
| `CORS_ORIGINS`            | `localhost:5173, :3000`    | Allowed CORS origins                                    |

The autonomy thresholds are calibrated so that the system handles most situations independently. Only high-risk, multi-shipment events requiring bulk reroutes will surface an approval request.

---

## Usage

### Command Center (Dashboard)

The dashboard provides a real-time view of the logistics network:

- **Metrics Cards** -- Shipment counts, at-risk and delayed totals, agent operations count, and pending approvals.
- **Agent Mesh** -- Visual representation of the five-agent pipeline showing which agents are active and their most recent outputs.
- **Shipment Table** -- Filterable table of all active shipments with route, carrier, ETA, SLA, risk score, and status.
- **Shipment Map** -- Interactive Leaflet map displaying hub locations and shipment positions with color-coded risk markers.
- **Carrier Cards** -- Reliability trend charts for each carrier in the network.
- **Event Ticker** -- Scrolling marquee of real-time agent events across the top of the screen.
- **Approval Banner** -- When a decision requires human sign-off, a banner appears with a review button that opens the Approval Modal showing current vs. proposed routes and risk metrics.

### Simulation Page

The simulation page is a scenario builder that allows you to construct and stress-test logistics networks:

1. **Build a Network** -- Add warehouses (click-to-place on map), define routes between them, register carriers, and create shipments.
2. **Generate Sample Data** -- One-click generation of a complete logistics scenario with realistic hubs, routes, carriers, and clean shipments.
3. **Inject Disruptions** -- Trigger realistic disruptions and watch the agent pipeline respond autonomously.
4. **Monitor the Pipeline** -- A live status panel shows the pipeline cycle count, buffered anomalies, and time until the next run.

---

## Disruption Simulation

SchnellXAI supports five disruption types that can be injected into any active scenario:

| Disruption Type        | Effect                                                                                          |
|------------------------|-------------------------------------------------------------------------------------------------|
| **Late Pickup**        | Marks a shipment as delayed with increased risk and added ETA minutes                           |
| **Warehouse Congestion** | Sets a hub to congested status; raises risk only on shipments routing through that specific hub |
| **Inaccurate ETA**     | Shifts a shipment's ETA forward or backward, triggering risk recalculation                      |
| **Cascading Reroute**  | Blocks a primary shipment at a hub and cascades secondary impact to nearby shipments             |
| **Carrier Degradation**| Reduces carrier reliability scores and raises risk on affected shipments                         |

The system responds differently based on severity. A hub at 40% congestion with low overall risk will be monitored but not acted upon. A hub at 90% congestion blocking multiple high-risk shipments will trigger autonomous reroutes or surface an approval request for the operator.

---

## API Reference

All endpoints are prefixed with `/api`.

### Simulation

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| GET    | `/api/simulation/scenario`      | Retrieve the current scenario      |
| POST   | `/api/simulation/save-scenario` | Save a scenario configuration      |
| POST   | `/api/simulation/generate-sample` | Generate a complete sample system |
| POST   | `/api/simulation/disruption`    | Inject a disruption event          |
| POST   | `/api/simulation/reset`         | Reset all state                    |
| GET    | `/api/simulation/pipeline-status` | Get pipeline scheduler status    |

### Dashboard and Data

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| GET    | `/api/dashboard/metrics`        | Aggregate metrics for the navbar   |
| GET    | `/api/shipments`                | List all shipments                 |
| GET    | `/api/shipments/locations`      | Shipment coordinates for the map   |
| GET    | `/api/carriers`                 | List all carriers with stats       |
| GET    | `/api/hubs`                     | List all hubs/warehouses           |

### Agents

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| GET    | `/api/agents/status`            | Status of all five agents          |
| GET    | `/api/agent/events`             | Recent event stream                |

### Approvals

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| GET    | `/api/approvals/pending`        | Get pending approval requests      |
| POST   | `/api/approvals/{id}/approve`   | Approve a pending action           |
| POST   | `/api/approvals/{id}/reject`    | Reject a pending action            |

### Health

| Method | Endpoint     | Description          |
|--------|-------------|----------------------|
| GET    | `/health`    | Server health check  |

---

## License

This project is proprietary. All rights reserved.
