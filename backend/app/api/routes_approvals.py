from fastapi import APIRouter

from ..agents.executor import run_executor
from ..agents.learner import run_learner
from ..models.domain import Approval, ApprovalDecisionRequest
from ..state import get_state


router = APIRouter(tags=["approvals"])


@router.get("/approvals/pending", response_model=Approval | None)
async def get_pending_approval():
    """
    Return the next pending approval proposal, if any.
    """
    state = get_state()
    return state.pop_next_approval()


@router.post("/approvals/execute")
async def execute_approval(decision: ApprovalDecisionRequest):
    """
    Execute an approved action, updating shipments and metrics.
    """
    state = get_state()
    approval = state.remove_approval(decision.id)
    if approval and approval.shipmentId:
        # Construct a minimal AgentAction on the fly for the executor.
        from ..models.domain import ActionType, AgentAction

        action = AgentAction(
            id=f"ACT-{approval.shipmentId}",
            type=ActionType.REROUTE_SHIPMENT,
            shipmentId=approval.shipmentId,
            description=approval.action,
            blastRadius=approval.blastRadius,
            costDelta=float(approval.costDelta.replace("+₹", "").replace("₹", "").replace(",", "")),
            slaImpactMinutes=120,
            requiresApproval=False,
            recommended=True,
            rationale=approval.reason,
        )
        await run_executor(state, action)
        await run_learner(state)

    return {"success": True}


@router.post("/approvals/reject")
async def reject_approval(decision: ApprovalDecisionRequest):
    """
    Reject an approval proposal and let the learner treat it as a negative outcome.
    """
    state = get_state()
    state.remove_approval(decision.id)
    # No direct state mutation; learner will interpret absence of execution
    # as implicit feedback when evaluating alternatives.
    return {"success": True}

