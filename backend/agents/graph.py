from langgraph.graph import END, StateGraph

from agents.decider import decider_node
from agents.executor import executor_node
from agents.learner import learner_node
from agents.observer import observer_node
from agents.reasoner import reasoner_node
from agents.state import AgentState


def has_anomalies(state: AgentState) -> str:
    return "reasoner" if state.get("observations") else "learner"


def needs_execution(state: AgentState) -> str:
    autonomous = [a for a in state.get("actions", []) if a.get("autonomous")]
    return "executor" if autonomous else "learner"


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("observer", observer_node)
    g.add_node("reasoner", reasoner_node)
    g.add_node("decider", decider_node)
    g.add_node("executor", executor_node)
    g.add_node("learner", learner_node)

    g.set_entry_point("observer")
    g.add_conditional_edges("observer", has_anomalies)
    g.add_edge("reasoner", "decider")
    g.add_conditional_edges("decider", needs_execution)
    g.add_edge("executor", "learner")
    g.add_edge("learner", END)

    return g.compile()


logistics_graph = build_graph()
