import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Backend configuration loaded from environment variables."""

    api_prefix: str = "/api"
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "gemma:2b")

    # Simulation and risk configuration
    simulation_tick_seconds: float = float(os.getenv("SIMULATION_TICK_SECONDS", "5"))
    max_events: int = int(os.getenv("MAX_AGENT_EVENTS", "200"))

    # Guardrail thresholds
    auto_execute_max_blast_radius: int = int(
        os.getenv("AUTO_EXECUTE_MAX_BLAST_RADIUS", "3")
    )
    auto_execute_max_cost_delta: float = float(
        os.getenv("AUTO_EXECUTE_MAX_COST_DELTA", "2500")
    )  # in arbitrary currency units


settings = Settings()

