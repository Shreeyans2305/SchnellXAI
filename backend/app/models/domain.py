from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class MetricValue(BaseModel):
    value: int
    change: str


class DashboardMetrics(BaseModel):
    shipments: MetricValue
    atRisk: MetricValue
    delayed: MetricValue
    agentOps: MetricValue
    approvals: MetricValue
    ollamaStatus: str
    agentsActive: int
    agentsTotal: int


class EventType(str, Enum):
    ANOMALY = "ANOMALY"
    REROUTE = "REROUTE"
    ALERT = "ALERT"
    LEARNING = "LEARNING"
    APPROVAL = "APPROVAL"
    EXECUTE = "EXECUTE"
    OPTIMIZE = "OPTIMIZE"


class AgentEvent(BaseModel):
    id: int
    time: str
    type: EventType
    flow: str
    message: str


class Agent(BaseModel):
    id: str
    name: str
    status: str
    load: int = Field(ge=0, le=100)
    messagesProcessed: int
    lastAction: str
    color: str


class AgentEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    active: bool

    model_config = ConfigDict(populate_by_name=True)


class ShipmentStatus(str, Enum):
    ON_TRACK = "ON TRACK"
    AT_RISK = "AT RISK"
    DELAYED = "DELAYED"


class Shipment(BaseModel):
    id: str
    route: str
    carrier: str
    progress: int = Field(ge=0, le=100)
    eta: str
    sla: str
    risk: int = Field(ge=0, le=100)
    agent: str
    status: ShipmentStatus
    notes: str


class Carrier(BaseModel):
    id: int
    name: str
    reliability: int = Field(ge=0, le=100)
    active: int
    delayed: int
    trend: List[int]
    logo: str


class LatLng(BaseModel):
    lat: float
    lng: float


class Hub(LatLng):
    id: int
    name: str
    shipments: int
    status: str


class ShipmentLocation(LatLng):
    id: str
    from_: LatLng = Field(alias="from")
    to: LatLng
    status: ShipmentStatus

    model_config = ConfigDict(populate_by_name=True)


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CascadeImpact(BaseModel):
    shipment: str
    impact: str
    severity: Severity


class SimulationOption(BaseModel):
    id: int
    name: str
    netScore: int = Field(ge=0, le=100)
    blastRadius: int
    slaImpact: str
    cost: str
    recommended: bool


class SimulationResult(BaseModel):
    options: List[SimulationOption]
    cascadeImpact: List[CascadeImpact]
    reasoning: str


class Approval(BaseModel):
    id: str
    shipmentId: str
    action: str
    currentRoute: List[str]
    proposedRoute: List[str]
    blastRadius: int
    netScore: int = Field(ge=0, le=100)
    costDelta: str
    slaImpact: str
    reason: str


class ActionType(str, Enum):
    REROUTE_SHIPMENT = "REROUTE_SHIPMENT"
    REASSIGN_CARRIER = "REASSIGN_CARRIER"
    DELAY_CONSOLIDATION = "DELAY_CONSOLIDATION"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"


class AgentAction(BaseModel):
    id: str
    type: ActionType
    shipmentId: Optional[str] = None
    description: str
    blastRadius: int
    costDelta: float
    slaImpactMinutes: int
    requiresApproval: bool
    recommended: bool = True
    rationale: str


class SimulationRequest(BaseModel):
    shipmentId: str
    hub: str


class WarehouseConfig(LatLng):
    id: int
    name: str
    status: str = "active"


class RouteConfig(BaseModel):
    id: str
    fromWarehouseId: int
    toWarehouseId: int
    distanceKm: float = Field(gt=0)
    typicalEtaMinutes: int = Field(gt=0)


class CarrierConfig(BaseModel):
    id: int
    name: str
    reliability: int = Field(ge=0, le=100)
    capacity: int = Field(ge=1)


class ShipmentConfig(BaseModel):
    id: str
    routeId: str
    carrierId: int
    progress: int = Field(ge=0, le=100)
    risk: int = Field(ge=0, le=100)
    status: ShipmentStatus
    slaMinutes: int = Field(gt=0)
    etaMinutes: int = Field(gt=0)
    notes: str = ""


class LogisticsScenario(BaseModel):
    warehouses: List[WarehouseConfig]
    routes: List[RouteConfig]
    carriers: List[CarrierConfig]
    shipments: List[ShipmentConfig]


class DisruptionType(str, Enum):
    LATE_PICKUP = "late_pickup"
    WAREHOUSE_CONGESTION = "warehouse_congestion"
    INACCURATE_ETA = "inaccurate_eta"
    CASCADING_REROUTE = "cascading_reroute"


class DisruptionRequest(BaseModel):
    type: DisruptionType
    targetShipmentId: Optional[str] = None
    targetWarehouseId: Optional[int] = None
    severity: int = Field(default=60, ge=1, le=100)


class PipelineSummary(BaseModel):
    observer: dict
    reasoner: dict
    decider: dict
    queuedApprovals: int


class DisruptionResponse(BaseModel):
    message: str
    pipeline: PipelineSummary


class ApprovalDecisionRequest(BaseModel):
    id: str

