"""
Aegis Configuration and Settings.
Uses standard pydantic/os.environ for zero-dependency environment loading.
"""

import os
from typing import Literal
from pydantic import BaseModel, Field


class AegisSettings(BaseModel):
    # LLM Settings
    llm_provider: str = Field(default_factory=lambda: os.getenv("AEGIS_LLM_PROVIDER", "mock"))
    llm_model: str = Field(default_factory=lambda: os.getenv("AEGIS_LLM_MODEL", "llama-3.3-70b-versatile"))
    groq_api_key: str | None = Field(default_factory=lambda: os.getenv("GROQ_API_KEY"))
    openai_api_key: str | None = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: str | None = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    ollama_base_url: str = Field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

    # Execution Sandbox Settings
    sandbox_mode: str = Field(default_factory=lambda: os.getenv("AEGIS_SANDBOX_MODE", "local"))
    docker_image: str = Field(default_factory=lambda: os.getenv("DOCKER_SANDBOX_IMAGE", "python:3.11-slim"))
    sandbox_timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "60")))
    sandbox_max_memory_mb: int = Field(default_factory=lambda: int(os.getenv("SANDBOX_MAX_MEMORY_MB", "1024")))

    # MCTS Search Parameters
    mcts_max_iterations: int = Field(default_factory=lambda: int(os.getenv("MCTS_MAX_ITERATIONS", "12")))
    mcts_exploration_constant: float = Field(default_factory=lambda: float(os.getenv("MCTS_EXPLORATION_CONSTANT", "1.414")))
    mcts_max_depth: int = Field(default_factory=lambda: int(os.getenv("MCTS_MAX_DEPTH", "6")))

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000


settings = AegisSettings()