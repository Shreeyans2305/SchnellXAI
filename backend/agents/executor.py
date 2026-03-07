import json
from datetime import datetime

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

from agents.state import AgentState
from config import settings
from memory.schemas import ShortTermEvent
from memory.short_term import short_term_memory
from tools.escalate import escalate_to_human
from tools.inventory import reallocate_inventory
from tools.notify import notify_carrier
from tools.reroute import reroute_shipment
from tools.simulate import run_what_if_simulation

llm = ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)
tools = [
    reroute_shipment,
    escalate_to_human,
    notify_carrier,
    reallocate_inventory,
    run_what_if_simulation,
]

SYSTEM_PROMPT = """You are the Executor agent. You have tools to act on logistics decisions.
For each autonomous action given, call the appropriate tool."""

executor_agent = create_react_agent(llm, tools)


def _fallback_execute(autonomous_actions: list[dict]) -> list[dict]:
    executed = []
    for action in autonomous_actions:
        tool_name = action.get("type")
        params = action.get("params", {})
        try:
            if tool_name == "reroute_shipment":
                outcome = reroute_shipment.invoke(params)
            elif tool_name == "notify_carrier":
                outcome = notify_carrier.invoke(params)
            elif tool_name == "reallocate_inventory":
                outcome = reallocate_inventory.invoke(params)
            elif tool_name == "escalate_to_human":
                outcome = escalate_to_human.invoke(params)
            else:
                outcome = {"success": False, "reason": f"Unsupported tool: {tool_name}"}
        except Exception as exc:
            outcome = {"success": False, "error": str(exc)}

        executed.append(
            {
                "action_id": action.get("id", "?"),
                "tool": tool_name,
                "outcome": outcome,
            }
        )
    return executed


def executor_node(state: AgentState) -> AgentState:
    autonomous_actions = [a for a in state.get("actions", []) if a.get("autonomous")]
    if not autonomous_actions:
        return {
            **state,
            "executed_actions": [],
            "executor_summary": "No autonomous actions to execute.",
        }

    user_msg = f"""
Execute these autonomous actions using your tools:
{json.dumps(autonomous_actions, indent=2)}

Shipment context:
{json.dumps(state['shipments'], indent=2)}
"""

    executed = []
    try:
        result = executor_agent.invoke(
            {
                "messages": [
                    ("system", SYSTEM_PROMPT),
                    ("human", user_msg),
                ]
            }
        )

        for msg in result.get("messages", []):
            msg_type = getattr(msg, "type", "")
            if msg_type == "tool":
                content = getattr(msg, "content", "")
                try:
                    outcome = json.loads(content) if isinstance(content, str) else content
                except Exception:
                    outcome = {"raw": content}
                executed.append(
                    {
                        "action_id": getattr(msg, "tool_call_id", "?"),
                        "tool": getattr(msg, "name", "tool_call"),
                        "outcome": outcome,
                    }
                )

        if not executed:
            executed = _fallback_execute(autonomous_actions)
    except Exception:
        executed = _fallback_execute(autonomous_actions)

    cycle_id = state.get("cycle_id", "?")
    short_term_memory.push(
        ShortTermEvent(
            cycle_id=cycle_id,
            timestamp=datetime.utcnow().isoformat(),
            event_type="EXECUTE",
            flow="executor → system",
            message=f"Executed {len(executed)} actions.",
        )
    )

    return {
        **state,
        "executed_actions": executed,
        "executor_summary": f"Executed {len(executed)} actions.",
    }
