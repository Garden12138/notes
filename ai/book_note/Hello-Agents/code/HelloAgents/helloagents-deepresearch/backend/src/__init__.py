"""Backend package for the automated deep research assistant."""

from .agent import DeepResearchAgent
from .architecture import build_architecture_snapshot

__all__ = ["DeepResearchAgent", "build_architecture_snapshot"]

